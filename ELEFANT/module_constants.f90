module constants
implicit none
integer, parameter :: one=1
integer, parameter :: two=2
integer, parameter :: three=3
integer, parameter :: four=4
real(8), parameter :: mm=1.d-3
real(8), parameter :: cm=1.d-2
real(8), parameter :: km=1.d+3
real(8), parameter :: hour=3600.d0    !seconds
real(8), parameter :: day=86400.d0    !seconds
real(8), parameter :: year=31557600d0 !seconds 
real(8), parameter :: Myr=3.15576d13  !seconds
real(8), parameter :: TKelvin=273.15d0 
real(8), parameter :: eps=1.d-8
real(8), parameter :: epsilon_test=1.d-6
real(8), parameter :: sqrt3 = 1.732050807568877293527446341505d0
real(8), dimension(2), parameter :: qcoords=(/-1.d0/sqrt3,+1.d0/sqrt3/)
real(8), dimension(2), parameter :: qweights=(/1.d0 , 1.d0 /)
end module constants