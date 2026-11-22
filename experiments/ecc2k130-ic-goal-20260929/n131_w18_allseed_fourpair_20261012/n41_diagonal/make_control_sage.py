"""Derive exact all-seed four-pair reciprocal chart from the public hit."""
import hashlib,json
from pathlib import Path
from sage.all import EllipticCurve,GF,PolynomialRing
h=Path(__file__).resolve().parent
p=json.loads((h/'control_protocol.json').read_text())
def sha(q):return hashlib.sha256(q.read_bytes()).hexdigest()
assert p['sha256']=={'source':sha(Path(__file__)),'audit':sha(h/'audit_result.json'),
                     'runtime':sha(h/'audit_sage_runtime_info.json')}
a=json.loads((h/'audit_result.json').read_text())
ring=PolynomialRing(GF(2),'t');t=ring.gen();F=GF(2**41,name='t',modulus=t**41+t**3+1)
E=EllipticCurve(F,[1,0,0,0,1])
def dec(n):return F(ring([(int(n)>>i)&1 for i in range(41)]))
def enc(v):return sum(int(bit)<<i for i,bit in enumerate(v.polynomial().list()))
Ps=[E(*map(dec,z['point'])) for z in a['pairs']]
node0=Ps[0]+Ps[1];node1=Ps[2]+Ps[3];total=node0+node1
assert [enc(total[0]),enc(total[1])]==a['raw_sum']
assert all(P!=E(0) and P[0]!=0 for P in Ps+[node0,node1,total])
result={'status':'PASS_N41_DIAGONAL_ALLSEED_FOURPAIR_RECIPROCAL_CHART',
        'curve_id':a['curve_id'],'public_target':a['public_target'],
        'raw_target':a['raw_sum'],'raw_preimage_index':a['raw_preimage_index'],
        'masks':[z['masks'] for z in a['pairs']],
        'sign_bits':[z['sign_bits'] for z in a['pairs']],
        'rotations':[z['rotation'] for z in a['pairs']],
        'pair_reciprocals':[enc(1/P[0]) for P in Ps],
        'intermediate_reciprocals':[enc(1/node0[0]),enc(1/node1[0])],
        'target_reciprocal':enc(1/total[0]),
        'source_audit_sha256':sha(h/'audit_result.json')}
(h/'control_fixture.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
print(result['status'])
