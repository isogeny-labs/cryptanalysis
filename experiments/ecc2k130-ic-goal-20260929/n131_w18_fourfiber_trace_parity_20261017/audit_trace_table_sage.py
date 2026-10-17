#!/usr/bin/env sage -python
"""Replay all terminal selector trace bits with independent Sage arithmetic."""
import hashlib
import json
from collections import Counter
from pathlib import Path

from sage.all import GF, PolynomialRing

HERE=Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    pool_path=HERE/'pool.json'
    pool=json.loads(pool_path.read_text())
    protocol_path=HERE/'protocol.json'
    protocol=json.loads(protocol_path.read_text())
    preflight=json.loads((HERE/'trace_audit_result.json').read_text())
    assert preflight['status']=='PASS_FOURFIBER_TRACE_PARITY_PREFLIGHT'
    ring=PolynomialRing(GF(2),'t');t=ring.gen()
    field=GF(2**131,name='t',modulus=t**131+t**13+t**2+t+1)
    def dec(value):
        return field(ring([(int(value)>>i)&1 for i in range(131)]))
    def trace(point):
        assert point is not None and point[0]!=0
        return int((1/dec(point[0])).trace())
    left={row['state_id']:trace(row['rotated_raw_point']) for row in pool['left_states']}
    right={row['state_id']:trace(row['rotated_raw_point']) for row in pool['right_states']}
    assert len(left)==len(right)==48
    signatures=Counter()
    for joint in pool['joint_states']:
        bit=left[joint['left_state_id']] ^ right[joint['right_state_id']]
        assert bit==trace(joint['raw_sum'])
        signatures[bit]+=1
    assert sum(signatures.values())==2080
    raw=[trace(point) for point in protocol['raw_preimages']]
    assert raw==preflight['panels'][0]['raw_target_trace_bits']
    result={'status':'PASS_INDEPENDENT_N131_TERMINAL_TRACE_TABLE',
            'left_states_checked':48,'right_states_checked':48,
            'joint_states_checked':2080,'joint_trace_counts':dict(signatures),
            'public_raw_target_trace_bits':raw,
            'sha256':{'script':sha(Path(__file__)),'pool':sha(pool_path),
                      'protocol':sha(protocol_path),
                      'preflight':sha(HERE/'trace_audit_result.json')}}
    (HERE/'trace_table_audit_result.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(result['status'],flush=True)


if __name__=='__main__':
    main()
