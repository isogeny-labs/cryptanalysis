"""Replay source hashes, comparator controls, Lean proof, and query status."""
import hashlib
import json
from pathlib import Path

here = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


for name in ('build_protocol.json', 'probe_protocol.json', 'query_protocol.json'):
    protocol = json.loads((here/name).read_text())
    for path,digest in protocol['sources'].items():
        assert sha(path) == digest, (name,path)
build = json.loads((here/'build_result.json').read_text())
assert build['status'] == 'PASS_N41_EQUAL_ROTATION_ORDER_CIRCUIT'
assert build['comparator_gates'] == 30 and build['comparator_clauses'] == 149
assert build['exhaustive_code_pairs_checked'] == 65536
assert build['formula_sha256'] == sha(here/'formula.xcnf')
assert build['protocol_sha256'] == sha(here/'build_protocol.json')
assert sum(row['kind']=='positive' for row in build['controls']) == 1
assert all(row['accepted_by_order'] for row in build['controls']
           if row['kind']=='positive')
with (here/'formula.xcnf').open('r') as file:
    header = file.readline().split()
assert header == ['p','cnf',str(build['new_variables']),str(build['new_constraints'])]
probe = json.loads((here/'probe_result.json').read_text())
assert probe['status'] == 'COMPLETED_FROZEN_ABBA_PROBE'
assert probe['protocol_sha256'] == sha(here/'probe_protocol.json')
arms = probe['arm_results']
assert [row['arm'] for row in arms] == ['quadratic','ordered','ordered','quadratic']
assert all(row['status']=='INDETERMINATE_CONFLICT_CAP' and
           row['monitor_error'] is None and row['reported_conflicts'] >= 20000
           for row in arms)
for i,j in ((1,0),(2,3)):
    assert arms[i]['reported_decisions'] <= .9*arms[j]['reported_decisions']
    assert arms[i]['wall_seconds'] <= 1.25*arms[j]['wall_seconds']
    print('ordered_pair',i,j,'decision_ratio',
          arms[i]['reported_decisions']/arms[j]['reported_decisions'],
          'wall_ratio',arms[i]['wall_seconds']/arms[j]['wall_seconds'])
lean = (here/'lean_check.log').read_text()
assert (here/'lean_exit_code.txt').read_text().strip() == '0'
assert all(f"'OrderSymmetry.{name}' depends on axioms:" in lean
           for name in ('f4_swap','exchange_preserves_gate','ordered_orientation'))
assert not any(word in (here/'OrderSymmetry.lean').read_text()
               for word in ('sorry','admit','sorryAx'))
query = json.loads((here/'query_result.json').read_text())
assert query['protocol_sha256'] == sha(here/'query_protocol.json')
assert query['solver_stdout_sha256'] == sha(here/'solver.stdout')
assert query['solver_stderr_sha256'] == sha(here/'solver.stderr')
assert query['worker_count'] == 1 and query['monitor_error'] is None
assert query['sampled_peak_combined_rss_bytes'] <= 4294967296
assert query['status'] in ('BOUNDED_UNKNOWN','SAT_MODEL_UNVERIFIED')
if query['status'] == 'SAT_MODEL_UNVERIFIED':
    replay = json.loads((here/'replay_result.json').read_text())
    assert replay['status'] == 'PASS_INDEPENDENT_SAGE_MODEL_GROUP_REPLAY'
    assert replay['independent_group_matches'] > 0
print('PASS_ORDERED_N41_EVIDENCE_REPLAY',query['status'])
