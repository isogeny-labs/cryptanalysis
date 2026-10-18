"""Replay frozen N131 width-one to width-three block-solver receipts."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


cfg = json.loads((HERE / 'n131_panel_protocol.json').read_text())
for name, expected in cfg['sources'].items():
    path = Path(name)
    if not path.is_absolute():
        path = ROOT / path
    assert sha(path) == expected, name
design = json.loads((HERE / 'protocol.json').read_text())
gate = json.loads((HERE / 'n41_gate.json').read_text())
assert gate['status'] == 'PASS_N41_JOINT_BLOCK_CONTROL'
assert gate['case_count'] == 10 and gate['max_first_free_bits'] == 5
lean_source = (HERE / 'JointSourceExpansion.lean').read_text()
lean_log = (HERE / 'lean_check.log').read_text()
for token in ('sorry', 'admit', 'sorryAx', 'unsafe', '\naxiom '):
    assert token not in lean_source
assert 'error:' not in lean_log and 'sorryAx' not in lean_log
for declaration in ('weighted_square', 'weighted_cube', 'weighted_fourth',
                    'joint_cubic_rewrite', 'source_power_correct',
                    'joint_resultant_expansion'):
    assert f"'JointSourceExpansion.{declaration}' depends on axioms:" in lean_log
replay = json.loads((HERE.parent / 'n131_w33_resultant_core_20261018' / 'replay_result.json').read_text())
assert replay['status'] == 'PASS_INDEPENDENT_N131_CURVE_REPLAY'
assert replay['source_codes'] == [3, 16722]
rows = []
for k in range(1, 4):
    for label in ('p', 'o'):
        name = f'n131_{label}_k{k}'
        c = design['cases'][name]
        suffix = ('_v3' if k == 3 and label == 'p' else
                  '_v2' if k == 3 else '')
        run_protocol = ('run_protocol_n131_v3.json' if suffix == '_v3' else
                        'run_protocol_n131_v2.json' if suffix == '_v2' else
                        'run_protocol_n131.json')
        result = json.loads((HERE / f'{name}_result.json').read_text())
        receipt = json.loads((HERE / f'{name}{suffix}_receipt.json').read_text())
        limit = json.loads((HERE / run_protocol).read_text())
        assert c['field_degree'] == 131 and c['first_free_bits'] == k
        assert c['first_base_code'] == 3 & ~((1 << k) - 1)
        assert receipt['status'] == 'COMPLETE' and receipt['stop_reason'] is None
        assert receipt['wall_seconds'] <= c['wall_cap_seconds'] == 600
        assert receipt['sampled_peak_combined_rss_bytes'] < limit['rss_cap_bytes']
        assert receipt['protocol_sha256'] == sha(HERE / run_protocol)
        assert receipt['result_sha256'] == sha(HERE / f'{name}_result.json')
        assert receipt['stdout_sha256'] == sha(HERE / f'{name}{suffix}.stdout')
        assert receipt['stderr_sha256'] == sha(HERE / f'{name}{suffix}.stderr')
        assert result['protocol_sha256'] == sha(HERE / 'protocol.json')
        assert result['target_index'] == c['target_index']
        assert result['first_free_bits'] == k and result['second_free_bits'] == 32
        assert result['variables'] == 32 + k and result['equations'] == 131
        if label == 'p':
            assert result['status'] == 'GB_COMPLETE'
            assert result['pinned_bits'] == result['variables']
            assert result['recovered_codes'] == {'first_code': 3, 'second_code': 16722}
            assert result['target_point'] == replay['target_point']
        else:
            assert result['status'] == 'GB_UNIT_IDEAL'
            assert result['recovered_codes'] is None
        rows.append({'case': name, 'status': result['status'],
                     'gb_seconds': result['gb_seconds'],
                     'wall_seconds': receipt['wall_seconds'],
                     'sampled_peak_combined_rss_bytes': receipt['sampled_peak_combined_rss_bytes'],
                     'anf_monomials': result['anf_monomials']})
old = json.loads((HERE / 'n131_p_k3_attempt1_result.json').read_text())
assert old['recovered_codes'] == {'first_code': 3, 'second_code': 16722}
assert old['status'] == 'GB_COMPLETE'
assert (HERE / 'n131_p_k3_wrapper_failure.txt').exists()
attempt2 = json.loads((HERE / 'n131_p_k3_v2_receipt.json').read_text())
assert attempt2['status'] == 'MONITOR_FAILURE'
assert attempt2['monitor_error'] == 'NoSuchProcess'
assert attempt2['exit_code'] == 0
assert json.loads((HERE / 'n131_p_k3_attempt2_result.json').read_text())['recovered_codes'] == {
    'first_code': 3, 'second_code': 16722}
out = {'status': 'PASS_N131_JOINT_BLOCK_PANEL_REPLAY',
       'candidate_id': None, 'curve_id': design['curve_ids']['131'],
       'n41_gate_sha256': sha(HERE / 'n41_gate.json'),
       'protocol_sha256': sha(HERE / 'n131_panel_protocol.json'),
       'rows': rows, 'case_count': len(rows)}
(HERE / 'n131_panel_verification.json').write_text(json.dumps(out, sort_keys=True, indent=2) + '\n')
print(json.dumps({'status': out['status'], 'case_count': len(rows)}, sort_keys=True))
