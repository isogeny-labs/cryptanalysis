"""Derive the intermediate reciprocal from the archived checked N41 witness."""
import hashlib,json
from pathlib import Path
from sage.all import EllipticCurve,GF,PolynomialRing

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
p=json.loads((HERE/'witness_protocol.json').read_text())
for path,digest in p['sources'].items():assert sha(path)==digest,path
source=json.loads(Path(p['states']).read_text())
fixture=json.loads(Path(p['fixture']).read_text())
R=PolynomialRing(GF(2),'u');u=R.gen()
F=GF(2**41,name='u',modulus=u**41+u**3+1)
E=EllipticCurve(F,[1,0,0,0,1])
dec=lambda x:F(R([(int(x)>>i)&1 for i in range(41)]))
enc=lambda x:sum(int(c)<<i for i,c in enumerate(x.polynomial().list()))
points=[E(dec(source['states'][slot][sid]['point'][0]),
          dec(source['states'][slot][sid]['point'][1]))
        for slot,sid in enumerate(fixture['state_ids'])]
raw=E(dec(source['target_raw_point'][0]),dec(source['target_raw_point'][1]))
public=E(raw[0]**(1<<6),raw[1]**(1<<6))
left=sum(points[:3],E(0));intermediate=left+points[3]
assert intermediate and intermediate[0] and left and left[0] and public and public[0]
assert intermediate+points[4]==public
assert enc(1/left[0])==fixture['left_reciprocal']
assert enc(1/public[0])==fixture['public_reciprocal']
out={'status':'PASS_INTERMEDIATE_WITNESS','intermediate_reciprocal':enc(1/intermediate[0]),
     'intermediate_point':[enc(intermediate[0]),enc(intermediate[1])],
     'source_sha256':sha(p['states']),'fixture_sha256':sha(p['fixture']),
     'protocol_sha256':sha(HERE/'witness_protocol.json')}
(HERE/'witness.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
print(json.dumps(out,sort_keys=True))
