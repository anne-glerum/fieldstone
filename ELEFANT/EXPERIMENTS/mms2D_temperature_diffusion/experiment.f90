!==================================================================================================!
!==================================================================================================!
!                                                                                                  !
! ELEFANT                                                                        C. Thieulot       !
!                                                                                                  !
!==================================================================================================!
!==================================================================================================!

subroutine declare_main_parameters

use module_parameters

implicit none

!----------------------------------------------------------

Lx=1
Ly=1

nelx=32
nely=32

use_T=.true.

solve_stokes_system=.false.



!----------------------------------------------------------

end subroutine

!==================================================================================================!

subroutine define_material_properties

implicit none

!----------------------------------------------------------


!----------------------------------------------------------

end subroutine

!==================================================================================================!

subroutine material_model(x,y,z,p,T,exx,eyy,ezz,exy,exz,eyz,imat,mode,&
                          eta,rho,hcond,hcapa,hprod)

implicit none

real(8), intent(in) :: x,y,z,p,T,exx,eyy,ezz,exy,exz,eyz
integer, intent(in) :: imat,mode
real(8), intent(out) :: eta,rho,hcond,hcapa,hprod

!----------------------------------------------------------

eta=0
rho=1
hcond=1
hcapa=1
hprod=0

!----------------------------------------------------------

end subroutine

!==================================================================================================!

subroutine swarm_material_layout 

implicit none

!----------------------------------------------------------


!----------------------------------------------------------

end subroutine

!==================================================================================================!

subroutine define_bcV

implicit none

!----------------------------------------------------------


!----------------------------------------------------------

end subroutine

!==================================================================================================!

subroutine define_bcT

use module_parameters
use module_mesh 

implicit none

integer i

!----------------------------------------------------------

do iel=1,nel
   mesh(iel)%fix_T(:)=.false. 
   !bottom boundary
   do i=1,mT
      if (mesh(iel)%bnd3_node(i)) then
         mesh(iel)%fix_T(i)=.true. ; mesh(iel)%T(i)=1.d0
      end if
   end do
   !top boundary
   do i=1,mT
      if (mesh(iel)%bnd4_node(i)) then
         mesh(iel)%fix_T(i)=.true. ; mesh(iel)%T(i)=0.d0
      end if
   end do
end do

!----------------------------------------------------------

end subroutine

!==================================================================================================!

subroutine initial_temperature

use module_parameters
use module_mesh 

implicit none

!----------------------------------------------------------

do iel=1,nel
   mesh(iel)%T=0.5
end do

!----------------------------------------------------------

end subroutine

!==================================================================================================!

subroutine analytical_solution(x,y,z,u,v,w,p,T,exx,eyy,ezz,exy,exz,eyz)

implicit none

real(8), intent(in) :: x,y,z
real(8), intent(out) :: u,v,w,p,T,exx,eyy,ezz,exy,exz,eyz

!----------------------------------------------------------

! your stuff here

u=0
v=0
w=0
p=0
T=1-y
exx=0
eyy=0
ezz=0
exy=0
exz=0
eyz=0

!----------------------------------------------------------

end subroutine

!==================================================================================================!

subroutine gravity_model(x,y,z,gx,gy,gz)

implicit none

real(8), intent(in) :: x,y,z
real(8), intent(out) :: gx,gy,gz

!----------------------------------------------------------

gx=0
gy=0
gz=0

!----------------------------------------------------------

end subroutine

!==================================================================================================!

subroutine test

implicit none

!----------------------------------------------------------

! your stuff here

!----------------------------------------------------------

end subroutine

!==================================================================================================!

subroutine postprocessor_experiment

implicit none

!----------------------------------------------------------

! your stuff here

!----------------------------------------------------------

end subroutine

!==================================================================================================!
