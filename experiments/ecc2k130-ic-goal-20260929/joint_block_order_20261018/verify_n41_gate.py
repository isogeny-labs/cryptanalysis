"""Freeze the degrevlex N41 positive and ordinary block controls."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


cfg = json.loads((HERE / 'n41_gate_protocol.json').read_text())
for name, digest in cfg['sources'].items():
    path = Path(name)
    if not path.is_absolute():
        path = ROOT / path
    assert sha(path) == digest, name
design = json.loads((HERE / 'protocol.json').read_text())
run = json.loads((HERE / 'run_protocol_n41.json').read_text())
prior_gate = json.loads((HERE.parent / 'joint_block_gb_20261018' / 'n41_gate.json').read_text())
assert prior_gate['status'] == 'PASS_N41_JOINT_BLOCK_CONTROL'
assert design['term_order'] == 'degrevlex'
rows = []
for label in ('p', 'o'):
    name = f'n41_{label}_k5'
    case = design['cases'][name]
    result = json.loads((HERE / f'{name}_result.json').read_text())
    receipt = json.loads((HERE / f'{name}_receipt.json').read_text())
    assert case['first_free_bits'] == 5 and case['first_base_code'] == 224
    assert case['target_index'] == (0 if label == 'p' else 1)
    assert receipt['status'] == 'COMPLETE' and receipt['stop_reason'] is None
    assert receipt['wall_seconds'] < case['wall_cap_seconds'] == 120
    assert receipt['sampled_peak_combined_rss_bytes'] < run['rss_cap_bytes']
    assert receipt['result_sha256'] == sha(HERE / f'{name}_result.json')
    assert receipt['stdout_sha256'] == sha(HERE / f'{name}.stdout')
    assert receipt['stderr_sha256'] == sha(HERE / f'{name}.stderr')
    assert receipt['protocol_sha256'] == sha(HERE / 'run_protocol_n41.json')
    assert result['term_order'] == 'degrevlex'
    assert result['protocol_sha256'] == sha(HERE / 'protocol.json')
    assert result['variables'] == 15 and result['equations'] == 41
    if label == 'p':
        assert result['status'] == 'GB_COMPLETE'
        assert result['recovered_codes'] == {'first_code': 253, 'second_code': 63}
        assert result['pinned_bits'] == 15
    else:
        assert result['status'] == 'GB_UNIT_IDEAL'
        assert result['recovered_codes'] is None
    rows.append({'case': name, 'status': result['status'],
                 'result_sha256': sha(HERE / f'{name}_result.json'),
                 'receipt_sha256': sha(HERE / f'{name}_receipt.json')})
out = {'status': 'PASS_N41_DEGREVLEX_CONTROL', 'candidate_id': None,
       'curve_id': design['curve_ids']['41'], 'term_order': 'degrevlex',
       'case_count': 2, 'prior_gate_sha256': sha(HERE.parent / 'joint_block_gb_20261018' / 'n41_gate.json'),
       'protocol_sha256': sha(HERE / 'n41_gate_protocol.json'), 'rows': rows}
(HERE / 'n41_gate.json').write_text(json.dumps(out, sort_keys=True, indent=2) + '\n')
print(json.dumps({'status': out['status'], 'case_count': out['case_count']}, sort_keys=True))
