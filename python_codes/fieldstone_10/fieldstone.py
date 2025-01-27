import numpy as np
import math as math
import sys as sys
import scipy
import scipy.sparse as sps
from scipy.sparse.linalg.dsolve import linsolve
import time as time
import matplotlib.pyplot as plt
from scipy.sparse import csr_matrix, lil_matrix

#------------------------------------------------------------------------------

def rho(x,y,z):
    if (x-.5)**2+(y-0.5)**2+(z-0.5)**2<0.123**2:
       val=2.
    else:
       val=1.
    return val

def mu(x,y,z):
    if (x-.5)**2+(y-0.5)**2+(z-0.5)**2<0.123**2:
       val=1.e2
    else:
       val=1.
    return val

#------------------------------------------------------------------------------

print("-----------------------------")
print("----------SimpleFEM----------")
print("-----------------------------")

m=8     # number of nodes making up an element
ndof=3  # number of degrees of freedom per node

Lx=1.  # x- extent of the domain 
Ly=1.  # y- extent of the domain 
Lz=1.  # z- extent of the domain 

assert (Lx>0.), "Lx should be positive" 
assert (Ly>0.), "Ly should be positive" 
assert (Lz>0.), "Lz should be positive" 

# allowing for argument parsing through command line
if int(len(sys.argv) == 4):
   nelx = int(sys.argv[1])
   nely = int(sys.argv[2])
   nelz = int(sys.argv[3])
else:
   nelx = 16
   nely = 16
   nelz = 16

assert (nelx>0.), "nelx should be positive" 
assert (nely>0.), "nely should be positive" 
assert (nelz>0.), "nelz should be positive" 

visu=1
    
nnx=nelx+1  # number of elements, x direction
nny=nely+1  # number of elements, y direction
nnz=nelz+1  # number of elements, z direction

nnp=nnx*nny*nnz  # number of nodes

nel=nelx*nely*nelz  # number of elements, total

penalty=1.e7  # penalty coefficient value

Nfem=nnp*ndof  # Total number of degrees of freedom

eps=1.e-10

gx=0.   # gravity vector, x component
gy=0.   # gravity vector, y component
gz=-1.  # gravity vector, z component

sqrt3=np.sqrt(3.)

#################################################################
# grid point setup
#################################################################

print("grid point setup")

x = np.empty(nnp, dtype=np.float64)  # x coordinates
y = np.empty(nnp, dtype=np.float64)  # y coordinates
z = np.empty(nnp, dtype=np.float64)  # z coordinates

counter=0
for i in range(0, nnx):
    for j in range(0, nny):
        for k in range(0, nnz):
            x[counter]=i*Lx/float(nelx)
            y[counter]=j*Ly/float(nely)
            z[counter]=k*Lz/float(nelz)
            counter += 1

#################################################################
# connectivity
#################################################################

print("connectivity")

icon =np.zeros((m, nel),dtype=np.int16)
counter = 0
for i in range(0, nelx):
    for j in range(0, nely):
        for k in range(0, nelz):
            icon[0,counter]=nny*nnz*(i-1+1)+nnz*(j-1+1)+k
            icon[1,counter]=nny*nnz*(i  +1)+nnz*(j-1+1)+k
            icon[2,counter]=nny*nnz*(i  +1)+nnz*(j  +1)+k
            icon[3,counter]=nny*nnz*(i-1+1)+nnz*(j  +1)+k
            icon[4,counter]=nny*nnz*(i-1+1)+nnz*(j-1+1)+k+1
            icon[5,counter]=nny*nnz*(i  +1)+nnz*(j-1+1)+k+1
            icon[6,counter]=nny*nnz*(i  +1)+nnz*(j  +1)+k+1
            icon[7,counter]=nny*nnz*(i-1+1)+nnz*(j  +1)+k+1
            counter += 1

#################################################################
# define boundary conditions
#################################################################
start = time.time()

bc_fix=np.zeros(Nfem,dtype=np.bool)  # boundary condition, yes/no
bc_val=np.zeros(Nfem,dtype=float)  # boundary condition, value

