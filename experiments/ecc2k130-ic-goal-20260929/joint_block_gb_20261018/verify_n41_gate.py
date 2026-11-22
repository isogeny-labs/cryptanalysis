"""Verify every frozen N41 joint-block case against the all-code census."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


cfg = json.loads((HERE / 'n41_gate_protocol.json').read_text())
for name, expected in cfg['sources'].items():
    path = Path(name)
    if not path.is_absolute():
        path = ROOT / path
    assert sha(path) == expected, name
allcode = json.loads((ROOT / cfg['allcode_result']).read_text())
assert allcode['total_zero_pairs'] == 1
assert allcode['targets'][0]['zero_pairs'] == [[253, 63]]
assert allcode['targets'][1]['zero_pairs'] == []
design = json.loads((HERE / 'protocol.json').read_text())
run_cfg = json.loads((HERE / 'run_protocol_n41.json').read_text())
rows = []
for k in range(1, 6):
    for label in ('p', 'o'):
        name = f'n41_{label}_k{k}'
        case = design['cases'][name]
        receipt = json.loads((HERE / f'{name}_receipt.json').read_text())
        result = json.loads((HERE / f'{name}_result.json').read_text())
        assert case['field_degree'] == 41 and case['first_free_bits'] == k
        assert case['first_base_code'] == 253 & ~((1 << k) - 1)
        assert case['target_index'] == (0 if label == 'p' else 1)
        assert receipt['status'] == 'COMPLETE' and receipt['stop_reason'] is None
        assert receipt['sampled_peak_combined_rss_bytes'] < run_cfg['rss_cap_bytes']
        assert receipt['wall_seconds'] <= case['wall_cap_seconds']
        assert receipt['protocol_sha256'] == sha(HERE / 'run_protocol_n41.json')
        assert receipt['stdout_sha256'] == sha(HERE / f'{name}.stdout')
        assert receipt['stderr_sha256'] == sha(HERE / f'{name}.stderr')
        assert receipt['result_sha256'] == sha(HERE / f'{name}_result.json')
        assert result['protocol_sha256'] == sha(HERE / 'protocol.json')
        assert result['target_index'] == case['target_index']
        assert result['first_free_bits'] == k and result['second_free_bits'] == 10
        assert result['variables'] == 10 + k and result['equations'] == 41
        if label == 'p':
            assert result['status'] == 'GB_COMPLETE'
            assert result['pinned_bits'] == result['variables']
            assert result['recovered_codes'] == {'first_code': 253, 'second_code': 63}
        else:
            assert result['status'] == 'GB_UNIT_IDEAL'
            assert result['recovered_codes'] is None
        rows.append({'case': name, 'status': result['status'],
                     'result_sha256': sha(HERE / f'{name}_result.json'),
                     'receipt_sha256': sha(HERE / f'{name}_receipt.json')})
out = {'status': 'PASS_N41_JOINT_BLOCK_CONTROL',
       'candidate_id': None, 'curve_id': design['curve_ids']['41'],
       'case_count': len(rows), 'max_first_free_bits': 5,
       'positive_codes': [253, 63], 'allcode_result_sha256': sha(ROOT / cfg['allcode_result']),
       'protocol_sha256': sha(HERE / 'n41_gate_protocol.json'), 'rows': rows}
(HERE / 'n41_gate.json').write_text(json.dumps(out, sort_keys=True, indent=2) + '\n')
print(json.dumps({k: out[k] for k in ('status', 'case_count', 'max_first_free_bits')}, sort_keys=True))
