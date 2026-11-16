#!/usr/bin/env python3
"""CT36 standalone x-only 7+7 dual certificate on public F_101 toy curves.
No imports from CT29-35, no DLP oracle, no extension-field root choices.
All results development-only [pcc:unverified].
"""
import json
P=101
# (name, [source, middle, end], [nondual degree-7 kernels], [normalized dual kernels])
CASES=[
 ('E109',((1,46),(26,58),(59,27)),((72,100,35,1),(99,94,75,1)),((58,26,58,1),(13,62,81,1))),
 ('E113',((44,21),(69,50),(23,7)),((59,46,8,1),(53,19,40,1)),((29,88,45,1),(11,64,23,1)))
]
def square_root_table():
 d={}
 for y in range(P):d.setdefault(y*y%P,[]).append(y)
 return d
SQ=square_root_table()
def points(curve):
 a,b=curve
 return [None]+[(x,y) for x in range(P) for y in SQ.get((x**3+a*x+b)%P,())]
def add(p,q,a):
 if p is None:return q
 if q is None:return p
 x,y=p;u,v=q
 if x==u and (y+v)%P==0:return None
 if p==q:
  if y==0:return None
  slope=((3*x*x+a)*pow(2*y,-1,P))%P
 else:slope=((v-y)*pow(u-x,-1,P))%P
 xx=(slope*slope-x-u)%P
 return (xx,(slope*(x-xx)-y)%P)
def mul(point,n,a):
 z=None
 while n:
  if n&1:z=add(z,point,a)
  point=add(point,point,a);n//=2
 return z
def poly_deriv(q):return tuple(i*q[i]%P for i in range(1,len(q)))
def poly_eval(q,x):
 z=0
 for c in reversed(q):z=(z*x+c)%P
 return z
def scale(pt,u):
 if pt is None:return None
 x,y=pt;return (x*u*u%P,y*u*u*u%P)
def codomain(a,b,h):
 # Normalized degree-7 Velu from Newton identities over the *coefficient field*.
 s1=-h[2]%P;s2=(h[2]**2-2*h[1])%P;s3=(-h[2]**3+3*h[2]*h[1]-3*h[0])%P
 return ((a-10*(3*s2+3*a))%P,(b-14*(5*s3+3*a*s1+6*b))%P)
def velu7(pt,a,b,h):
 """X=N(x)/h(x)^2, Y=y*dX/dx from independent quotient derivatives."""
 if pt is None:return None
 x,y=pt
 d=7; h0=poly_eval(h,x)
 if h0==0: return None # kernel on rational points
 h1=poly_eval(poly_deriv(h),x);h2=poly_eval(poly_deriv(poly_deriv(h)),x);h3=6
 f=(x**3+a*x+b)%P;f1=(3*x*x+a)%P;f2=(6*x)%P
 z=(d*x+2*h[2])%P
 n=(z*h0*h0-2*f1*h1*h0+4*f*(h1*h1-h0*h2))%P
 nd=(d*h0*h0+z*2*h0*h1-2*(f2*h1*h0+f1*h2*h0+f1*h1*h1)+4*(f1*(h1*h1-h0*h2)+f*(h1*h2-h0*h3)))%P
 hi=pow(h0,-1,P)
 X=n*hi*hi%P
 Y=y*(nd*h0-2*n*h1)*hi**3%P
 return X,Y