for i in range(0,nnp):
    if x[i]<eps:
       bc_fix[i*ndof+0]=True ; bc_val[i*ndof+0]= 0.
    if x[i]>(Lx-eps):
       bc_fix[i*ndof+0]=True ; bc_val[i*ndof+0]= 0.
    if y[i]<eps:
       bc_fix[i*ndof+1]=True ; bc_val[i*ndof+1]= 0.
    if y[i]>(Ly-eps):
       bc_fix[i*ndof+1]=True ; bc_val[i*ndof+1]= 0.
    if z[i]<eps:
       bc_fix[i*ndof+2]=True ; bc_val[i*ndof+2]= 0.
    if z[i]>(Lz-eps):
       bc_fix[i*ndof+2]=True ; bc_val[i*ndof+2]= 0.

print("define b.c.: %.3f s" % (time.time() - start))

#################################################################
# build FE matrix
#################################################################
start = time.time()

a_mat = lil_matrix((Nfem,Nfem),dtype=np.float64) # matrix of Ax=b
b_mat = np.zeros((6,ndof*m),dtype=np.float64)    # gradient matrix B 
rhs   = np.zeros(Nfem,dtype=np.float64)          # right hand side of Ax=b
N     = np.zeros(m,dtype=np.float64)             # shape functions
dNdx  = np.zeros(m,dtype=np.float64)             # shape functions derivatives
dNdy  = np.zeros(m,dtype=np.float64)             # shape functions derivatives
dNdz  = np.zeros(m,dtype=np.float64)             # shape functions derivatives
dNdr  = np.zeros(m,dtype=np.float64)             # shape functions derivatives
dNds  = np.zeros(m,dtype=np.float64)             # shape functions derivatives
dNdt  = np.zeros(m,dtype=np.float64)             # shape functions derivatives
u     = np.zeros(nnp,dtype=np.float64)           # x-component velocity
v     = np.zeros(nnp,dtype=np.float64)           # y-component velocity
w     = np.zeros(nnp,dtype=np.float64)           # z-component velocity
k_mat = np.zeros((6,6),dtype=np.float64) 
c_mat = np.zeros((6,6),dtype=np.float64) 

k_mat[0,0]=1. ; k_mat[0,1]=1. ; k_mat[0,2]=1.  
k_mat[1,0]=1. ; k_mat[1,1]=1. ; k_mat[1,2]=1.  
k_mat[2,0]=1. ; k_mat[2,1]=1. ; k_mat[2,2]=1.  

c_mat[0,0]=2. ; c_mat[1,1]=2. ; c_mat[2,2]=2.
c_mat[3,3]=1. ; c_mat[4,4]=1. ; c_mat[5,5]=1.

