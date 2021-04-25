!==================================================================================================!
!==================================================================================================!
!                                                                                                  !
! ELEFANT                                                                        C. Thieulot       !
!                                                                                                  !
!==================================================================================================!
!==================================================================================================!

subroutine assign_values_to_qpoints

use global_parameters
use global_measurements
use structures
use constants
use timing

implicit none

integer i,im,iq,idummy,ipvt2D(3),ipvt3D(4),job
real(8) x(1000),y(1000),z(1000),rho(1000),eta(1000),rcond
real(8) A2D(3,3),B2D(3),work2D(3),A3D(4,4),B3D(4),work3D(4),NNNT(mT),NNNP(mP)
real(8) pm,Tm,exxm,eyym,ezzm,exym,exzm,eyzm
real(8) exxq,eyyq,ezzq,exyq,exzq,eyzq

!==================================================================================================!
!==================================================================================================!
!@@ \subsubsection{assign\_values\_to\_qpoints.f90}
!@@
!==================================================================================================!

if (iproc==0) then

call system_clock(counti,count_rate)

!==============================================================================!

etaq_max=-1d50
etaq_min=+1d50
rhoq_max=-1d50
rhoq_min=+1d50

if (use_swarm) then 

   do iel=1,nel
  
      do i=1,mesh(iel)%nmarker

         im=mesh(iel)%list_of_markers(i)

         call NNP(swarm(im)%r,swarm(im)%s,swarm(im)%t,NNNP(1:mP),mP,ndim,pair)
         pm=sum(NNNP(1:mP)*mesh(iel)%p(1:mP))

         !or use q ?

         call NNT(swarm(im)%r,swarm(im)%s,swarm(im)%t,NNNT(1:mT),mT,ndim)
         Tm=sum(NNNT(1:mT)*mesh(iel)%T(1:mT))
         exxm=sum(NNNT(1:mT)*mesh(iel)%exx(1:mT))
         eyym=sum(NNNT(1:mT)*mesh(iel)%eyy(1:mT))
         ezzm=sum(NNNT(1:mT)*mesh(iel)%ezz(1:mT))
         exym=sum(NNNT(1:mT)*mesh(iel)%exy(1:mT))
         exzm=sum(NNNT(1:mT)*mesh(iel)%exz(1:mT))
         eyzm=sum(NNNT(1:mT)*mesh(iel)%eyz(1:mT))

         call material_model(swarm(im)%x,&
                             swarm(im)%y,&
                             swarm(im)%z,&
                             pm,&
                             Tm,&
                             exxm,eyym,ezzm,exym,exzm,eyzm,&
                             swarm(im)%mat,one,&
                             swarm(im)%eta,&
                             swarm(im)%rho,&
                             swarm(im)%hcond,&
                             swarm(im)%hcapa,&
                             swarm(im)%hprod)

         x(i)=swarm(im)%x-mesh(iel)%xc
         y(i)=swarm(im)%y-mesh(iel)%yc
         z(i)=swarm(im)%z-mesh(iel)%zc
         rho(i)=swarm(im)%rho
         eta(i)=swarm(im)%eta

      end do 

      if (ndim==2) then 

        A2D(1,1)=mesh(iel)%nmarker
        A2D(1,2)=sum(x(1:mesh(iel)%nmarker)) 
        A2D(1,3)=sum(y(1:mesh(iel)%nmarker)) 
        A2D(2,1)=sum(x(1:mesh(iel)%nmarker)) 
        A2D(2,2)=sum(x(1:mesh(iel)%nmarker)*x(1:mesh(iel)%nmarker)) 
        A2D(2,3)=sum(x(1:mesh(iel)%nmarker)*y(1:mesh(iel)%nmarker)) 
        A2D(3,1)=sum(y(1:mesh(iel)%nmarker)) 
        A2D(3,2)=sum(y(1:mesh(iel)%nmarker)*x(1:mesh(iel)%nmarker)) 
        A2D(3,3)=sum(y(1:mesh(iel)%nmarker)*y(1:mesh(iel)%nmarker))
        call DGECO (A2D, three, three, ipvt2D, rcond, work2D)

        ! build rhs for density and solve
        B2D(1)=sum(rho(1:mesh(iel)%nmarker))
        B2D(2)=sum(x(1:mesh(iel)%nmarker)*rho(1:mesh(iel)%nmarker))
        B2D(3)=sum(y(1:mesh(iel)%nmarker)*rho(1:mesh(iel)%nmarker))

        job=0
        call DGESL (A2D, three, three, ipvt2D, B2D, job)
        mesh(iel)%a_rho=B2D(1)
        mesh(iel)%b_rho=B2D(2)
        mesh(iel)%c_rho=B2D(3)
        mesh(iel)%d_rho=0d0

        ! build rhs for viscosity and solve
        B2D(1)=sum(eta(1:mesh(iel)%nmarker))
        B2D(2)=sum(x(1:mesh(iel)%nmarker)*eta(1:mesh(iel)%nmarker))
        B2D(3)=sum(y(1:mesh(iel)%nmarker)*eta(1:mesh(iel)%nmarker))
        job=0
        call DGESL (A2D, three, three, ipvt2D, B2D, job)
        mesh(iel)%a_eta=B2D(1)
        mesh(iel)%b_eta=B2D(2)
        mesh(iel)%c_eta=B2D(3)
        mesh(iel)%d_eta=0d0

        ! filter for over/undershoot

        mesh(iel)%b_rho=0 
        mesh(iel)%c_rho=0 

        mesh(iel)%b_eta=0 
        mesh(iel)%c_eta=0 

      end if ! ndim=2

      if (ndim==3) then 

        A3D(1,1)=mesh(iel)%nmarker
        A3D(1,2)=sum(x(1:mesh(iel)%nmarker)) 
        A3D(1,3)=sum(y(1:mesh(iel)%nmarker)) 
        A3D(1,4)=sum(z(1:mesh(iel)%nmarker)) 
        A3D(2,1)=sum(x(1:mesh(iel)%nmarker)) 
        A3D(2,2)=sum(x(1:mesh(iel)%nmarker)*x(1:mesh(iel)%nmarker)) 
        A3D(2,3)=sum(x(1:mesh(iel)%nmarker)*y(1:mesh(iel)%nmarker)) 
        A3D(2,4)=sum(x(1:mesh(iel)%nmarker)*z(1:mesh(iel)%nmarker)) 
        A3D(3,1)=sum(y(1:mesh(iel)%nmarker)) 
        A3D(3,2)=sum(y(1:mesh(iel)%nmarker)*x(1:mesh(iel)%nmarker)) 
        A3D(3,3)=sum(y(1:mesh(iel)%nmarker)*y(1:mesh(iel)%nmarker))
        A3D(3,4)=sum(y(1:mesh(iel)%nmarker)*z(1:mesh(iel)%nmarker))
        A3D(4,1)=sum(z(1:mesh(iel)%nmarker)) 
        A3D(4,2)=sum(z(1:mesh(iel)%nmarker)*x(1:mesh(iel)%nmarker)) 
        A3D(4,3)=sum(z(1:mesh(iel)%nmarker)*y(1:mesh(iel)%nmarker))
        A3D(4,4)=sum(z(1:mesh(iel)%nmarker)*z(1:mesh(iel)%nmarker))
        call DGECO (A3D, four, four, ipvt3D, rcond, work3D)

        ! build rhs for density and solve
        B3D(1)=sum(rho(1:mesh(iel)%nmarker))
        B3D(2)=sum(x(1:mesh(iel)%nmarker)*rho(1:mesh(iel)%nmarker))
        B3D(3)=sum(y(1:mesh(iel)%nmarker)*rho(1:mesh(iel)%nmarker))
        B3D(4)=sum(z(1:mesh(iel)%nmarker)*rho(1:mesh(iel)%nmarker))

        job=0
        call DGESL (A3D, four, four, ipvt3D, B3D, job)
        mesh(iel)%a_rho=B3D(1)
        mesh(iel)%b_rho=B3D(2)
        mesh(iel)%c_rho=B3D(3)
        mesh(iel)%d_rho=B3D(4)

        ! build rhs for viscosity and solve
        B3D(1)=sum(eta(1:mesh(iel)%nmarker))
        B3D(2)=sum(x(1:mesh(iel)%nmarker)*eta(1:mesh(iel)%nmarker))
        B3D(3)=sum(y(1:mesh(iel)%nmarker)*eta(1:mesh(iel)%nmarker))
        B3D(3)=sum(z(1:mesh(iel)%nmarker)*eta(1:mesh(iel)%nmarker))
        job=0
        call DGESL (A3D, four, four, ipvt3D, B3D, job)
        mesh(iel)%a_eta=B3D(1)
        mesh(iel)%b_eta=B3D(2)
        mesh(iel)%c_eta=B3D(3)
        mesh(iel)%d_eta=B3D(4)

        ! filter for over/undershoot

        mesh(iel)%b_rho=0 
        mesh(iel)%c_rho=0 
        mesh(iel)%d_rho=0 

        mesh(iel)%b_eta=0 
        mesh(iel)%c_eta=0 
        mesh(iel)%d_eta=0 

      end if ! ndim=3

      ! project values on quadrature points

      do iq=1,nqel
         mesh(iel)%etaq(iq)=mesh(iel)%a_eta+&
                            mesh(iel)%b_eta*(mesh(iel)%xq(iq)-mesh(iel)%xc)+&
                            mesh(iel)%c_eta*(mesh(iel)%yq(iq)-mesh(iel)%yc)+&
                            mesh(iel)%d_eta*(mesh(iel)%zq(iq)-mesh(iel)%zc)
         mesh(iel)%rhoq(iq)=mesh(iel)%a_rho+&
                            mesh(iel)%b_rho*(mesh(iel)%xq(iq)-mesh(iel)%xc)+&
                            mesh(iel)%c_rho*(mesh(iel)%yq(iq)-mesh(iel)%yc)+&
                            mesh(iel)%d_rho*(mesh(iel)%zq(iq)-mesh(iel)%zc)
      end do

      etaq_min=min(minval(mesh(iel)%etaq(:)),etaq_min)
      etaq_max=max(maxval(mesh(iel)%etaq(:)),etaq_max)
      rhoq_min=min(minval(mesh(iel)%rhoq(:)),rhoq_min)
      rhoq_max=max(maxval(mesh(iel)%rhoq(:)),rhoq_max)

   end do ! iel

