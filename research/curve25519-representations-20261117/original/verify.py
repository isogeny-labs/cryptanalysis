"""Independent x-only scalar path and artifact integrity checks."""
from research import *

def ladder(C,n,u):
 p=C.p;x1=u;x2,z2,x3,z3,swap=1,0,u,1,0;a24=(C.a2-2)*pow(4,-1,p)%p
 for t in range(max(1,n.bit_length())-1,-1,-1):
  k=(n>>t)&1;swap^=k
  if swap:x2,x3,z2,z3=x3,x2,z3,z2
  swap=k
  a=(x2+z2)%p;aa=a*a%p;b=(x2-z2)%p;bb=b*b%p;e=(aa-bb)%p
  c=(x3+z3)%p;d=(x3-z3)%p;da=d*a%p;cb=c*b%p
  x3=(da+cb)**2%p;z3=x1*(da-cb)**2%p;x2=aa*bb%p;z2=e*(aa+a24*e)%p
 if swap:x2,x3,z2,z3=x3,x2,z3,z2
 return None if z2==0 else x2*pow(z2,-1,p)%p

def main():
 data=json.loads((OUT/'results.json').read_text());f=json.loads((OUT/'followup-results.json').read_text());checks=0
 for rec in data['instances']:
  c=rec['curve']['curve'];C=Curve(rec['curve']['field']['p'],c['a2'],c['a4'],c['a6']);G=tuple(c['G']);r=c['r']
  for i in range(r+1):
   P=C.mul(i,G);assert ladder(C,i,G[0])==(None if P is None else P[0]);checks+=1
  u=dict((r['policy'],r['base']) for r in rec['rows'])['u']
  # Direct cubic membership is checked independently for every recorded base point.
  for P in u:assert (P[1]**2-P[0]**3-C.a2*P[0]**2-P[0])%C.p==0;checks+=1
 real=data['real_curve_checks']['curve'];c=real['curve'];C=Curve(real['field']['p'],c['a2'],c['a4']);G=tuple(c['G'])
 for i in list(range(1,33))+[c['r']]:
  P=C.mul(i,G);assert ladder(C,i,G[0])==(None if P is None else P[0]);checks+=1
 initial=json.loads((OUT/'preliminary.json').read_text())
 for rec in f['field_factors']:
  prior=next(x for x in initial['field_factors'] if x['name']==rec['name'])
  assert rec['smooth_part']==prior['smooth_part'] and rec['remaining_cofactor']==prior['remaining_cofactor'];checks+=1
 assert all(x['IC']['status']=='verified' and x['rho_reference']['status']=='verified' for x in f['end_to_end_correctness'])
 out={'status':'passed','independent_ladder_and_artifact_checks':checks,'path':'Montgomery differential ladder vs affine group scalar multiplication; not independent-host replay','no_benchmark':True}
 (OUT/'verification.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
if __name__=='__main__':main()
