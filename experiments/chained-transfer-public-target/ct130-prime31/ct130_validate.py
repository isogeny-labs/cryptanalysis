#!/usr/bin/env python3
"""Independent arithmetic and report auditor (does not import the producer)."""
import json,math,statistics as stats,sys
P=(1<<31)-1;A=829286810;B=1720850223;Q=1073779747;N=2*Q
G=(340312345,363681553)

def add(Pt,Qt,a=A,b=B):
 if Pt is None:return Qt
 if Qt is None:return Pt
 x,y=Pt;u,v=Qt
 if x==u and (y+v)%P==0:return None
 if x!=u: slope=(v-y)*pow(u-x,-1,P)%P
 else:slope=(3*x*x+2*a*x+b)*pow(2*y,-1,P)%P
 w=(slope*slope-a-x-u)%P
 return(w,(slope*(x-w)-y)%P)
def mul(T,k,a=A,b=B):
 S=None
 while k:
  if k%2:S=add(S,T,a,b)
  T=add(T,T,a,b);k//=2
 return S

def prime(n):
 if n<2:return False
 for d in range(2,math.isqrt(n)+1):
  if n%d==0:return False
 return True

def iso(T):
 if T is None or T==(0,0):return None
 x,y=T;z=pow(x,-1,P)
 return ((x+A+B*z)%P, y*(1-B*z*z)%P)

def audit():
 if not (prime(P) and prime(Q)): raise ValueError("CT130 ct130_validate.py check at line 35")
 if not (B%P and (A*A-4*B)%P): raise ValueError("CT130 ct130_validate.py check at line 36")
 if not (abs(N-(P+1))<=math.isqrt(4*P)): raise ValueError("CT130 ct130_validate.py check at line 37")
 if not (mul(G,Q) is None and G is not None): raise ValueError("CT130 ct130_validate.py check at line 38")
 # Rational 2-torsion (0,0) plus odd prime-order G forces #E multiple 2Q.
 # Hasse interval width <2Q: it determines #E exactly.
 if not (2*math.isqrt(4*P)<2*Q): raise ValueError("CT130 ct130_validate.py check at line 41")
 at=(-2*A)%P;bt=(A*A-4*B)%P
 if not ((at,bt)==(488910027,790354208)): raise ValueError("CT130 ct130_validate.py check at line 43")
 if not (iso((0,0)) is None): raise ValueError("CT130 ct130_validate.py check at line 44")
 H=iso(G)
 if not (H is not None and mul(H,Q,at,bt) is None): raise ValueError("CT130 ct130_validate.py check at line 46")
 for k in (1,2,17,12345,456789,Q-1):
  T=mul(G,k);U=iso(T)
  if not (U is None or (U[1]*U[1]-(U[0]**3+at*U[0]**2+bt*U[0]))%P==0): raise ValueError("CT130 ct130_validate.py check at line 49")
  if not (U==mul(H,k,at,bt)): raise ValueError("CT130 ct130_validate.py check at line 50")
 per_run=[];per_scalar=[]
 for idx,p in enumerate(sys.argv[1:4],1):
  data=json.load(open(p));assert data['source_prime']==P and data['subgroup_prime']==Q
  if not (data['curve_order']==N and data['source_generator']==list(G)): raise ValueError("CT130 ct130_validate.py check at line 54")
  ratios=[]
  for row,k in zip(data['rows'],(17,12345,456789)):
   if not (row['fixture_scalar']==k): raise ValueError("CT130 ct130_validate.py check at line 57")
   if not (row['source_public']==list(mul(G,k))): raise ValueError("CT130 ct130_validate.py check at line 58")
   if not (row['target_public']==list(mul(H,k,at,bt))): raise ValueError("CT130 ct130_validate.py check at line 59")
   if not (len(row['blocks'])==4): raise ValueError("CT130 ct130_validate.py check at line 60")
   for j,b in enumerate(row['blocks']):
    expected=['source','target','target','source'] if j%2==0 else ['target','source','source','target']
    if not (b['order']==expected): raise ValueError("CT130 ct130_validate.py check at line 63")
    samples=b['observations'];assert [x['arm'] for x in samples]==expected
    if not (all(x['ns']>0 and x['baby_entries']==math.isqrt(Q-1)+1 for x in samples)): raise ValueError("CT130 ct130_validate.py check at line 65")
    if not (all(x['field_inversions']<=x['group_add_calls'] for x in samples)): raise ValueError("CT130 ct130_validate.py check at line 66")
    s=stats.mean(x['ns'] for x in samples if x['arm']=='source')
    t=stats.mean(x['ns'] for x in samples if x['arm']=='target')
    ratios.append(s/t)
    per_scalar.append((k,s,t))
  per_run.append(stats.median(ratios))
 rho=json.load(open(sys.argv[4]))
 if not (len(rho)==6): raise ValueError("CT130 ct130_validate.py check at line 73")
 for row in rho:
  if not (row['scalar'] in (17,12345,456789)): raise ValueError("CT130 ct130_validate.py check at line 75")
  if not (row['arm'] in ('source-rho','transfer-rho')): raise ValueError("CT130 ct130_validate.py check at line 76")
  if not (len(row['elapsed_ns'])==len(row['walk_steps'])==len(row['stored_distinguished'])==2): raise ValueError("CT130 ct130_validate.py check at line 77")
  if not (all(x>0 for x in row['walk_steps']+row['elapsed_ns'])): raise ValueError("CT130 ct130_validate.py check at line 78")
 print(json.dumps({'arithmetical_checks':'pass','hasse_order_proof':'#E(Fp)=2q (prime q, rational 2-torsion, Hasse interval)',
  'verified_public_scalars':[1,2,17,12345,456789,Q-1],
  'run_median_source_over_transferred_bsgs':per_run,
  'overall_bsgs_source_median_ms':stats.median(s/1e6 for _,s,_ in per_scalar),
  'overall_bsgs_transferred_median_ms':stats.median(t/1e6 for _,_,t in per_scalar),
  'rho_source_median_ms':stats.median(v/1e6 for r in rho if r['arm']=='source-rho' for v in r['elapsed_ns']),
  'rho_transferred_median_ms':stats.median(v/1e6 for r in rho if r['arm']=='transfer-rho' for v in r['elapsed_ns']),
  'standing':'producer-only, exploratory, nonpreregistered, no PCC signature'},sort_keys=True,indent=2))
if __name__=='__main__':audit()
