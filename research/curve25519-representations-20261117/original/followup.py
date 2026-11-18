from research import *
from functools import reduce

def addrow(piv,row,r,n):
 row=[v%r for v in row]
 for col in sorted(piv):
  t=row[col]
  if t:row=[(a-t*b)%r for a,b in zip(row,piv[col])]
 col=next((i for i in range(n) if row[i]),None)
 if col is None:
  assert row[-1]==0
  return False
 inv=pow(row[col],-1,r);row=[v*inv%r for v in row]
 for j in list(piv):
  t=piv[j][col]
  if t:piv[j]=[(a-t*b)%r for a,b in zip(piv[j],row)]
 piv[col]=row
 return True

def rho(C,r,G,Q):
 rng=random.Random(918273)
 def step(state):
  P,a,b=state;c=0 if P is None else P[0]%3
  if c==0:return C.add(P,G),(a+1)%r,b
  if c==1:return C.add(P,P),2*a%r,2*b%r
  return C.add(P,Q),a,(b+1)%r
 for restart in range(32):
  a,b=rng.randrange(r),rng.randrange(r);slow=(C.add(C.mul(a,G),C.mul(b,Q)),a,b);fast=slow
  for j in range(4*isqrt(r)+32):
   slow=step(slow);fast=step(step(fast))
   if slow[0]==fast[0]:
    den=(fast[2]-slow[2])%r
    if den:
     k=(slow[1]-fast[1])*pow(den,-1,r)%r
     assert C.mul(k,G)==Q
     return {'status':'verified','recovered_k':k,'restarts':restart}
    break
 return {'status':'failed','restarts':32}

def recover(C,r,G,B,Q):
 signed=[]
 for i,P in enumerate(B):signed.extend([(P,i,1),(C.neg(P),i,-1)])
 lookup={P:(i,s) for P,i,s in signed};piv={};rng=random.Random(20261117);hits=0;skips=0
 n=len(B)+1
 for q in range(1,10001):
  a,b=rng.randrange(r),rng.randrange(r);R=C.add(C.mul(a,G),C.mul(b,Q))
  if R is None:skips+=1;continue
  for P,i,s in signed:
   U=C.add(R,C.neg(P))
   if U in lookup:
    j,t=lookup[U];assert C.add(P,U)==R;hits+=1
    row=[0]*(n+1);row[i]+=s;row[j]+=t;row[-2]-=b;row[-1]=a
    addrow(piv,row,r,n)
    break
  if len(piv)==n:
   ans=piv[n-1][-1]
   assert C.mul(ans,G)==Q
   for i,P in enumerate(B):assert C.mul(piv[i][-1],G)==P
   return {'status':'verified','queries':q,'relations':hits,'rank':len(piv),'unknowns':n,'skipped_identity_queries':skips,'recovered_k':ans}
 return {'status':'rank_incomplete','queries':10000,'relations':hits,'rank':len(piv),'unknowns':n,'skipped_identity_queries':skips}

def curve_from(rec):
 d=rec['curve']['curve'];p=rec['curve']['field']['p'];return Curve(p,d['a2'],d['a4'],d['a6']),int(d['r']),tuple(d['G'])

