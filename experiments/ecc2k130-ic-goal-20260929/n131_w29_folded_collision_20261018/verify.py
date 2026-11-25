"""Audit frozen collision sources, independent replay, and Lean proofs."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(name):
    return json.loads((HERE / name).read_text())


for name in ('protocol.json', 'filter_protocol.json', 'verify_protocol.json'):
    for path, expected in read(name)['sources'].items():
        assert sha(path) == expected, (name, path)

audit = read('audit_result.json')
filtered = read('filter_result.json')
replay = read('verification_result.json')
assert audit['protocol_sha256'] == sha(HERE / 'protocol.json')
assert filtered['protocol_sha256'] == sha(HERE / 'filter_protocol.json')
assert replay['protocol_sha256'] == sha(HERE / 'verify_protocol.json')
assert audit['candidate_id'] is None and filtered['candidate_id'] is None
assert audit['case_count'] == 524
assert audit['nontrivial_case_count'] == 14
assert filtered['counts']['enumerated_code_pairs'] == 33096
assert filtered['distinct_valid_collision_pairs'] == 2093
assert replay['status'] == 'PASS_INDEPENDENT_SAGE_ORBIT_AND_CURVE_VALIDITY_REPLAY'
assert replay['linear_cases_replayed'] == 524
assert replay['distinct_valid_collision_pairs'] == 2093
assert len(filtered['collision_pairs']) == 2093
assert all(a < b for a, b in (row['codes'] for row in filtered['collision_pairs']))
assert len({tuple(row['codes']) for row in filtered['collision_pairs']}) == 2093
assert (HERE / 'lean_exit_code.txt').read_text().strip() == '0'
log = (HERE / 'lean_check.log').read_text()
assert log.count('depends on axioms:') == 2
assert 'sorryAx' not in log and 'error:' not in log

out = {'status': 'PASS_N131_W29_COLLISION_RECEIPT_AUDIT',
       'candidate_id': None,
       'curve_id': audit['curve_id'],
       'valid_cross_code_pairs': 2093,
       'lean_module_sha256': sha(HERE / 'FoldedCollision.lean'),
       'independent_replay_sha256': sha(HERE / 'verification_result.json')}
(HERE / 'receipt_audit.json').write_text(json.dumps(out, sort_keys=True, indent=2) + '\n')
print(json.dumps(out, sort_keys=True))