for iel in range(0, nel):

    # set 2 arrays to 0 every loop
    b_el=np.zeros(m*ndof,dtype=np.float64)
    a_el=np.zeros((m*ndof,m*ndof),dtype=np.float64)

    # integrate viscous term at 4 quadrature points
    for iq in [-1, 1]:
        for jq in [-1, 1]:
            for kq in [-1, 1]:

                # position & weight of quad. point
                rq=iq/sqrt3
                sq=jq/sqrt3
                tq=kq/sqrt3
                wq=1.*1.*1.

                # calculate shape functions
                N[0]=0.125*(1.-rq)*(1.-sq)*(1.-tq)
                N[1]=0.125*(1.+rq)*(1.-sq)*(1.-tq)
                N[2]=0.125*(1.+rq)*(1.+sq)*(1.-tq)
                N[3]=0.125*(1.-rq)*(1.+sq)*(1.-tq)
                N[4]=0.125*(1.-rq)*(1.-sq)*(1.+tq)
                N[5]=0.125*(1.+rq)*(1.-sq)*(1.+tq)
                N[6]=0.125*(1.+rq)*(1.+sq)*(1.+tq)
                N[7]=0.125*(1.-rq)*(1.+sq)*(1.+tq)

                # calculate shape function derivatives
                dNdr[0]=-0.125*(1.-sq)*(1.-tq) 
                dNdr[1]=+0.125*(1.-sq)*(1.-tq)
                dNdr[2]=+0.125*(1.+sq)*(1.-tq)
                dNdr[3]=-0.125*(1.+sq)*(1.-tq)
                dNdr[4]=-0.125*(1.-sq)*(1.+tq)
                dNdr[5]=+0.125*(1.-sq)*(1.+tq)
                dNdr[6]=+0.125*(1.+sq)*(1.+tq)
                dNdr[7]=-0.125*(1.+sq)*(1.+tq)

                dNds[0]=-0.125*(1.-rq)*(1.-tq) 
                dNds[1]=-0.125*(1.+rq)*(1.-tq)
                dNds[2]=+0.125*(1.+rq)*(1.-tq)
                dNds[3]=+0.125*(1.-rq)*(1.-tq)
                dNds[4]=-0.125*(1.-rq)*(1.+tq)
                dNds[5]=-0.125*(1.+rq)*(1.+tq)
                dNds[6]=+0.125*(1.+rq)*(1.+tq)
                dNds[7]=+0.125*(1.-rq)*(1.+tq)

                dNdt[0]=-0.125*(1.-rq)*(1.-sq) 
                dNdt[1]=-0.125*(1.+rq)*(1.-sq)
                dNdt[2]=-0.125*(1.+rq)*(1.+sq)
                dNdt[3]=-0.125*(1.-rq)*(1.+sq)
                dNdt[4]=+0.125*(1.-rq)*(1.-sq)
                dNdt[5]=+0.125*(1.+rq)*(1.-sq)
                dNdt[6]=+0.125*(1.+rq)*(1.+sq)
                dNdt[7]=+0.125*(1.-rq)*(1.+sq)

                # calculate jacobian matrix
                jcb=np.zeros((3,3),dtype=np.float64)
                for k in range(0,m):
                    jcb[0, 0] += dNdr[k]*x[icon[k,iel]]
                    jcb[0, 1] += dNdr[k]*y[icon[k,iel]]
                    jcb[0, 2] += dNdr[k]*z[icon[k,iel]]
                    jcb[1, 0] += dNds[k]*x[icon[k,iel]]
                    jcb[1, 1] += dNds[k]*y[icon[k,iel]]
                    jcb[1, 2] += dNds[k]*z[icon[k,iel]]
                    jcb[2, 0] += dNdt[k]*x[icon[k,iel]]
                    jcb[2, 1] += dNdt[k]*y[icon[k,iel]]
                    jcb[2, 2] += dNdt[k]*z[icon[k,iel]]

                # calculate the determinant of the jacobian
                jcob = np.linalg.det(jcb)

                # calculate inverse of the jacobian matrix
                jcbi = np.linalg.inv(jcb)

                # compute dNdx, dNdy, dNdz
                xq=0.0
                yq=0.0
                zq=0.0
                for k in range(0, m):
                    xq+=N[k]*x[icon[k,iel]]
                    yq+=N[k]*y[icon[k,iel]]
                    zq+=N[k]*z[icon[k,iel]]
                    dNdx[k]=jcbi[0,0]*dNdr[k]+jcbi[0,1]*dNds[k]+jcbi[0,2]*dNdt[k]
                    dNdy[k]=jcbi[1,0]*dNdr[k]+jcbi[1,1]*dNds[k]+jcbi[1,2]*dNdt[k]
                    dNdz[k]=jcbi[2,0]*dNdr[k]+jcbi[2,1]*dNds[k]+jcbi[2,2]*dNdt[k]

                # construct 3x8 b_mat matrix
                for i in range(0, m):
                    b_mat[0:6, 3*i:3*i+3] = [[dNdx[i],0.     ,0.     ],
                                             [0.     ,dNdy[i],0.     ],
                                             [0.     ,0.     ,dNdz[i]],
                                             [dNdy[i],dNdx[i],0.     ],
                                             [dNdz[i],0.     ,dNdx[i]],
                                             [0.     ,dNdz[i],dNdy[i]]]

                # compute elemental a_mat matrix
                a_el += b_mat.T.dot(c_mat.dot(b_mat))*mu(xq,yq,zq)*wq*jcob

                # compute elemental rhs vector
                for i in range(0, m):
                    b_el[ndof*i+0]+=N[i]*jcob*wq*rho(xq,yq,zq)*gx
                    b_el[ndof*i+1]+=N[i]*jcob*wq*rho(xq,yq,zq)*gy
                    b_el[ndof*i+2]+=N[i]*jcob*wq*rho(xq,yq,zq)*gz

    # integrate penalty term at 1 point
    rq=0.
    sq=0.
    tq=0.
    wq=2.*2.*2.

    # calculate shape functions
    N[0]=0.125*(1.-rq)*(1.-sq)*(1.-tq)
    N[1]=0.125*(1.+rq)*(1.-sq)*(1.-tq)
    N[2]=0.125*(1.+rq)*(1.+sq)*(1.-tq)
    N[3]=0.125*(1.-rq)*(1.+sq)*(1.-tq)
    N[4]=0.125*(1.-rq)*(1.-sq)*(1.+tq)
    N[5]=0.125*(1.+rq)*(1.-sq)*(1.+tq)
    N[6]=0.125*(1.+rq)*(1.+sq)*(1.+tq)
    N[7]=0.125*(1.-rq)*(1.+sq)*(1.+tq)

    dNdr[0]=-0.125*(1.-sq)*(1.-tq) 
    dNdr[1]=+0.125*(1.-sq)*(1.-tq)
    dNdr[2]=+0.125*(1.+sq)*(1.-tq)
    dNdr[3]=-0.125*(1.+sq)*(1.-tq)
    dNdr[4]=-0.125*(1.-sq)*(1.+tq)
    dNdr[5]=+0.125*(1.-sq)*(1.+tq)
    dNdr[6]=+0.125*(1.+sq)*(1.+tq)
    dNdr[7]=-0.125*(1.+sq)*(1.+tq)

    dNds[0]=-0.125*(1.-rq)*(1.-tq) 
    dNds[1]=-0.125*(1.+rq)*(1.-tq)
    dNds[2]=+0.125*(1.+rq)*(1.-tq)
    dNds[3]=+0.125*(1.-rq)*(1.-tq)
    dNds[4]=-0.125*(1.-rq)*(1.+tq)
    dNds[5]=-0.125*(1.+rq)*(1.+tq)
    dNds[6]=+0.125*(1.+rq)*(1.+tq)
    dNds[7]=+0.125*(1.-rq)*(1.+tq)

    dNdt[0]=-0.125*(1.-rq)*(1.-sq) 
    dNdt[1]=-0.125*(1.+rq)*(1.-sq)
    dNdt[2]=-0.125*(1.+rq)*(1.+sq)
    dNdt[3]=-0.125*(1.-rq)*(1.+sq)
    dNdt[4]=+0.125*(1.-rq)*(1.-sq)
    dNdt[5]=+0.125*(1.+rq)*(1.-sq)
    dNdt[6]=+0.125*(1.+rq)*(1.+sq)
    dNdt[7]=+0.125*(1.-rq)*(1.+sq)

    # calculate jacobian matrix
    jcb=np.zeros((3,3),dtype=np.float64)
    for k in range(0,m):
        jcb[0, 0] += dNdr[k]*x[icon[k,iel]]
        jcb[0, 1] += dNdr[k]*y[icon[k,iel]]
        jcb[0, 2] += dNdr[k]*z[icon[k,iel]]
        jcb[1, 0] += dNds[k]*x[icon[k,iel]]
        jcb[1, 1] += dNds[k]*y[icon[k,iel]]
        jcb[1, 2] += dNds[k]*z[icon[k,iel]]
        jcb[2, 0] += dNdt[k]*x[icon[k,iel]]
        jcb[2, 1] += dNdt[k]*y[icon[k,iel]]
        jcb[2, 2] += dNdt[k]*z[icon[k,iel]]

    # calculate determinant of the jacobian
    jcob = np.linalg.det(jcb)

    # calculate the inverse of the jacobian
    jcbi = np.linalg.inv(jcb)

    # compute dNdx and dNdy
    for k in range(0,m):
        dNdx[k]=jcbi[0,0]*dNdr[k]+jcbi[0,1]*dNds[k]+jcbi[0,2]*dNdt[k]
        dNdy[k]=jcbi[1,0]*dNdr[k]+jcbi[1,1]*dNds[k]+jcbi[1,2]*dNdt[k]
        dNdz[k]=jcbi[2,0]*dNdr[k]+jcbi[2,1]*dNds[k]+jcbi[2,2]*dNdt[k]

    # compute gradient matrix
    for i in range(0,m):
        b_mat[0:6, 3*i:3*i+3] = [[dNdx[i],0.     ,0.     ],
                                 [0.     ,dNdy[i],0.     ],
                                 [0.     ,0.     ,dNdz[i]],
                                 [dNdy[i],dNdx[i],0.     ],
                                 [dNdz[i],0.     ,dNdx[i]],
                                 [0.     ,dNdz[i],dNdy[i]]]

    # compute elemental matrix
    a_el += b_mat.T.dot(k_mat.dot(b_mat))*penalty*wq*jcob

    # apply boundary conditions
    for k1 in range(0,m):
        for i1 in range(0,ndof):
            m1 =ndof*icon[k1,iel]+i1
            if bc_fix[m1]: 
               fixt=bc_val[m1]
               ikk=ndof*k1+i1
               aref=a_el[ikk,ikk]
               for jkk in range(0,m*ndof):
                   b_el[jkk]-=a_el[jkk,ikk]*fixt
                   a_el[ikk,jkk]=0.
                   a_el[jkk,ikk]=0.
               a_el[ikk,ikk]=aref
               b_el[ikk]=aref*fixt

    # assemble matrix a_mat and right hand side rhs
    for k1 in range(0,m):
        for i1 in range(0,ndof):
            ikk=ndof*k1          +i1
            m1 =ndof*icon[k1,iel]+i1
            for k2 in range(0,m):
                for i2 in range(0,ndof):
                    jkk=ndof*k2          +i2
                    m2 =ndof*icon[k2,iel]+i2
                    a_mat[m1,m2]+=a_el[ikk,jkk]
            rhs[m1]+=b_el[ikk]

