"""Bind the degree-order N131 positive model to independent curve replay."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


cfg = json.loads((HERE / 'positive_gate_protocol.json').read_text())
for name, expected in cfg['sources'].items():
    path = Path(name)
    if not path.is_absolute():
        path = ROOT / path
    assert sha(path) == expected, name
design = json.loads((HERE / 'protocol.json').read_text())
case = design['cases']['n131_p_k4']
assert design['term_order'] == 'degrevlex'
assert case['first_base_code'] == 0 and case['first_free_bits'] == 4
assert 3 < 1 << case['first_free_bits']
run = json.loads((HERE / 'run_protocol_n131.json').read_text())
gate = json.loads((HERE / 'n41_gate.json').read_text())
assert gate['status'] == 'PASS_N41_DEGREVLEX_CONTROL'
receipt = json.loads((HERE / 'n131_p_k4_receipt.json').read_text())
result = json.loads((HERE / 'n131_p_k4_result.json').read_text())
assert receipt['status'] == 'COMPLETE' and receipt['stop_reason'] is None
assert receipt['exit_code'] == 0 and receipt['monitor_error'] is None
assert receipt['wall_seconds'] < case['wall_cap_seconds'] == 600
assert receipt['sampled_peak_combined_rss_bytes'] < run['rss_cap_bytes']
assert receipt['protocol_sha256'] == sha(HERE / 'run_protocol_n131.json')
assert receipt['result_sha256'] == sha(HERE / 'n131_p_k4_result.json')
assert receipt['stdout_sha256'] == sha(HERE / 'n131_p_k4.stdout')
assert receipt['stderr_sha256'] == sha(HERE / 'n131_p_k4.stderr')
assert result['status'] == 'GB_COMPLETE'
assert result['term_order'] == 'degrevlex'
assert result['protocol_sha256'] == sha(HERE / 'protocol.json')
assert result['pinned_bits'] == result['variables'] == 36
assert result['recovered_codes'] == {'first_code': 3, 'second_code': 16722}
replay = json.loads((HERE.parent / 'n131_w33_resultant_core_20261018' / 'replay_result.json').read_text())
assert replay['status'] == 'PASS_INDEPENDENT_N131_CURVE_REPLAY'
assert replay['source_codes'] == [3, 16722]
assert replay['target_point'] == result['target_point']
out = {'status': 'PASS_N131_DEGREVLEX_WIDTH4_POSITIVE_GATE',
       'candidate_id': None, 'curve_id': result['curve_id'],
       'source_codes': [3, 16722], 'target_point': result['target_point'],
       'term_order': 'degrevlex', 'wall_seconds': receipt['wall_seconds'],
       'sampled_peak_combined_rss_bytes': receipt['sampled_peak_combined_rss_bytes'],
       'protocol_sha256': sha(HERE / 'positive_gate_protocol.json')}
(HERE / 'positive_gate.json').write_text(json.dumps(out, sort_keys=True, indent=2) + '\n')
print(json.dumps(out, sort_keys=True))
