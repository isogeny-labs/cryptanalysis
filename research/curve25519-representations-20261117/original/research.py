"""Reproducible exact diagnostics. No wall-time benchmarking or speedup claims."""
from dataclasses import dataclass
from collections import defaultdict, Counter
from itertools import combinations_with_replacement
from math import isqrt
import json, random, hashlib, platform
from pathlib import Path
import sympy as S
OUT=Path(__file__).resolve().parent
@dataclass
class Curve:
 p:int
 a2:int
 a4:int
 a6:int=0
 def rhs(self,x):return (x**3+self.a2*x*x+self.a4*x+self.a6)%self.p
 def neg(self,P):return None if P is None else (P[0],-P[1]%self.p)
 def add(self,P,Q):
  if P is None:return Q
  if Q is None:return P
  p=self.p;x,y=P;u,v=Q
  if x==u and (y+v)%p==0:return None
  s=((3*x*x+2*self.a2*x+self.a4)*pow(2*y,-1,p) if P==Q else (v-y)*pow(u-x,-1,p))%p
  z=(s*s-self.a2-x-u)%p
  return z,(s*(x-z)-y)%p
 def mul(self,n,P):
  if n<0:return self.mul(-n,self.neg(P))
  R=None
  while n:
   if n&1:R=self.add(R,P)
   P=self.add(P,P);n//=2
  return R
 def contains(self,P):return P is None or P[1]**2%self.p==self.rhs(P[0])
 def points(self):
  roots=defaultdict(list)
  for y in range(self.p):roots[y*y%self.p].append(y)
  return [None]+[(x,y) for x in range(self.p) for y in roots[self.rhs(x)]]
 def record(self,r,G):
  d={'field':{'p':self.p,'degree':1,'encoding':'least_nonnegative_residues'},'curve':{'model':'y2=x3+a2*x2+a4*x+a6','a2':self.a2%self.p,'a4':self.a4%self.p,'a6':self.a6%self.p,'r':r,'G':G}}
  h=hashlib.sha256(json.dumps(d,sort_keys=True,separators=(',',':')).encode()).hexdigest()
  return dict(d,curve_id=f'EC1P{self.p.bit_length()}Ctoy_h{h[:12]}',sha256=h)
def subgroup(C,r,pts,h):
 for P in pts[1:]:
  G=C.mul(h,P)
  if G is not None and C.mul(r,G) is None:return G
 raise AssertionError('no subgroup generator')
def reps(C,H):return sorted(P for P in H if P is not None and P<C.neg(P))
def signset(C,B):return sorted(set(B+[C.neg(P) for P in B]))
def pair_sums(C,B):
 D=defaultdict(int);pts=signset(C,B)
 for i,P in enumerate(pts):
  for Q in pts[i:]:D[C.add(P,Q)]+=1
 return D

def iso(C,P):
 if P is None or P[0]==0:return None
 u,v=P;p=C.p
 return (u+C.a2+pow(u,-1,p))%p,v*(1-pow(u*u,-1,p))%p

def coord(C,P,model):
 u=P[0];p=C.p
 if model=='u':return u
 if model=='X':return (u+C.a2*pow(3,-1,p))%p
 if model=='y':return (u-1)*pow(u+1,-1,p)%p
 if model=='z':return (u+pow(u,-1,p))%p
 raise ValueError(model)