a_mat=csr_matrix(a_mat)

print("build FE system: %.3f s" % (time.time() - start))

#################################################################
# solve system
#################################################################
start = time.time()

sol = sps.linalg.spsolve(a_mat,rhs)

print("solve time: %.3f s" % (time.time() - start))

#####################################################################
# put solution into separate x,y velocity arrays
#####################################################################
start = time.time()

u,v,w=np.reshape(sol,(nnp,3)).T

print("     -> u (m,M) %.4f %.4f " %(np.min(u),np.max(u)))
print("     -> v (m,M) %.4f %.4f " %(np.min(v),np.max(v)))
print("     -> w (m,M) %.4f %.4f " %(np.min(w),np.max(w)))

np.savetxt('velocity.ascii',np.array([x,y,z,u,v,w]).T,header='# x,y,z,u,v,w')

print("transfer solution: %.3f s" % (time.time() - start))
#####################################################################
# retrieve pressure
#####################################################################
start = time.time()

xc = np.zeros(nel,dtype=np.float64)  
yc = np.zeros(nel,dtype=np.float64)  
zc = np.zeros(nel,dtype=np.float64)  
p  = np.zeros(nel,dtype=np.float64)  
exx = np.zeros(nel,dtype=np.float64)  
eyy = np.zeros(nel,dtype=np.float64)  
ezz = np.zeros(nel,dtype=np.float64)  
exy = np.zeros(nel,dtype=np.float64)  
exz = np.zeros(nel,dtype=np.float64)  
eyz = np.zeros(nel,dtype=np.float64)  
visc = np.zeros(nel,dtype=np.float64)  
dens = np.zeros(nel,dtype=np.float64)  
sr = np.zeros(nel,dtype=np.float64)  

