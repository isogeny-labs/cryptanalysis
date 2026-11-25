"""Derive the exact serial-oracle work floor from frozen join counters."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PRIOR = HERE.parent / 'n41_target_conditioned_2p1_join_20261018'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


cfg = json.loads((HERE / 'work_protocol.json').read_text())
for name, expected in cfg['source_sha256'].items():
    path = Path(name)
    if not path.is_absolute():
        path = ROOT / path
    assert sha(path) == expected, name
prior = json.loads((PRIOR / 'run_result.json').read_text())
query = json.loads((HERE / 'query_result.json').read_text())
audit = json.loads((HERE / 'audit_result.json').read_text())
assert prior['status'] == 'HIT_PENDING_SAGE_REPLAY'
assert query['status'] == 'COMPLETE_PENDING_INDEPENDENT_REPLAY'
assert audit['status'] == 'PASS_INDEPENDENT_N41_IMPLICIT_PAIR_PANEL'
assert len(prior['orientation_done_lines']) == 3
completed = [list(map(int, line.split()[1:4]))
             for line in prior['orientation_done_lines']]
assert completed == [[0, 21868032, 0], [1, 21868032, 0], [2, 21868032, 0]]
hit = prior['hit_lines'][0].split()
assert hit[:7] == ['HIT', '3', '0', '130', '233', '283', '152']
hit_probes, hit_matches = int(hit[7]), int(hit[8])
assert (hit_probes, hit_matches) == (18008709, 2)
queries = sum(row[1] for row in completed) + hit_probes
matches = sum(row[2] for row in completed) + hit_matches
assert queries == 83612805 and matches == 2
# Every key without a left-pair match exhausts all 284 first-slot states.
# At most one distinct key is made nonempty per reported hash match.
minimum_misses = queries - matches
first_states = 284
minimum_checks = minimum_misses * first_states
assert minimum_checks == 23746036052
lines = (HERE / 'query.stdout').read_text().splitlines()
case_seconds = sum(float(line.split()[-1]) for line in lines
                   if line.startswith('CASE '))
assert len([line for line in lines if line.startswith('CASE ')]) == 385
assert audit['panel_cases'] == 385
assert query['total_lines'] == ['TOTAL 385 109340 1 1']
result = {'status': 'EXACT_SERIAL_POLICY_WORK_FLOOR',
          'candidate_id': None,
          'reference_join_lookups': queries,
          'reference_join_hash_matches': matches,
          'minimum_complete_miss_keys': minimum_misses,
          'first_slot_states': first_states,
          'minimum_first_state_checks': minimum_checks,
          'required_check_rate_for_600s': str(minimum_checks / 600),
          'panel_cases': 385, 'panel_first_state_checks': 109340,
          'panel_native_case_seconds': case_seconds,
          'panel_measured_checks_per_second': 109340 / case_seconds,
          'operation_boundary': 'one first-state group subtraction and source-product inference per serial candidate; complete misses exhaust 284 states',
          'no_full_run_time_extrapolation': True,
          'protocol_sha256': sha(HERE / 'work_protocol.json')}
assert not (HERE / 'work_result.json').exists()
(HERE / 'work_result.json').write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')
print(json.dumps({k: result[k] for k in
                  ('status', 'reference_join_lookups',
                   'minimum_first_state_checks')}, sort_keys=True))