def census(C,r,G,A=None):
 H=[C.mul(i,G) for i in range(r)];assert len(set(H))==r
 R=reps(C,H);k=min(12,max(3,isqrt(r)//2),(r-1)//2)
 policies=['u','y','z','random'] if A is not None else ['u','random']
 rows=[];bases={}
 for policy in policies:
  B=R.copy()
  if policy=='random':random.Random(20261117+C.p).shuffle(B)
  else:B.sort(key=lambda P:coord(C,P,policy))
  B=B[:k];D=pair_sums(C,B);Drev=pair_sums(C,list(reversed(B)));assert D==Drev
  assert all(C.add(P,Q) in D for P in B for Q in B)
  assert pair_sums(C,[])=={}
  assert set(D)<=set(H)
  rec={'policy':policy,'r':r,'p':C.p,'sign_classes':k,'actual_signed_points':2*k,'covered_nonidentity':len(set(D)-{None}),'coverage':len(set(D)-{None})/(r-1),'unordered_signed_pairs':sum(D.values()),'max_multiplicity':max(D.values()),'base':B}
  if A is not None:
   Cp=Curve(C.p,-2*A,A*A-4);I=[iso(C,P) for P in H]
   assert len(set(I))==r and all(Cp.contains(P) for P in I)
   for i in range(min(r,32)):
    P,Q=H[i],H[(i*7+3)%r]
    assert iso(C,C.add(P,Q))==Cp.add(iso(C,P),iso(C,Q))
   BI=[iso(C,P) for P in B];DI=pair_sums(Cp,BI)
   assert {iso(C,P):n for P,n in D.items()}==dict(DI)
   rec['transported_coverage_equal']=True
  rows.append(rec);bases[policy]=B
 if A is not None:
  distinct={m:len({coord(C,P,m) for P in H[1:]}) for m in ['u','y','z']}
  assert len(set(distinct.values()))==1 and distinct['u']==(r-1)//2
 else:distinct={'u':len({P[0] for P in H[1:]})}
 return {'curve':C.record(r,G),'order':len(C.points()),'r':r,'G':G,'coordinate_distinct_counts':distinct,'rows':rows},H,bases

def select_curves(p):
 roots={y*y%p for y in range(p)};chosen=[]
 for A in range(3,min(p-2,1000)):
  if (A*A-4)%p==0 or (-A-2)%p not in roots:continue
  d=-(A-2)*pow(A+2,-1,p)%p
  if d in roots:continue
  C=Curve(p,A,1);pts=C.points();n=len(pts)
  if n%8 or n//8<11 or not S.isprime(n//8):continue
  r=n//8;G=subgroup(C,r,pts,8);chosen.append((C,r,G,A))
  if len(chosen)==3:break
 return chosen

def prime_control(p):
 for b in range(1,p):
  if (4*(-3)**3+27*b*b)%p==0:continue
  C=Curve(p,0,-3,b);pts=C.points();r=len(pts)
  if S.isprime(r):return C,r,pts[1]
 return None

def semaev3(x,y,z,a,b):
 return (x-y)**2*z*z-2*((x+y)*(x*y+a)+2*b)*z+(x*y-a)**2-4*b*(x+y)
def s3_for(C,x,y,z):
 p=C.p;t=C.a2*pow(3,-1,p)%p
 a=(C.a4-C.a2*C.a2*pow(3,-1,p))%p
 b=(2*C.a2**3*pow(27,-1,p)-C.a2*C.a4*pow(3,-1,p)+C.a6)%p
 return semaev3(x+t,y+t,z+t,a,b)

def symbolic_diagnostics(C,r,G,B):
 x,y=S.symbols('x y');p=C.p;R=C.mul(3,G);records=[]
 for model in ['u','X','y','z']:
  if model=='u':poly=s3_for(C,x,y,R[0])
  elif model=='X':
   t=C.a2*pow(3,-1,p)%p
   poly=s3_for(C,x-t,y-t,R[0])
  elif model=='y':
   poly=S.cancel(s3_for(C,(1+x)/(1-x),(1+y)/(1-y),R[0])).as_numer_denom()[0]
  else:
   Cp=Curve(p,-2*C.a2,C.a2*C.a2-4);Rt=iso(C,R)
   poly=s3_for(Cp,x+C.a2,y+C.a2,Rt[0])
  poly=S.Poly(poly,x,y,modulus=p)
  roots=[coord(C,P,model) for P in B]
  allowed=[]
  for i,u in enumerate(roots):
   for j,v in enumerate(roots):
    if int(poly.eval({x:u,y:v}))%p==0:allowed.append((i,j))
  exact=[]
  for i,P in enumerate(B):
   for j,Q in enumerate(B):
    if any(C.add(C.mul(a,P),C.mul(b,Q))==R for a in [-1,1] for b in [-1,1]):exact.append((i,j))
  assert set(allowed)==set(exact),(model,allowed,exact)
  F=S.Poly(S.prod(x-a for a in roots),x,modulus=p)
  records.append({'model':model,'input_degree':poly.total_degree(),'input_terms':len(poly.terms()),'base_polynomial_degree':F.degree(),'base_polynomial_terms':len(F.terms()),'candidate_root_pairs':len(allowed),'exact_root_pairs':len(exact),'equation':str(poly.as_expr())})
 # Retained Edwards equations for P+Q=R, with products split into auxiliary variables.
 d=-(C.a2-2)*pow(C.a2+2,-1,p)%p
 c=next(i for i in range(p) if i*i%p==(-C.a2-2)%p)
 def ed(P):
  if P is None:return 0,1
  u,v=P;return c*u*pow(v,-1,p)%p,(u-1)*pow(u+1,-1,p)%p
 for P in signset(C,B):
  for Q in signset(C,B):
   Z=C.add(P,Q);x1,y1=ed(P);x2,y2=ed(Q);xr,yr=ed(Z)
   t=x1*x2%p;w=y1*y2%p;h=t*w%p
   assert (xr*(1+d*h)-x1*y2-y1*x2)%p==0
   assert (yr*(1-d*h)-w-t)%p==0
 # Projective identity Z*(Y²Z-X³-A X²Z-XZ²)=0 admits all Z=0 points;
 # demand the actual homogenized curve and valid nonzero coordinates, not that product.
 return {'p':p,'A':C.a2,'r':r,'target':R,'base':B,'S3':records,'retained_edwards_pair_checks':len(signset(C,B))**2,'retained_system':{'auxiliary_variables':['t=x1*x2','w=y1*y2','h=t*w'],'equations':['t-x1*x2','w-y1*y2','h-t*w','xr*(1+d*h)-x1*y2-y1*x2','yr*(1-d*h)-w-t'],'max_degree_for_fixed_target':2,'caveat':'curve/base constraints also required; no solver runtime measured'}}

def ell2(C,t,Z):
 p=C.p;tv=Z*t*t%p
 if tv==p-1:tv=0
 x1=-C.a2*pow(1+tv,-1,p)%p;g=C.rhs(x1);square=pow(g,(p-1)//2,p) in [0,1]
 x=x1 if square else (-x1-C.a2)%p
 gy=g if square else tv*g%p
 y=next(y for y in range(p) if y*y%p==gy)
 if y%2!=int(square):y=-y%p
 P=(x,y);assert C.contains(P);return P

def lifting(A,H=10000):
 pts=[]
 for u in range(-H,H+1):
  v2=u**3+A*u*u+u
  if v2>=0 and isqrt(v2)**2==v2:
   v=isqrt(v2);pts.append([u,v])
   if v:pts.append([u,-v])
 return {'A':A,'integer_u_bound':H,'integer_points':pts,'count':len(pts),'scope':'fixed rational model, integer coordinates only; no rational-denominator or alternative-lift census'}

def real_checks():
 p=2**255-19;r=2**252+27742317777372353535851937790883648493;A=486662;C=Curve(p,A,1)
 G=(9,14781619447589544791020593568409986887264606134616475288964881837755586237401);T=(0,0);Cp=Curve(p,-2*A,A*A-4)
 assert C.contains(G) and C.mul(r,G) is None
 c=pow((-A-2)%p,(p+3)//8,p)
 if c*c%p!=(-A-2)%p:c=c*pow(2,(p-1)//4,p)%p
 assert c*c%p==(-A-2)%p
 d=-(A-2)*pow(A+2,-1,p)%p
 count=2
 for i in range(1,33):
  P=C.mul(i,G);Q=C.mul(i+7,G);u,v=P;Pt=C.add(P,T)
  assert Pt==(pow(u,-1,p),-v*pow(u*u,-1,p)%p)
  assert Cp.contains(iso(C,P))
  assert iso(C,C.add(P,Q))==Cp.add(iso(C,P),iso(C,Q))
  x=c*u*pow(v,-1,p)%p;y=(u-1)*pow(u+1,-1,p)%p
  assert (-x*x+y*y-1-d*x*x*y*y)%p==0
  assert (1+y)*pow(1-y,-1,p)%p==u
  assert c*u*pow(x,-1,p)%p==v
  assert C.mul(r,Pt)==T
  count+=7
 return {'curve':C.record(r,G),'checks':count,'samples':32,'status':'passed','isogeny_target':Cp.record(r,iso(C,G)),'d':d}

def main():
 allrows=[];symbols=[];encodings=[];controls=[];selections=[]
 for p in [101,229,461,929,1861,3733]:
  selected=select_curves(p);selections.append({'p':p,'selected_coefficients':[a for *_,a in selected]})
  for C,r,G,A in selected:
   rec,H,bases=census(C,r,G,A);allrows.append(rec)
   if len(symbols)<6:symbols.append(symbolic_diagnostics(C,r,G,bases['u'][:4]))
   Z=next(z for z in range(2,p) if pow(z,(p-1)//2,p)==p-1)
   images=[C.mul(8,ell2(C,t,Z)) for t in range(p)]
   assert set(images)<=set(H)
   encodings.append({'p':p,'A':A,'r':r,'Z':Z,'distinct_projected_images':len(set(images)),'parameter_count':p,'sample_nonhomomorphism':next(([a,b] for a in range(8) for b in range(8) if C.add(images[a],images[b])!=images[(a+b)%p]),None)})
  control=prime_control(p)
  if control:
   C,r,G=control;rec,_,_=census(C,r,G);rec['control_kind']='same_field_different_subgroup_order';controls.append(rec)
  if selected:
   target_r=selected[0][1];q=int(S.nextprime(target_r-1))
   for trial in range(50):
    control=prime_control(q)
    if control:
     C,r,G=control;rec,_,_=census(C,r,G);rec['control_kind']='near_subgroup_order_different_field';rec['matched_to_r']=target_r;controls.append(rec);break
    q=int(S.nextprime(q))
 lifts=[lifting(A) for A in sorted({rec['curve']['curve']['a2'] for rec in allrows}|{486662})]
 result={'scope':'CPU exact finite-set diagnostics; no timings or speedup claims','platform':platform.platform(),'python':platform.python_version(),'sympy':S.__version__,'selections':selections,'instances':allrows,'controls':controls,'symbolic':symbols,'encodings':encodings,'integer_lifts':lifts,'real_curve_checks':real_checks()}
 (OUT/'results.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps({'instances':len(allrows),'controls':len(controls),'symbolic_cases':len(symbols),'ell2_cases':len(encodings),'status':'all assertions passed'}))
 for rec in allrows:print(rec['curve']['field']['p'],rec['curve']['curve']['a2'],rec['r'],[(x['policy'],x['covered_nonidentity']) for x in rec['rows']])
if __name__=='__main__':main()