for iel in range(0,nel):

    rq=0.
    sq=0.
    tq=0.
    wq=2.*2.*2.

    N[0]=0.125*(1.-rq)*(1.-sq)*(1.-tq)
    N[1]=0.125*(1.+rq)*(1.-sq)*(1.-tq)
    N[2]=0.125*(1.+rq)*(1.+sq)*(1.-tq)
    N[3]=0.125*(1.-rq)*(1.+sq)*(1.-tq)
    N[4]=0.125*(1.-rq)*(1.-sq)*(1.+tq)
    N[5]=0.125*(1.+rq)*(1.-sq)*(1.+tq)
    N[6]=0.125*(1.+rq)*(1.+sq)*(1.+tq)
    N[7]=0.125*(1.-rq)*(1.+sq)*(1.+tq)

    dNdr[0]=-0.125*(1.-sq)*(1.-tq) 
    dNdr[1]=+0.125*(1.-sq)*(1.-tq)
    dNdr[2]=+0.125*(1.+sq)*(1.-tq)
    dNdr[3]=-0.125*(1.+sq)*(1.-tq)
    dNdr[4]=-0.125*(1.-sq)*(1.+tq)
    dNdr[5]=+0.125*(1.-sq)*(1.+tq)
    dNdr[6]=+0.125*(1.+sq)*(1.+tq)
    dNdr[7]=-0.125*(1.+sq)*(1.+tq)

    dNds[0]=-0.125*(1.-rq)*(1.-tq) 
    dNds[1]=-0.125*(1.+rq)*(1.-tq)
    dNds[2]=+0.125*(1.+rq)*(1.-tq)
    dNds[3]=+0.125*(1.-rq)*(1.-tq)
    dNds[4]=-0.125*(1.-rq)*(1.+tq)
    dNds[5]=-0.125*(1.+rq)*(1.+tq)
    dNds[6]=+0.125*(1.+rq)*(1.+tq)
    dNds[7]=+0.125*(1.-rq)*(1.+tq)

    dNdt[0]=-0.125*(1.-rq)*(1.-sq) 
    dNdt[1]=-0.125*(1.+rq)*(1.-sq)
    dNdt[2]=-0.125*(1.+rq)*(1.+sq)
    dNdt[3]=-0.125*(1.-rq)*(1.+sq)
    dNdt[4]=+0.125*(1.-rq)*(1.-sq)
    dNdt[5]=+0.125*(1.+rq)*(1.-sq)
    dNdt[6]=+0.125*(1.+rq)*(1.+sq)
    dNdt[7]=+0.125*(1.-rq)*(1.+sq)

    # calculate jacobian matrix
    jcb=np.zeros((3,3),dtype=np.float64)
    for k in range(0,m):
        jcb[0, 0] += dNdr[k]*x[icon[k,iel]]
        jcb[0, 1] += dNdr[k]*y[icon[k,iel]]
        jcb[0, 2] += dNdr[k]*z[icon[k,iel]]
        jcb[1, 0] += dNds[k]*x[icon[k,iel]]
        jcb[1, 1] += dNds[k]*y[icon[k,iel]]
        jcb[1, 2] += dNds[k]*z[icon[k,iel]]
        jcb[2, 0] += dNdt[k]*x[icon[k,iel]]
        jcb[2, 1] += dNdt[k]*y[icon[k,iel]]
        jcb[2, 2] += dNdt[k]*z[icon[k,iel]]

    # calculate determinant of the jacobian
    jcob=np.linalg.det(jcb)

    # calculate the inverse of the jacobian
    jcbi=np.linalg.inv(jcb)

    for k in range(0,m):
        dNdx[k]=jcbi[0,0]*dNdr[k]+jcbi[0,1]*dNds[k]+jcbi[0,2]*dNdt[k]
        dNdy[k]=jcbi[1,0]*dNdr[k]+jcbi[1,1]*dNds[k]+jcbi[1,2]*dNdt[k]
        dNdz[k]=jcbi[2,0]*dNdr[k]+jcbi[2,1]*dNds[k]+jcbi[2,2]*dNdt[k]

    for k in range(0, m):
        xc[iel]+=N[k]*x[icon[k,iel]]
        yc[iel]+=N[k]*y[icon[k,iel]]
        zc[iel]+=N[k]*z[icon[k,iel]]
        exx[iel]+=dNdx[k]*u[icon[k,iel]]
        eyy[iel]+=dNdy[k]*v[icon[k,iel]]
        ezz[iel]+=dNdz[k]*w[icon[k,iel]]
        exy[iel]+=0.5*dNdy[k]*u[icon[k,iel]]+0.5*dNdx[k]*v[icon[k,iel]]
        exz[iel]+=0.5*dNdz[k]*u[icon[k,iel]]+0.5*dNdx[k]*w[icon[k,iel]]
        eyz[iel]+=0.5*dNdz[k]*v[icon[k,iel]]+0.5*dNdy[k]*w[icon[k,iel]]

    p[iel]=-penalty*(exx[iel]+eyy[iel]+ezz[iel])
    visc[iel]=mu(xc[iel],yc[iel],zc[iel])
    dens[iel]=rho(xc[iel],yc[iel],zc[iel])
    sr[iel]=np.sqrt(0.5*(exx[iel]*exx[iel]+eyy[iel]*eyy[iel]+ezz[iel]*ezz[iel])
                    +exy[iel]*exy[iel]+exz[iel]*exz[iel]+eyz[iel]*eyz[iel])

