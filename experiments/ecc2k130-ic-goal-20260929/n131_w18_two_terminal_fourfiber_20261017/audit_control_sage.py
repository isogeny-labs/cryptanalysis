#!/usr/bin/env sage -python
"""Independent checked-Sage replay of four-fiber source and constructed rows."""
import hashlib
import json
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
PRIOR=ROOT/'n131_w18_two_terminal_bilinear_20261015'
R=680564733841876926932320129493409985129


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    protocol_path=HERE/'protocol.json';control_path=HERE/'control_result.json'
    protocol=json.loads(protocol_path.read_text())
    control=json.loads(control_path.read_text())
    pool=json.loads((HERE/'pool.json').read_text())
    n41=json.loads((HERE/'n41_control_result.json').read_text())
    runtime=json.loads((HERE/'sage_runtime_info.json').read_text())
    prior=json.loads((PRIOR/'sage_audit_result.json').read_text())
    assert runtime['status']=='verified'
    assert n41['status']=='PASS_UNPINNED_N41_FOURFIBER_SELECTOR_CONTROL'
    assert prior['status']=='PASS_INDEPENDENT_SAGE_BILINEAR_TWO_TERMINAL_FIBERS'
    assert prior['replayed_control_and_public_residuals']==4160
    assert prior['sha256']['pool']==sha(HERE/'pool.json')
    assert protocol['source_sha256']['terminal']==sha(HERE/'terminal.py')
    assert protocol['source_sha256']['batch']==sha(HERE/'batch.py')
    assert control['protocol_sha256']==sha(protocol_path)
    assert control['status']=='PASS_EXACT_N131_FOURFIBER_TWO_TERMINAL_CONTROL'
    assert control['assignment_check']=={'clauses':control['formula']['clauses'],
                                         'native_xor_rows':control['formula']['native_xor_rows']}
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
    public=point(protocol['public_target'])
    public_raw=[point(row) for row in protocol['raw_preimages']]
    assert len(set(public_raw))==4
    assert all(4*p==public and R*public==curve(0) for p in public_raw)
    raw_control=[point(row) for row in control['control_raw_targets']]
    assert len(set(raw_control))==4
    assert all(4*p==4*raw_control[0] for p in raw_control)
    assert xy(raw_control[0])==control['control_raw_target']
    assert len(pool['joint_states'])==2080
    assert len(control['residuals'])==4*2080
    exceptional=0
    for raw_index,target in enumerate(raw_control):
        rows=control['residuals'][raw_index*2080:(raw_index+1)*2080]
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
    assert exceptional==control['exceptional_raw_joint_choices']==0
    receipt={'status':'PASS_INDEPENDENT_SAGE_N131_FOURFIBER_CONTROL',
             'curve_id':protocol['curve_id'],'raw_public_preimages':4,
             'constructed_preimages':4,'residual_rows_checked':len(control['residuals']),
             'exceptional_residuals':exceptional,
             'assignment_check':control['assignment_check'],
             'source_sha256':{'script':sha(Path(__file__)),
                              'protocol':sha(protocol_path),'control':sha(control_path),
                              'pool':sha(HERE/'pool.json'),
                              'prior_sage_audit':sha(PRIOR/'sage_audit_result.json'),
                              'n41_control':sha(HERE/'n41_control_result.json'),
                              'runtime':sha(HERE/'sage_runtime_info.json')}}
    (HERE/'control_sage_audit_result.json').write_text(json.dumps(receipt,sort_keys=True,indent=2)+'\n')
    print(receipt['status'],len(control['residuals']),flush=True)


if __name__=='__main__':
    main()
