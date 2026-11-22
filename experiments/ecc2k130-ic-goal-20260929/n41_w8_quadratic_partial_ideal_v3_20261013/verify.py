"""Read-only receipt and invariant check for the W8 quadratic-family census."""
import hashlib
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def read(name):
    return json.loads((HERE / name).read_text())

def verify_sources(protocol):
    assert protocol['status'] == 'FROZEN'
    for name, expected in protocol['sources'].items():
        assert sha(Path(name)) == expected, name

for stem in ('n41_w8_quadratic_partial_ideal_20261013',
             'n41_w8_quadratic_partial_ideal_v2_20261013'):
    d = PARENT / stem
    protocol = json.loads((d / 'protocol.json').read_text())
    verify_sources(protocol)
    run = json.loads((d / 'run_result.json').read_text())
    assert run['protocol_sha256'] == sha(d / 'protocol.json')
    assert run['status'] == run['stop_reason'] == 'WALL_CAP'
    assert run['exit_code'] == -15 and run['wall_ns'] >= 120_000_000_000
    for name, digest in run['sha256'].items():
        assert sha(d / name) == digest

protocol = read('protocol.json')
verify_sources(protocol)
run = read('run_result.json')
assert run['status'] == 'EXIT_0' and run['exit_code'] == 0
assert run['stop_reason'] is None and run['wall_ns'] < 120_000_000_000
assert run['protocol_sha256'] == sha(HERE / 'protocol.json')
for name, digest in run['sha256'].items():
    assert sha(HERE / name) == digest
result = read('result.json')
assert result['status'] == 'COMPLETE_W8_QUADRATIC_PARTIAL_IDEAL_CENSUS'
assert result['target_reciprocal'] == 344545435656
cases = result['cases']
assert len(cases) == 196
expected = {(2,'witness'):1,(3,'witness'):1,(4,'witness'):1,(5,'witness'):1,
            (2,'sample'):64,(3,'sample'):64,(4,'sample'):64}
assert Counter((c['free_state_bits_per_slot'],c['kind']) for c in cases) == expected
for c in cases:
    assert c['exact_quadratic_one_hot_ideal'] == (
        c['left_unique_reciprocals'] > 0 and c['right_unique_reciprocals'] > 0
        and c['left_unique_reciprocals'] == c['left_span_rank']
        and c['right_unique_reciprocals'] == c['right_span_rank'])
    assert c['left_span_rank'] <= 40 and c['right_span_rank'] <= 40
    assert c['s3_coordinate_pairs'] >= c['exact_group_hits']
    assert c['root_proposals'] >= c['s3_coordinate_pairs']
    if c['kind'] == 'witness':
        assert c['s3_coordinate_pairs'] == c['exact_group_hits'] == 1
    else:
        assert c['s3_coordinate_pairs'] == c['exact_group_hits'] == 0
assert sum(c['exact_quadratic_one_hot_ideal'] for c in cases if c['kind']=='sample' and c['free_state_bits_per_slot']==2) == 61
assert sum(c['exact_quadratic_one_hot_ideal'] for c in cases if c['kind']=='sample' and c['free_state_bits_per_slot']==3) == 63
assert sum(c['exact_quadratic_one_hot_ideal'] for c in cases if c['kind']=='sample' and c['free_state_bits_per_slot']==4) == 0
assert cases[70]['right_unique_reciprocals'] == 32 and cases[70]['right_span_rank'] == 31

audit_protocol = read('audit_protocol.json')
verify_sources(audit_protocol)
audit_run = read('audit_run_result.json')
assert audit_run['status'] == 'EXIT_0' and audit_run['exit_code'] == 0
assert audit_run['protocol_sha256'] == sha(HERE / 'audit_protocol.json')
for name,digest in audit_run['sha256'].items():
    assert sha(HERE / name) == digest
audit = read('audit_result.json')
assert audit['status'] == 'PASS_INDEPENDENT_W8_QUADRATIC_PARTIAL_IDEAL_REPLAY'
assert [x['case_index'] for x in audit['checks']] == audit_protocol['case_indexes']
for x in audit['checks']:
    c = cases[x['case_index']]
    for key,aud_key in [('left_unique_reciprocals','left_unique'),('right_unique_reciprocals','right_unique'),
                        ('left_span_rank','left_rank'),('right_span_rank','right_rank'),
                        ('exact_quadratic_one_hot_ideal','onehot'),('exact_group_hits','group_hits')]:
        assert c[key] == x[aud_key], (x['case_index'], key)
    assert 1 << c['free_state_bits_per_slot'] == x['width']
    if x['direct_s3_coordinate_hits'] is not None:
        assert x['direct_s3_coordinate_hits'] == c['s3_coordinate_pairs']
build = read('build_receipt.json')
assert sha(Path(build['transitive_include'])) == build['transitive_include_sha256']
assert sha(HERE / 'census') == build['census_sha256']
assert build['command'] == ['clang++','-O3','-std=c++20','-Wall','-Wextra','-o','census','census.cpp']
assert 'Lean (version 4.34.1' in (HERE / 'lean_version.txt').read_text()
assert 'sorryAx' not in (HERE / 'lean_check.log').read_text()
assert "'PartialIdeal.quadratic_onehot' depends on axioms: [propext]" in (HERE / 'lean_check.log').read_text()
print(json.dumps({'status':'PASS_W8_QUADRATIC_PARTIAL_IDEAL_RECEIPTS',
                  'cases':len(cases),'native_wall_ns':run['wall_ns'],
                  'sage_audit_wall_ns':audit_run['wall_ns'],
                  'audit_cases':len(audit['checks']),
                  'result_sha256':sha(HERE / 'result.json'),
                  'audit_result_sha256':sha(HERE / 'audit_result.json')},sort_keys=True))
