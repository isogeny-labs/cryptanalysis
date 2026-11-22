"""Replay the N41 gate, N131 width-four pair, and lex-order control."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


cfg = json.loads((HERE / 'panel_protocol.json').read_text())
for name, expected in cfg['sources'].items():
    path = Path(name)
    if not path.is_absolute():
        path = ROOT / path
    assert sha(path) == expected, name
design = json.loads((HERE / 'protocol.json').read_text())
assert design['term_order'] == 'degrevlex'
gate = json.loads((HERE / 'n41_gate.json').read_text())
assert gate['status'] == 'PASS_N41_DEGREVLEX_CONTROL' and gate['case_count'] == 2
positive = json.loads((HERE / 'positive_gate.json').read_text())
assert positive['status'] == 'PASS_N131_DEGREVLEX_WIDTH4_POSITIVE_GATE'
assert positive['source_codes'] == [3, 16722]
assert positive['term_order'] == 'degrevlex'
prior = json.loads((HERE.parent / 'joint_block_gb_20261018' / 'n131_p_k4_v3_receipt.json').read_text())
assert prior['status'] == 'BOUNDED_UNKNOWN' and prior['stop_reason'] == 'WALL_CAP'
assert prior['result_sha256'] is None
diff = (HERE / 'source_diff.patch').read_text()
assert "order='lex'" in diff and "order=cfg['term_order']" in diff
assert diff.count('@@') == 8
rows = []
for label in ('p', 'o'):
    name = f'n131_{label}_k4'
    case = design['cases'][name]
    run_protocol = 'run_protocol_n131.json' if label == 'p' else 'run_protocol_public.json'
    limit = json.loads((HERE / run_protocol).read_text())
    result = json.loads((HERE / f'{name}_result.json').read_text())
    receipt = json.loads((HERE / f'{name}_receipt.json').read_text())
    assert case['field_degree'] == 131 and case['first_free_bits'] == 4
    assert case['first_base_code'] == 0
    assert receipt['status'] == 'COMPLETE' and receipt['stop_reason'] is None
    assert receipt['exit_code'] == 0 and receipt['monitor_error'] is None
    assert receipt['wall_seconds'] < case['wall_cap_seconds'] == 600
    assert receipt['sampled_peak_combined_rss_bytes'] < limit['rss_cap_bytes']
    assert receipt['protocol_sha256'] == sha(HERE / run_protocol)
    assert receipt['result_sha256'] == sha(HERE / f'{name}_result.json')
    assert receipt['stdout_sha256'] == sha(HERE / f'{name}.stdout')
    assert receipt['stderr_sha256'] == sha(HERE / f'{name}.stderr')
    assert result['protocol_sha256'] == sha(HERE / 'protocol.json')
    assert result['term_order'] == 'degrevlex'
    assert result['equations'] == 131 and result['variables'] == 36
    assert result['anf_monomials'] == 5317
    if label == 'p':
        assert result['status'] == 'GB_COMPLETE'
        assert result['pinned_bits'] == 36
        assert result['recovered_codes'] == {'first_code': 3, 'second_code': 16722}
        assert result['target_point'] == positive['target_point']
    else:
        assert result['status'] == 'GB_UNIT_IDEAL'
        assert result['recovered_codes'] is None
        assert result['target_point'] == [877610862732227974378969808549299291499,
                                          2063336771837286479337213121437715536874]
    rows.append({'case': name, 'status': result['status'],
                 'wall_seconds': receipt['wall_seconds'],
                 'sampled_peak_combined_rss_bytes': receipt['sampled_peak_combined_rss_bytes'],
                 'gb_seconds': result['gb_seconds']})
out = {'status': 'PASS_N131_DEGREVLEX_WIDTH4_PANEL_REPLAY',
       'candidate_id': None, 'curve_id': design['curve_ids']['131'],
       'term_order': 'degrevlex', 'prior_lex_positive_status': prior['status'],
       'positive_gate_sha256': sha(HERE / 'positive_gate.json'),
       'protocol_sha256': sha(HERE / 'panel_protocol.json'), 'rows': rows}
(HERE / 'panel_verification.json').write_text(json.dumps(out, sort_keys=True, indent=2) + '\n')
print(json.dumps(out, sort_keys=True))
