"""Replay the bounded N131 positive width-four first attempt."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


cfg = json.loads((HERE / 'width4_protocol.json').read_text())
for name, expected in cfg['sources'].items():
    path = Path(name)
    if not path.is_absolute():
        path = ROOT / path
    assert sha(path) == expected, name
design = json.loads((HERE / 'protocol.json').read_text())
case = design['cases']['n131_p_k4']
assert case['field_degree'] == 131 and case['target_index'] == 0
assert case['first_base_code'] == 0 and case['first_free_bits'] == 4
assert 3 < 1 << case['first_free_bits']
run = json.loads((HERE / 'run_protocol_n131_v3.json').read_text())
receipt = json.loads((HERE / 'n131_p_k4_v3_receipt.json').read_text())
handle = json.loads((HERE / 'n131_p_k4_v3_handle.json').read_text())
assert handle['child_pid'] == receipt['child_pid']
assert receipt['status'] == 'BOUNDED_UNKNOWN'
assert receipt['stop_reason'] == 'WALL_CAP'
assert receipt['exit_code'] == -15 and receipt['monitor_error'] is None
assert receipt['result_sha256'] is None
assert not (HERE / 'n131_p_k4_result.json').exists()
assert receipt['wall_seconds'] >= case['wall_cap_seconds']
assert receipt['wall_seconds'] < case['wall_cap_seconds'] + 2
assert receipt['sampled_peak_combined_rss_bytes'] < run['rss_cap_bytes']
assert receipt['protocol_sha256'] == sha(HERE / 'run_protocol_n131_v3.json')
assert receipt['stdout_sha256'] == sha(HERE / 'n131_p_k4_v3.stdout')
assert receipt['stderr_sha256'] == sha(HERE / 'n131_p_k4_v3.stderr')
assert 'GB_START' in (HERE / 'n131_p_k4_v3.stdout').read_text()
assert 'GB_COMPLETE' not in (HERE / 'n131_p_k4_v3.stdout').read_text()
out = {'status': 'PASS_N131_WIDTH4_CAP_REPLAY', 'candidate_id': None,
       'curve_id': receipt['curve_id'], 'case': receipt['case'],
       'terminal_status': receipt['status'], 'wall_seconds': receipt['wall_seconds'],
       'sampled_peak_combined_rss_bytes': receipt['sampled_peak_combined_rss_bytes'],
       'protocol_sha256': sha(HERE / 'width4_protocol.json')}
(HERE / 'width4_verification.json').write_text(json.dumps(out, sort_keys=True, indent=2) + '\n')
print(json.dumps(out, sort_keys=True))
