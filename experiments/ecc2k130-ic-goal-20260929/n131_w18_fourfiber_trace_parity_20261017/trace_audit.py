#!/usr/bin/env sage -python
"""Independent field-trace preflight for the nine-output parity gate."""
import hashlib
import json
from collections import Counter
from pathlib import Path

from sage.all import GF, PolynomialRing

HERE = Path(__file__).resolve().parent
PRIOR = HERE.parent / 'n131_w18_two_terminal_fourfiber_20261017'
BASE = HERE.parent / 'n131_fixed_seed_ninepair_cubic_20261011'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def field(degree, exponents):
    ring = PolynomialRing(GF(2), 't')
    t = ring.gen()
    modulus = sum(t**i for i in exponents)
    return ring, GF(2**degree, name='t', modulus=modulus)


def decode(ring, extension, value, degree):
    return extension(ring([(int(value) >> i) & 1 for i in range(degree)]))


def point_trace(ring, extension, point, degree):
    assert point is not None and point[0] != 0
    return int((1/decode(ring, extension, point[0], degree)).trace())


def main():
    runtime = json.loads((HERE/'sage_runtime_info.json').read_text())
    assert runtime['status'] == 'verified'
    prior_audit = json.loads((PRIOR/'audit_result.json').read_text())
    assert prior_audit['status'] == 'PASS_FOURFIBER_N131_PUBLIC_QUERY_AUDIT'
    public = json.loads((PRIOR/'query_result.json').read_text())
    constructed = json.loads((PRIOR/'control_result.json').read_text())
    source = json.loads((HERE/'pool.json').read_text())
    r131, f131 = field(131, (131,13,2,1,0))
    joint_trace = {
        (item['left_state_id'], item['right_state_id']):
        point_trace(r131,f131,item['raw_sum'],131)
        for item in source['joint_states']}
    assert len(joint_trace) == 2080
    panels = []
    for label, record, target_key in (
        ('public',public,'raw_targets'),
        ('constructed',constructed,'control_raw_targets')):
        targets = record[target_key]
        raw_trace = [point_trace(r131,f131,point,131) for point in targets]
        counts = Counter()
        for row in record['residuals']:
            key = row['left_state_id'],row['right_state_id']
            index = row['raw_preimage_index']
            expected = raw_trace[index] ^ joint_trace[key]
            actual = int(decode(r131,f131,row['standard_reciprocal'],131).trace())
            assert expected == actual
            counts[f'fiber{index}_trace{actual}'] += 1
        assert len(record['residuals']) == 8320
        panels.append({'label':label,'raw_target_trace_bits':raw_trace,
                       'counts':dict(sorted(counts.items())),
                       'rows_checked':len(record['residuals'])})
    fixture = json.loads((BASE/'control_fixture.json').read_text())
    control = constructed['control_choice_indices']
    chosen = next(row for row in constructed['residuals']
                  if row['raw_preimage_index']==0 and
                     (row['left_state_id'],row['right_state_id'])==tuple(control))
    free_trace = 0
    for shifted in fixture['pair_rotated_z'][:7]:
        z = decode(r131,f131,shifted,131)
        free_trace ^= int((z/(z+1)).trace())
    assert free_trace == int(decode(r131,f131,chosen['standard_reciprocal'],131).trace()) == 1
    r41,f41 = field(41,(41,3,0))
    n41 = json.loads((HERE/'n41_control_result.json').read_text())
    assert n41['status']=='PASS_UNPINNED_N41_FOURFIBER_SELECTOR_CONTROL'
    n41_free = point_trace(r41,f41,n41['free_five_sum'],41)
    n41_terminal = point_trace(r41,f41,n41['terminal_two_sum'],41)
    n41_target = point_trace(r41,f41,n41['raw_fibers'][0]['raw_target'],41)
    assert n41_free ^ n41_terminal ^ n41_target == 0
    receipt = {'status':'PASS_FOURFIBER_TRACE_PARITY_PREFLIGHT',
               'curve_id':public['curve_id'],'workload_id':public['workload_id'],
               'public_rows_checked':8320,'constructed_rows_checked':8320,
               'panels':panels,'constructed_free_seven_trace':free_trace,
               'n41_trace_bits':{'free_five':n41_free,'terminal_two':n41_terminal,
                                 'raw_target':n41_target},
               'source_sha256':{'script':sha(Path(__file__)),
                                'prior_audit':sha(PRIOR/'audit_result.json'),
                                'public':sha(PRIOR/'query_result.json'),
                                'constructed':sha(PRIOR/'control_result.json'),
                                'pool':sha(HERE/'pool.json'),
                                'n41_control':sha(HERE/'n41_control_result.json'),
                                'runtime':sha(HERE/'sage_runtime_info.json')}}
    (HERE/'trace_audit_result.json').write_text(json.dumps(receipt,sort_keys=True,indent=2)+'\n')
    print(receipt['status'],flush=True)


if __name__ == '__main__':
    main()
