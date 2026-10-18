"""Read-only audit of the frozen exact-ANF and capped-solver receipts."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORKSPACE = HERE.parents[2]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(name):
    return json.loads((HERE / name).read_text())


for name in ('protocol.json', 'runner_v2_protocol.json',
             'deglex_protocol.json', 'verify_protocol.json'):
    cfg = read(name)
    for source, expected in cfg['sources'].items():
        path = Path(source)
        if not path.is_absolute():
            path = WORKSPACE / path
        assert sha(path) == expected, source

verification = read('verification_result.json')
assert verification['status'] == 'PASS_EXACT_RESULTANT_ANF_REPLAY'
assert verification['protocol_sha256'] == sha(HERE / 'verify_protocol.json')
assert verification['cases']['n41_positive']['field_coefficients'] == 3046
assert verification['cases']['n41_ordinary']['field_coefficients'] == 3046
assert verification['cases']['n131_positive_48']['field_coefficients'] == 71857
assert [verification['cases'][name]['evaluations'] for name in
        ('n41_positive', 'n41_ordinary', 'n131_positive_48')] == [17, 16, 17]

for result_name, stem, status in (
        ('n41_positive_run_result.json', 'n41_positive', 'MONITOR_FAILURE'),
        ('n41_positive_run_v2_result.json', 'n41_positive_v2', 'BOUNDED_UNKNOWN'),
        ('n41_positive_deglex_run_result.json', 'n41_positive_deglex', 'BOUNDED_UNKNOWN'),
        ('n41_ordinary_deglex_run_result.json', 'n41_ordinary_deglex', 'BOUNDED_UNKNOWN')):
    row = read(result_name)
    assert row['status'] == status and row['candidate_id'] is None
    assert row['stdout_sha256'] == sha(HERE / (stem + '.stdout'))
    assert row['stderr_sha256'] == sha(HERE / (stem + '.stderr'))
    if status == 'BOUNDED_UNKNOWN':
        assert row['stop_reason'] == 'WALL_CAP'
        assert 120 <= row['wall_seconds'] < 122
        assert 0 < row['sampled_peak_combined_rss_bytes'] < 4294967296
        events = [(json.loads(line)['event']) for line in
                  (HERE / (stem + '.stdout')).read_text().splitlines()]
        assert events == ['ANF_READY', 'GB_START']
    else:
        assert row['monitor_error'] == 'PermissionError'
        assert row['sampled_peak_combined_rss_bytes'] == 0

assert not (HERE / 'n131_positive_48_result.json').exists()
assert not (HERE / 'n131_positive_48_deglex_result.json').exists()
print(json.dumps({'status': 'PASS_BOOLEAN_GB_FROZEN_AUDIT',
                  'unpromoted_n131': True, 'n41_capped_solver_runs': 3},
                 sort_keys=True))
