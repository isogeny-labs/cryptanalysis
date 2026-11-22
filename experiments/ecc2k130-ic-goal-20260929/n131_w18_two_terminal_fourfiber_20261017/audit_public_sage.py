#!/usr/bin/env sage -python
"""Independent checked-Sage replay of all four public terminal fibers."""
import hashlib
import json
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE=Path(__file__).resolve().parent
R=680564733841876926932320129493409985129


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    protocol_path=HERE/'protocol.json';query_path=HERE/'query_result.json'
    protocol=json.loads(protocol_path.read_text())
    query=json.loads(query_path.read_text())
    pool=json.loads((HERE/'pool.json').read_text())
    control_audit=json.loads((HERE/'control_sage_audit_result.json').read_text())
    runtime=json.loads((HERE/'sage_runtime_info.json').read_text())
    assert runtime['status']=='verified'
    assert control_audit['status']=='PASS_INDEPENDENT_SAGE_N131_FOURFIBER_CONTROL'
    assert query['protocol_sha256']==sha(protocol_path)
    assert query['public_target']==protocol['public_target']
    assert query['raw_targets']==protocol['raw_preimages']
    assert protocol['source_sha256']['pool']==sha(HERE/'pool.json')
    ring=PolynomialRing(GF(2),'t');t=ring.gen()
    field=GF(2**131,name='t',modulus=t**131+t**13+t**2+t+1)
    curve=EllipticCurve(field,[1,0,0,0,1])
    def dec(value):
        return field(ring([(int(value)>>i)&1 for i in range(131)]))
    def enc(value):
        return sum(int(bit)<<i for i,bit in enumerate(value.polynomial().list()))
    def point(row):
        return curve(0) if row is None else curve([dec(v) for v in row])
    def xy(p):
        return None if p==curve(0) else [enc(p[0]),enc(p[1])]
    public=point(query['public_target'])
    raw_targets=[point(row) for row in query['raw_targets']]
    assert len(raw_targets)==4 and len(set(raw_targets))==4
    assert all(4*p==public for p in raw_targets)
    assert R*public==curve(0)
    assert len(pool['joint_states'])==2080
    assert len(query['residuals'])==4*2080
    exceptional=0
    for raw_index,target in enumerate(raw_targets):
        rows=query['residuals'][raw_index*2080:(raw_index+1)*2080]
        for joint,recorded in zip(pool['joint_states'],rows):
            assert recorded['raw_preimage_index']==raw_index
            assert (recorded['left_state_id'],recorded['right_state_id'])==(
                joint['left_state_id'],joint['right_state_id'])
            actual=target-point(joint['raw_sum'])
            assert xy(actual)==recorded['point']
            if actual==curve(0) or actual[0] in (0,1):
                assert recorded['standard_reciprocal'] is None
                exceptional+=1
            else:
                assert enc(1/actual[0])==recorded['standard_reciprocal']
    assert exceptional==query['exceptional_raw_joint_choices']
    result={'status':'PASS_INDEPENDENT_SAGE_N131_FOURFIBER_PUBLIC_RESIDUALS',
            'curve_id':query['curve_id'],'workload_id':query['workload_id'],
            'raw_preimages_checked':4,'residual_rows_checked':len(query['residuals']),
            'exceptional_residuals':exceptional,
            'source_sha256':{'script':sha(Path(__file__)),
                             'protocol':sha(protocol_path),'query':sha(query_path),
                             'pool':sha(HERE/'pool.json'),
                             'control_sage_audit':sha(HERE/'control_sage_audit_result.json'),
                             'runtime':sha(HERE/'sage_runtime_info.json')}}
    (HERE/'public_sage_audit_result.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(result['status'],len(query['residuals']),flush=True)


if __name__=='__main__':
    main()
