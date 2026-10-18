"""Terminal verification of the exact two-pair circuit and inverse oracle."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
protocol = json.loads((HERE / 'verify_protocol.json').read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


for path, expected in protocol['sources'].items():
    assert sha(path) == expected, path
fixture = json.loads((HERE / 'fixture.json').read_text())
build = json.loads((HERE / 'build_result.json').read_text())
query = json.loads((HERE / 'query_result.json').read_text())
inverse = json.loads((HERE / 'inverse_result.json').read_text())
audit = json.loads((HERE / 'inverse_audit_result.json').read_text())
work = json.loads((HERE / 'work_result.json').read_text())
assert fixture['status'] == 'PASS_N41_W11_TWO_PAIR_POSITIVE_RESIDUAL_FIXTURE'
assert build['status'] == 'PASS_N41_W11_EXACT_TWO_PAIR_POSITIVE_CIRCUIT'
assert build['formula_sha256'] == sha(HERE / 'formula.xcnf')
assert build['constructed_assignment_check'] == \
    {'clauses': build['counts']['clauses'],
     'native_xor_rows': build['counts']['xor_rows']}
assert query['status'] == 'BOUNDED_UNKNOWN'
assert query['stop_reason'] == 'WALL_CAP' and query['monitor_error'] is None
assert query['wall_seconds'] >= 120
assert query['sampled_peak_combined_rss_bytes'] < 4*1024**3
assert query['solver_stdout_sha256'] == sha(HERE / 'solver.stdout')
assert not query['solver_terminal_sat'] and not query['solver_terminal_unsat']
assert inverse['status'] == 'COMPLETE_N41_W11_IMPLICIT_TWO_PAIR_ORACLE'
assert inverse['pair_law_checks'] == 1124
assert inverse['product_code_map_entries'] == 1024
assert [row['status'] for row in inverse['query_rows']] == \
    ['EXACT_TWO_PAIR_HIT', 'EXACT_TWO_PAIR_MISS']
assert inverse['query_rows'][0]['source_codes'] == [253, 63]
assert audit['status'] == 'PASS_INDEPENDENT_N41_W11_IMPLICIT_ORACLE_HIT_MISS'
assert [row['direct_exact_matches'] for row in audit['query_rows']] == [1, 0]
assert work['status'] == 'EXACT_N41_W11_SERIAL_IMPLICIT_ORACLE_WORK_LEDGER'
assert work['serial_candidate_checks_on_frozen_residual_order'] == 442911355
lean_log = (HERE / 'lean_check.log').read_text()
assert 'error:' not in lean_log and 'sorryAx' not in lean_log
assert 'SerialOracleWork.frozen_serial_candidate_count' in lean_log
result = {'status': 'PASS_N41_W11_EXACT_IMPLICIT_ORACLE_AND_WORK_AUDIT',
          'candidate_id': None, 'curve_id': protocol['curve_id'],
          'positive_source_codes': inverse['query_rows'][0]['source_codes'],
          'ordinary_control_exact_matches': audit['query_rows'][1]['direct_exact_matches'],
          'sat_control_status': query['status'],
          'serial_candidate_checks': work['serial_candidate_checks_on_frozen_residual_order'],
          'protocol_sha256': sha(HERE / 'verify_protocol.json')}
out = HERE / 'verification_result.json'
assert not out.exists()
out.write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
print(json.dumps(result, sort_keys=True))