def main():
 data=json.loads((OUT/'results.json').read_text());e2e=[];gb=[];structured=[];cancellations=[]
 for rec in data['instances']:
  C,r,G=curve_from(rec);Q=C.mul(7%r,G);ref=rho(C,r,G,Q)
  assert ref['status']=='verified'
  for row in rec['rows']:
   B=list(map(tuple,row['base']));result=recover(C,r,G,B,Q)
   if result['status']=='verified':assert result['recovered_k']==7%r
   e2e.append({'curve_id':rec['curve']['curve_id'],'p':C.p,'A':C.a2,'r':r,'policy':row['policy'],'target':Q,'rho_reference':ref,'IC':result,'scope':'correctness only; no performance comparison; exhaustive base setup'})
  # Missing affine intermediate O for G + (-G) + [2]G = [2]G.
  P=G;minus=C.neg(P);R=C.mul(2,G)
  assert C.add(C.add(P,minus),R)==R
  assert C.add(P,minus) is None
  cancellations.append({'curve_id':rec['curve']['curve_id'],'witness':[P,minus,R],'target':R,'intermediate':None,'affine_chain_has_this_path':False,'projective_chain_requires_infinity_chart':True})
  H=[C.mul(i,G) for i in range(r)]
  # mu_D roots plus Dickson recurrence C_D(u+1/u)=u^D+u^-D.
  for D in S.divisors(C.p-1):
   D=int(D)
   if D>64:continue
   mu=[u for u in range(1,C.p) if pow(u,D,C.p)==1]
   assert len(mu)==D
   zs=set()
   for u in mu:
    z=(u+pow(u,-1,C.p))%C.p;zs.add(z);a,b=2,z
    if D==1:value=z
    else:
     for n in range(2,D+1):a,b=b,(z*b-a)%C.p
     value=b
    assert value==2
   B=[P for P in H[1:] if pow(P[0],D,C.p)==1]
   repsB=[P for P in B if P<C.neg(P)];sums=pair_sums(C,repsB)
   structured.append({'p':C.p,'A':C.a2,'r':r,'D':D,'coordinate_roots':D,'invariant_roots':len(zs),'subgroup_points':len(B),'sign_classes':len(repsB),'covered_nonidentity':len(set(sums)-{None}),'prime_factors_of_D':{str(k):int(v) for k,v in S.factorint(D).items()}})
 for rec in data['symbolic']:
  x,y=S.symbols('x y');p=rec['p'];C=Curve(p,rec['A'],1);B=list(map(tuple,rec['base']))
  for row in rec['S3']:
   roots=[coord(C,P,row['model']) for P in B]
   F=S.prod(x-a for a in roots);F2=S.prod(y-a for a in roots)
   pol=S.sympify(row['equation']);G=S.groebner([F,F2,pol],x,y,modulus=p,order='grevlex')
   original={(u,v) for u in roots for v in roots if int(pol.subs({x:u,y:v}))%p==0}
   reduced={(u,v) for u in roots for v in roots if all(int(f.as_expr().subs({x:u,y:v}))%p==0 for f in G.polys)}
   assert original==reduced
   gb.append({'p':p,'A':C.a2,'model':row['model'],'basis_polynomials':len(G.polys),'output_max_degree':max(int(f.total_degree()) for f in G.polys),'output_terms':sum(len(f.terms()) for f in G.polys),'exact_root_sets_equal':True,'root_pairs':len(original),'scope':'reference GB correctness; no timing, solving-degree, F4 or cryptographic-size claim'})
 primes={'Curve25519':2**255-19,'P224':2**224-2**96+1,'P256':2**256-2**224+2**192+2**96-1,'P384':2**384-2**128-2**96+2**32-1,'P521':2**521-1};factors=[]
 for name,p in primes.items():
  n=p-1;small={};part=1
  for q in S.primerange(2,100001):
   e=0
   while n%q==0:n//=q;part*=q;e+=1
   if e:small[str(q)]=e
  assert part*n==p-1
  factors.append({'name':name,'p':str(p),'trial_bound':100000,'small_factors':small,'smooth_part':str(part),'remaining_cofactor':str(n),'remaining_cofactor_primality':'not assessed'})
 out={'end_to_end_correctness':e2e,'groebner_correctness':gb,'structured_factor_bases':structured,'cancellation_cases':cancellations,'field_factors':factors}
 (OUT/'followup-results.json').write_text(json.dumps(out,indent=2)+'\n')
 print(json.dumps({'end_to_end':len(e2e),'verified':sum(x['IC']['status']=='verified' for x in e2e),'GB':len(gb),'structured':len(structured),'cancellation':len(cancellations)}))
if __name__=='__main__':main()
