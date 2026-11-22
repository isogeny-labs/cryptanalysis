"""Check frozen N131 filter construction and bounded solver receipts."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORKSPACE = HERE.parents[2]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(name):
    return json.loads((HERE / name).read_text())


for name, expected in read('verification_protocol.json')['sources'].items():
    path = Path(name)
    if not path.is_absolute():
        path = WORKSPACE / path
    assert sha(path) == expected, name
build = read('build_0_result.json')
assert build['status'] == 'PASS_N131_W33_RESULTANT_FILTER_CIRCUIT'
assert build['candidate_id'] is None
assert build['protocol_sha256'] == sha(HERE / 'build_protocol.json')
assert build['formula_sha256'] == sha(HERE / 'positive.xcnf')
assert build['counts']['and_gates'] == 6841
assert build['counts']['variables'] == 11868
assert build['counts']['clauses'] == 20655
assert build['counts']['xor_rows'] == 4963
assert build['positive_assignment_check'] == {
    'clauses': 20655, 'native_xor_rows': 4963}
audit = read('independent_audit_result.json')
assert audit['status'] == 'PASS_N131_W33_INDEPENDENT_POSITIVE_ROOT'
assert audit['formula_sha256'] == build['formula_sha256']
assert audit['resultant_value'] == 0

statuses = []
for prefix, protocol in (('solver_0', 'solver_protocol.json'),
                         ('solver_600_0', 'solver_600_protocol.json')):
    row = read(prefix + '_result.json')
    cfg = read(protocol)
    assert row['protocol_sha256'] == sha(HERE / protocol)
    assert row['curve_id'] == build['curve_id']
    assert row['candidate_id'] is None
    assert row['sampled_peak_combined_rss_bytes'] < cfg['rss_cap_bytes']
    assert row['solver_stdout_sha256'] == sha(HERE / (prefix + '.stdout'))
    assert row['solver_stderr_sha256'] == sha(HERE / (prefix + '.stderr'))
    assert row['wall_seconds'] <= cfg['parent_wall_cap_seconds'] + 2
    if row['status'] == 'BOUNDED_UNKNOWN':
        assert row['stop_reason'] == 'WALL_CAP' or row['solver_terminal_indeterminate']
        assert not row['solver_terminal_sat'] and not row['solver_terminal_unsat']
    elif row['status'] == 'SAT_MODEL_UNVERIFIED':
        assert row['solver_terminal_sat']
    else:
        raise AssertionError((prefix, row['status']))
    statuses.append(row['status'])
out = {'status': 'PASS_N131_W33_RESULTANT_FILTER_RECEIPT_REPLAY',
       'candidate_id': None, 'curve_id': build['curve_id'],
       'positive_filter_assignment': 'PASS',
       'solver_statuses': statuses,
       'formula_sha256': build['formula_sha256'],
       'verification_protocol_sha256': sha(HERE / 'verification_protocol.json')}
(HERE / 'verification_result.json').write_text(json.dumps(out, sort_keys=True, indent=2) + '\n')
print(json.dumps(out, sort_keys=True))
