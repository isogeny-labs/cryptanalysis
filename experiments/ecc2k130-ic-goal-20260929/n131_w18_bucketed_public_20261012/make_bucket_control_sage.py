"""Derive exact reciprocal circuit inputs from the independently checked row."""
import hashlib,json
from pathlib import Path
from sage.all import EllipticCurve,GF,PolynomialRing

HERE=Path(__file__).resolve().parent
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def main():
    p=json.loads((HERE/'bucket_control_protocol.json').read_text())
    paths={'source':HERE/'make_bucket_control_sage.py','audit':HERE/'bucket_audit_result.json',
           'plan':HERE/'bucket_plan.json','runtime':HERE/'sage_runtime_info.json'}
    assert {k:sha(v) for k,v in paths.items()}==p['sha256']
    audit=json.loads(paths['audit'].read_text());plan=json.loads(paths['plan'].read_text())
    assert audit['status']=='PASS_INDEPENDENT_N41_BUCKET_905_PUBLIC_RELATION'
    assert plan['plan'][0]['low6_masks']==[9,14]
    ring=PolynomialRing(GF(2),'t');t=ring.gen();F=GF(2**41,name='t',modulus=t**41+t**3+1)
    E=EllipticCurve(F,[1,0,0,0,1])
    def dec(n):return F(ring([(int(n)>>i)&1 for i in range(41)]))
    def enc(v):return sum(int(b)<<i for i,b in enumerate(v.polynomial().list()))
    points=[E(*map(dec,row['point'])) for row in audit['pairs']]
    left=points[0]+points[1];right=points[2]+points[3]
    raw=E(*map(dec,audit['raw_sum']))
    assert left!=E(0) and right!=E(0) and left[0]!=0 and right[0]!=0
    assert left+right==raw
    masks=[list(row['masks']) for row in audit['pairs']]
    masks[0].reverse()
    assert (masks[0][0]&63,masks[0][1]&63)==(9,14)
    pair_c=[enc(1/P[0]) for P in points]
    middle=[enc(1/left[0]),enc(1/right[0])]
    fixture={'status':'PASS_N41_BUCKET_905_POSITIVE_CIRCUIT_FIXTURE',
             'curve_id':audit['curve_id'],'masks':masks,'pair_reciprocals':pair_c,
             'intermediate_reciprocals':middle,
             'target_reciprocal':enc(1/raw[0]),
             'public_target':audit['public_target'],'raw_target':audit['raw_sum'],
             'source_audit_sha256':sha(paths['audit']),
             'protocol_sha256':sha(HERE/'bucket_control_protocol.json')}
    (HERE/'bucket_control_fixture.json').write_text(json.dumps(fixture,sort_keys=True,indent=2)+'\n')
    print(fixture['status'],pair_c,middle,flush=True)
if __name__=='__main__':main()
