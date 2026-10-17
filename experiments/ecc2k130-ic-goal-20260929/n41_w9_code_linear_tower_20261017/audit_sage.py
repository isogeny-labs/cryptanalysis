"""Independently replay the final-pair resultant over the exact N41 source."""
import hashlib,json,random,time
from pathlib import Path
from sage.all import EllipticCurve,GF,PolynomialRing

HERE=Path(__file__).resolve().parent
sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
p=json.loads((HERE/'audit_protocol.json').read_text())
for path,digest in p['sources'].items():assert sha(path)==digest,path
source=json.loads(Path(p['states']).read_text())
fixture=json.loads(Path(p['fixture']).read_text())
witness=json.loads((HERE/'witness.json').read_text())
R=PolynomialRing(GF(2),'u');u=R.gen()
F=GF(2**41,name='u',modulus=u**41+u**3+1)
E=EllipticCurve(F,[1,0,0,0,1])
dec=lambda x:F(R([(int(x)>>i)&1 for i in range(41)]))
enc=lambda x:sum(int(c)<<i for i,c in enumerate(x.polynomial().list()))
fro=lambda x,k:x**(1<<k)
s=dec(source['seed']<<1)
h=sum((s**(1<<(2*j)) for j in range(21)),F(0))**2
H=fro(h,24);C=F(1)+H;t=dec(fixture['public_reciprocal'])
assert C and H
rows=[]
for ordinal in range(71):
    states=source['states'][4][4*ordinal:4*ordinal+4]
    mask=states[0]['masks'][0]
    w=dec(mask<<1);prod=fro(w*(w+s),24)
    roots=sorted({enc(1/dec(state['point'][0])) for state in states})
    assert len(roots)==2
    for root in roots:assert C*dec(root)**2+prod*dec(root)+H==0
    assert C*(dec(roots[0])+dec(roots[1]))==prod
    assert C*dec(roots[0])*dec(roots[1])==H
    rows.append((prod,roots))

random_words=random.Random(p['random_seed'])
charts=[0,enc(t),witness['intermediate_reciprocal']]
charts.extend(random_words.randrange(1<<41) for _ in range(p['random_chart_count']))
comparisons=0,0,0
start=time.monotonic();identity_checks=0;common_root_checks=0;zero_resultants=0
for word in charts:
    v=dec(word);A=F(1)+(t*v)**2;B=t*v;D=t**2+v**2
    for product,roots in rows:
        M=A*H+C*D;L=A*product+C*B;N=B*H+product*D
        resultant=M**2+L*N
        g=[A*dec(root)**2+B*dec(root)+D for root in roots]
        assert resultant==C**2*g[0]*g[1]
        assert (resultant==0)==(g[0]==0 or g[1]==0)
        identity_checks+=1;common_root_checks+=1;zero_resultants+=int(resultant==0)
assert identity_checks==len(charts)*71
positive_ordinal=fixture['state_ids'][4]//4
assert positive_ordinal==27
positive_product,positive_roots=rows[positive_ordinal]
v=dec(witness['intermediate_reciprocal'])
A=F(1)+(t*v)**2;B=t*v;D=t**2+v**2
assert any(A*dec(root)**2+B*dec(root)+D==0 for root in positive_roots)
out={'status':'PASS_RESULTANT_SOURCE_EQUIVALENCE','curve_id':source['curve_id'],
     'source_codes':len(rows),'charts':len(charts),'identity_checks':identity_checks,
     'common_root_checks':common_root_checks,'zero_resultants':zero_resultants,
     'positive_code_ordinal':positive_ordinal,
     'positive_chart_reciprocal':witness['intermediate_reciprocal'],
     'elapsed_seconds':time.monotonic()-start,
     'protocol_sha256':sha(HERE/'audit_protocol.json')}
(HERE/'audit_result.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
print(json.dumps(out,sort_keys=True))