print("     -> p (m,M) %.4f %.4f " %(np.min(p),np.max(p)))
print("     -> exx (m,M) %.4f %.4f " %(np.min(exx),np.max(exx)))
print("     -> eyy (m,M) %.4f %.4f " %(np.min(eyy),np.max(eyy)))
print("     -> ezz (m,M) %.4f %.4f " %(np.min(ezz),np.max(ezz)))
print("     -> exy (m,M) %.4f %.4f " %(np.min(exy),np.max(exy)))
print("     -> exz (m,M) %.4f %.4f " %(np.min(exz),np.max(exz)))
print("     -> eyz (m,M) %.4f %.4f " %(np.min(eyz),np.max(eyz)))
print("     -> visc (m,M) %.4f %.4f " %(np.min(visc),np.max(visc)))
print("     -> dens (m,M) %.4f %.4f " %(np.min(dens),np.max(dens)))

np.savetxt('pressure.ascii',np.array([xc,yc,zc,p]).T,header='# xc,yc,zc,p')
np.savetxt('strainrate.ascii',np.array([xc,yc,zc,exx,eyy,exy]).T,header='# xc,yc,exx,eyy,exy')

print("compute p and strainrate: %.3f s" % (time.time() - start))

#####################################################################
# plot of solution
#####################################################################
start = time.time()