def check_case(name,curves,kernels,duals):
 e0,e1,e2=curves;h0,h1=kernels;d0,d1=duals
 scale_curve=lambda curve,u: (curve[0]*pow(u,4,P)%P,curve[1]*pow(u,6,P)%P)
 for i in (0,1):
  if codomain(*curves[i],kernels[i])!=curves[i+1]:raise AssertionError(('wrong forward codomain',i))
  if codomain(*curves[i+1],duals[i])!=scale_curve(curves[i],7):raise AssertionError(('wrong dual codomain',i))
 S0=points(e0);S1=points(e1);S2=points(e2)
 if len(set(S0))!=len(S0) or [len(S0),len(S1),len(S2)]!=([109]*3 if name=='E109' else [113]*3):raise AssertionError('point inventory')
 checks={'forward1':0,'forward2':0,'dual1':0,'dual2':0,'two_hop':0,'full_49_dual':0}
 for P0 in S0:
  Q1=velu7(P0,*e0,h0)
  if Q1 not in S1:raise AssertionError(('forward 1 equation',P0,Q1))
  checks['forward1']+=1
  Q2=velu7(Q1,*e1,h1)
  if Q2 not in S2:raise AssertionError(('forward 2 equation',P0,Q2))
  checks['forward2']+=1
  R1=velu7(Q1,*e1,d0)
  T1=scale(mul(P0,7,e0[0]),7)
  if R1!=T1:raise AssertionError(('dual 1 composition',P0,R1,T1))
  checks['dual1']+=1
  R2=velu7(Q2,*e2,d1)
  T2=scale(mul(Q1,7,e1[0]),7)
  if R2!=T2:raise AssertionError(('dual 2 composition',P0,R2,T2))
  checks['dual2']+=1
  checks['two_hop']+=1
  # Unwind the target twist: [7]^*E1 -> E1, dual first hop, and scale 7 once more.
  back=scale(velu7(scale(R2,pow(7,-1,P)),*e1,d0),7)
  expected=scale(mul(P0,49,e0[0]),49)
  if back!=expected:raise AssertionError(('degree49 dual',P0,back,expected))
  checks['full_49_dual']+=1
 # Check sign-negated kernels must NOT give the expected dual identity.
 bad=0
 for P0 in S0:
  Q1=velu7(P0,*e0,h0)
  wrong=velu7(Q1,*e1,h1) # forward a second time; wrong codomain
  if wrong!=scale(mul(P0,7,e0[0]),7):bad+=1
 if bad==0:raise AssertionError('negative control failed to reject')
 return dict(case=name,points=len(S0),checks=checks,wrong_reverse_kernel_rejected=bad,forward_kernels=kernels,dual_kernels=duals,dual_targets=[scale_curve(e0,7),scale_curve(e1,7)],standing='pcc:unverified')

def main():
 for args in CASES:print(json.dumps(check_case(*args),sort_keys=True))
 print('CT36 PASS [pcc:unverified]')

# Separate polynomial coefficient ring for universal rational-function checks.
# This checks the algebraic maps, not only their action on 109/113 base-field points.
def trim(v):
 v=[int(c)%P for c in v]
 while len(v)>1 and v[-1]==0:v.pop()
 return tuple(v) if v else (0,)
def pa(a,b):
 return trim([(a[i] if i<len(a) else 0)+(b[i] if i<len(b) else 0) for i in range(max(len(a),len(b)))])
def pn(a):return tuple(-c%P for c in a)
def ps(a,b):return pa(a,pn(b))
def pc(a,c):return trim([int(c)*v for v in a])
def pm(a,b):
 z=[0]*(len(a)+len(b)-1)
 for i,u in enumerate(a):
  for j,v in enumerate(b):z[i+j]=(z[i+j]+u*v)%P
 return trim(z)
def powpoly(a,k):
 z=(1,)
 for _ in range(k):z=pm(z,a)
 return z
def pdivmod(a,b):
 if b==(0,):raise ZeroDivisionError()
 r=list(a);q=[0]*max(1,(len(a)-len(b)+1));inv=pow(b[-1],-1,P)
 while len(r)>=len(b) and any(r):
  k=len(r)-len(b);c=r[-1]*inv%P;q[k]=c
  for i,v in enumerate(b):r[k+i]=(r[k+i]-c*v)%P
  while len(r)>1 and r[-1]==0:r.pop()
 return trim(q),trim(r)
def polyvelu(a,b,h):
 f=(b,a,0,1);df=(a,0,3);h1=poly_deriv(h);h2=poly_deriv(h1)
 # (7x+2h[2])h²-2f'h'h+4f[(h')²-hh''].
 N=pa(ps(pm((2*h[2]%P,7),powpoly(h,2)),pc(pm(pm(df,h1),h),2)),pc(pm(f,ps(powpoly(h1,2),pm(h,h2))),4))
 return N,powpoly(h,2)
def homogenize(q,N,D,degree):
 out=(0,)
 for i,c in enumerate(q):
  if c:out=pa(out,pc(pm(powpoly(N,i),powpoly(D,degree-i)),c))
 return out

