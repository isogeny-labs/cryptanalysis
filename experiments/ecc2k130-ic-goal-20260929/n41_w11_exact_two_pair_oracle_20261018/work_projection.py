"""Count exact serial inverse-oracle calls on the frozen native residual path."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
protocol = json.loads((HERE / 'work_protocol.json').read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


for path, expected in protocol['sources'].items():
    assert sha(path) == expected, path
out = HERE / 'work_result.json'
assert not out.exists()
native = json.loads((ROOT / 'n41_w11_fivepair_native_join_20261018' /
                     'query_result.json').read_text())
inverse = json.loads((HERE / 'inverse_result.json').read_text())
audit = json.loads((HERE / 'inverse_audit_result.json').read_text())
assert native['status'] == 'N41_W11_NATIVE_RELATION_UNVERIFIED'
assert native['hit']['hash_hits'] == 1
assert inverse['status'] == 'COMPLETE_N41_W11_IMPLICIT_TWO_PAIR_ORACLE'
assert audit['status'] == 'PASS_INDEPENDENT_N41_W11_IMPLICIT_ORACLE_HIT_MISS'
assert inverse['first_pair_states'] == 1124
assert inverse['query_rows'][0]['status'] == 'EXACT_TWO_PAIR_HIT'
assert inverse['query_rows'][0]['states_examined'] == 279
source = (ROOT / 'n41_w11_fivepair_native_join_20261018' / 'join.cpp').read_text()
assert 'if (middle.code == lists[0][L.a].code ||' in source
assert 'if (!five_distinct(row)) { ++rejected; continue; }' in source
assert '++hits;' in source and 'return 0;' in source
probes = native['hit']['probes']
early_skips = native['hit']['rejected_hit_or_probe']
assert probes == 396919 and early_skips == 2869
residuals = probes - early_skips
misses = residuals - 1
candidate_checks = misses * 1124 + inverse['query_rows'][0]['states_examined']
assert misses == 394049 and candidate_checks == 442911355
result = {'status': 'EXACT_N41_W11_SERIAL_IMPLICIT_ORACLE_WORK_LEDGER',
          'candidate_id': None, 'curve_id': inverse['curve_id'],
          'native_probe_indices': probes,
          'native_early_code_skips': early_skips,
          'target_residual_queries': residuals,
          'right_pair_hash_hits': native['hit']['hash_hits'],
          'completed_negative_residual_queries': misses,
          'first_pair_states_per_complete_miss': 1124,
          'final_positive_first_pair_states': inverse['query_rows'][0]['states_examined'],
          'serial_candidate_checks_on_frozen_residual_order': candidate_checks,
          'scope': 'same native target-derived residual order, separate exhaustive implicit query per residual, no cross-residual caching or batching',
          'protocol_sha256': sha(HERE / 'work_protocol.json')}
out.write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
print(json.dumps(result, sort_keys=True))