if visu==1:
   vtufile=open("solution.vtu","w")
   vtufile.write("<VTKFile type='UnstructuredGrid' version='0.1' byte_order='BigEndian'> \n")
   vtufile.write("<UnstructuredGrid> \n")
   vtufile.write("<Piece NumberOfPoints=' %5d ' NumberOfCells=' %5d '> \n" %(nnp,nel))
   #####
   vtufile.write("<Points> \n")
   vtufile.write("<DataArray type='Float32' NumberOfComponents='3' Format='ascii'> \n")
   for i in range(0,nnp):
       vtufile.write("%10f %10f %10f \n" %(x[i],y[i],z[i]))
   vtufile.write("</DataArray>\n")
   vtufile.write("</Points> \n")
   #####
   vtufile.write("<CellData Scalars='scalars'>\n")
   #--
   vtufile.write("<DataArray type='Float32' Name='element id' Format='ascii'> \n")
   for iel in range (0,nel):
       vtufile.write("%d\n" % iel)
   vtufile.write("</DataArray>\n")
   #--
   vtufile.write("<DataArray type='Float32' Name='p' Format='ascii'> \n")
   for iel in range (0,nel):
       vtufile.write("%f\n" % p[iel])
   vtufile.write("</DataArray>\n")
   #--
   vtufile.write("<DataArray type='Float32' Name='density' Format='ascii'> \n")
   for iel in range (0,nel):
       vtufile.write("%f\n" % dens[iel])
   vtufile.write("</DataArray>\n")
   #--
   vtufile.write("<DataArray type='Float32' Name='viscosity' Format='ascii'> \n")
   for iel in range (0,nel):
       vtufile.write("%f\n" % visc[iel])
   vtufile.write("</DataArray>\n")
   #--
   vtufile.write("<DataArray type='Float32' Name='strainrate' Format='ascii'> \n")
   for iel in range (0,nel):
       vtufile.write("%f\n" % sr[iel])
   vtufile.write("</DataArray>\n")
   #--
   vtufile.write("</CellData>\n")
   #####
   vtufile.write("<PointData Scalars='scalars'>\n")
   #--
   vtufile.write("<DataArray type='Float32' NumberOfComponents='3' Name='velocity' Format='ascii'> \n")
   for i in range(0,nnp):
       vtufile.write("%10f %10f %10f \n" %(u[i],v[i],w[i]))
   vtufile.write("</DataArray>\n")
   #--
   vtufile.write("</PointData>\n")
   #####
   vtufile.write("<Cells>\n")
   #--
   vtufile.write("<DataArray type='Int32' Name='connectivity' Format='ascii'> \n")
   for iel in range (0,nel):
       vtufile.write("%d %d %d %d %d %d %d %d\n" %(icon[0,iel],icon[1,iel],icon[2,iel],icon[3,iel],
                                       icon[4,iel],icon[5,iel],icon[6,iel],icon[7,iel]))
   vtufile.write("</DataArray>\n")
   #--
   vtufile.write("<DataArray type='Int32' Name='offsets' Format='ascii'> \n")
   for iel in range (0,nel):
       vtufile.write("%d \n" %((iel+1)*8))
   vtufile.write("</DataArray>\n")
   #--
   vtufile.write("<DataArray type='Int32' Name='types' Format='ascii'>\n")
   for iel in range (0,nel):
       vtufile.write("%d \n" %12)
   vtufile.write("</DataArray>\n")
   #--
   vtufile.write("</Cells>\n")
   #####
   vtufile.write("</Piece>\n")
   vtufile.write("</UnstructuredGrid>\n")
   vtufile.write("</VTKFile>\n")
   vtufile.close()
   print("export to vtu: %.3f s" % (time.time() - start))

print("-----------------------------")
print("------------the end----------")
print("-----------------------------")