def psi7_and_mult7(a,b):
 x=(0,1);f=(b,a,0,1)
 p3=trim((-a*a,12*b,6*a,0,3))
 f4=trim((-8*b*b-a*a*a,-4*a*b,-5*a*a,20*b,5*a,0,1))
 f2=powpoly(f,2)
 p5=ps(pc(pm(f2,f4),32),powpoly(p3,3))
 p7=ps(pm(p5,powpoly(p3,3)),pc(pm(f2,powpoly(f4,3)),128))
 # 6- and 8-division polynomials are 2y*J6 and 4y*J8.
 j6=pm(p3,ps(p5,pc(powpoly(f4,2),4)))
 j8=pm(f4,ps(pm(powpoly(p3,3),ps(p5,pc(powpoly(f4,2),4))),powpoly(p5,2)))
 psi6psi8=pc(pm(f,pm(j6,j8)),8)
 return p7,ps(pm(x,powpoly(p7,2)),psi6psi8),powpoly(p7,2)

def symbolic_seven_dual(a,b,h,source_mid,dual):
 fn,fd=polyvelu(a,b,h)
 gn,gd=polyvelu(*source_mid,dual)
 nh=homogenize(gn,fn,fd,7)
 # dual denominator=(dual_h(N/D))²; the extra D normalizes degree 49.
 hh=homogenize(dual,fn,fd,3)
 dh=pm(fd,powpoly(hh,2))
 division7,num7,den7=psi7_and_mult7(a,b)
 q,r=pdivmod(division7,h)
 if r!=(0,):raise AssertionError(('kernel factor fails 7-division polynomial',h,r))
 # scale_7([7]P).x = 49 * [7]P.x
 difference=ps(pm(nh,den7),pc(pm(dh,num7),49))
 if difference!=(0,):
  raise AssertionError(('universal degree7 composition failed',a,b,degree_str(difference)))
 return {'source':(a,b),'forward_h':h,'dual_h':dual,
         'source_psi7_degree':len(division7)-1,
         'normalized_dual_composite_numerator_degree':len(nh)-1,
         'normalized_dual_composite_denominator_degree':len(dh)-1,
         'symbolic_x_identity':True}
def degree_str(q):return len(q)-1

def symbolic_checks():
 for name,curves,kernels,duals in CASES:
  for hop in (0,1):
   x=symbolic_seven_dual(*curves[hop],kernels[hop],curves[hop+1],duals[hop])
   r=pdivmod(psi7_and_mult7(*curves[hop+1])[0],duals[hop])[1]
   if r!=(0,):raise AssertionError(('dual kernel fails 7-division polynomial',name,hop,r))
   mutated=list(duals[hop]);mutated[0]=(mutated[0]+1)%P;mutated=tuple(mutated)
   if pdivmod(psi7_and_mult7(*curves[hop+1])[0],mutated)[1]==(0,):
    raise AssertionError(('modified dual kernel unexpectedly divides psi7',name,hop))
   try:
    symbolic_seven_dual(*curves[hop],kernels[hop],curves[hop+1],mutated)
   except AssertionError:
    pass
   else:
    raise AssertionError(('modified dual kernel unexpectedly reproduces [7]',name,hop))
   print(json.dumps(dict(case=name,hop=hop,negative_mutations_rejected=2,**x),sort_keys=True))
 print('CT36 UNIVERSAL POLYNOMIAL IDENTITIES PASS [pcc:unverified]')

def exhaustive_reverse_group_checks():
 for name,curves,kernels,duals in CASES:
  for hop in (0,1):
   src=curves[hop+1]; tgt=(curves[hop][0]*pow(7,4,P)%P,curves[hop][1]*pow(7,6,P)%P)
   S=points(src); T=set(points(tgt)); mp={x:velu7(x,*src,duals[hop]) for x in S}
   if set(mp.values())!=T:raise AssertionError(('reverse not a bijection',name,hop))
   for A in S:
    for B in S:
     lhs=mp[add(A,B,src[0])]
     rhs=add(mp[A],mp[B],tgt[0])
     if lhs!=rhs:raise AssertionError(('reverse fails group law',name,hop,A,B))
   print(json.dumps(dict(case=name,reverse_hop=hop,ordered_pair_additions=len(S)**2,
                         full_bijection=True,all_homomorphism_pairs=True,standing='pcc:unverified'),sort_keys=True))
 print('CT36 ALL REVERSE HOMOMORPHISMS PASS [pcc:unverified]')

if __name__=='__main__':
 main()
 symbolic_checks()
 exhaustive_reverse_group_checks()