else

   do iel=1,nel
      do iq=1,nqel

         !compute pq

         call NNP(mesh(iel)%rq(iq),mesh(iel)%sq(iq),mesh(iel)%tq(iq),NNNP(1:mP),mP,ndim,pair)
         mesh(iel)%pq(iq)=sum(NNNP(1:mP)*mesh(iel)%p(1:mP))

         !compute strainrate and Tq

         call NNT(mesh(iel)%rq(iq),mesh(iel)%sq(iq),mesh(iel)%tq(iq),NNNT(1:mT),mT,ndim)
         mesh(iel)%thetaq(iq)=sum(NNNT(1:mT)*mesh(iel)%T(1:mT))
         exxq=sum(NNNT(1:mT)*mesh(iel)%exx(1:mT))
         eyyq=sum(NNNT(1:mT)*mesh(iel)%eyy(1:mT))
         ezzq=sum(NNNT(1:mT)*mesh(iel)%ezz(1:mT))
         exyq=sum(NNNT(1:mT)*mesh(iel)%exy(1:mT))
         exzq=sum(NNNT(1:mT)*mesh(iel)%exz(1:mT))
         eyzq=sum(NNNT(1:mT)*mesh(iel)%eyz(1:mT))

         call material_model(mesh(iel)%xq(iq),&
                             mesh(iel)%yq(iq),&
                             mesh(iel)%zq(iq),&
                             mesh(iel)%pq(iq),&
                             mesh(iel)%Tq(iq),&
                             exxq,eyyq,ezzq,exyq,exzq,eyzq,&
                             idummy,one,&
                             mesh(iel)%etaq(iq),&
                             mesh(iel)%rhoq(iq),&
                             mesh(iel)%hcondq(iq),&
                             mesh(iel)%hcapaq(iq),&
                             mesh(iel)%hprodq(iq))

   
      end do

      etaq_min=min(minval(mesh(iel)%etaq(:)),etaq_min)
      etaq_max=max(maxval(mesh(iel)%etaq(:)),etaq_max)
      rhoq_min=min(minval(mesh(iel)%rhoq(:)),rhoq_min)
      rhoq_max=max(maxval(mesh(iel)%rhoq(:)),rhoq_max)

   end do

end if

write(*,'(a,2es10.3)') '        rhoq (m/M):',rhoq_min,rhoq_max
write(*,'(a,2es10.3)') '        etaq (m/M):',etaq_min,etaq_max

!==============================================================================!

call system_clock(countf) ; elapsed=dble(countf-counti)/dble(count_rate)

write(*,'(a,f4.2,a)') '     >> assign_values_to_qpoints         ',elapsed,' s'

end if ! iproc

end subroutine

!==================================================================================================!
!==================================================================================================!
