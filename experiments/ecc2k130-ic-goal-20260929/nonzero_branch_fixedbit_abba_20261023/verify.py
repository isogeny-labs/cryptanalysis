"""Audit every ABBA arm, exact ANF substitution, and resource receipt."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


cfg = read(HERE / 'protocol.json')
assert cfg['status'] == 'FROZEN_BEFORE_FIXEDBIT_ABBA_RUNS'
assert cfg['arm_order'] == ['old', 'new', 'new', 'old']
assert cfg['worker_count'] == 1 and cfg['rss_cap_bytes'] == 4 * 1024**3
assert cfg['wall_cap_seconds'] == 600
assert cfg['sage_launcher'] == '/Volumes/SSD990/cryptanalysis/sage'
assert read(HERE / 'sage_runtime_info.json')['status'] == 'verified'
for path, digest in cfg['sources'].items():
    assert sha(Path(path)) == digest, path

audit = read(HERE / 'anf_audit_result.json')
assert audit['status'] == 'PASS_EXACT_FIXED_BIT_CUBIC_ANF_IDENTITY'
assert audit['source_protocol_sha256'] == sha(HERE / 'protocol.json')
assert [row['target_index'] for row in audit['rows']] == [0, 1]
assert all(row['old_anf_monomials'] == 2314 and row['new_anf_monomials'] == 2215
           and row['substitution_exact'] for row in audit['rows'])

all_rows = {}
for panel, target_index in (('positive', 0), ('ordinary', 1)):
    rows = []
    target_points = []
    for index, arm in enumerate(cfg['arm_order']):
        directory = HERE / f'{panel}_{index}_{arm}'
        receipt = read(directory / 'receipt.json')
        case = cfg['arms'][arm]['cases'][panel]
        result_path = directory / (case + '_result.json')
        result = read(result_path)
        assert receipt['status'] == 'COMPLETE' and receipt['exit_code'] == 0
        assert receipt['panel'] == panel and receipt['index'] == index and receipt['arm'] == arm
        assert receipt['case'] == case and receipt['stop_reason'] is None
        assert receipt['wall_seconds'] < 600 and receipt['sampled_peak_combined_rss_bytes'] < cfg['rss_cap_bytes']
        assert receipt['rss_samples'] > 0 and receipt['monitor_error'] is None
        assert receipt['protocol_sha256'] == sha(HERE / 'protocol.json')
        assert receipt['arm_protocol_sha256'] == sha(directory / 'protocol.json') == cfg['sources'][cfg['arms'][arm]['directory'] + '/protocol.json']
        assert receipt['arm_source_sha256'] == sha(directory / 'branch_gb.py') == cfg['sources'][cfg['arms'][arm]['directory'] + '/branch_gb.py']
        assert receipt['result_sha256'] == sha(result_path)
        assert receipt['stdout_sha256'] == sha(directory / 'stdout.log')
        assert receipt['stderr_sha256'] == sha(directory / 'stderr.log')
        assert result['case'] == case and result['candidate_id'] is None
        assert result['target_index'] == target_index
        assert result['curve_id'] == cfg['curve_id']
        assert result['protocol_sha256'] == receipt['arm_protocol_sha256']
        assert result['recovered_codes'] == ({'first_code': 3, 'second_code': 16722} if panel == 'positive' else None)
        assert result['status'] == ('GB_COMPLETE' if panel == 'positive' else 'GB_UNIT_IDEAL')
        assert result['variables'] == (36 if arm == 'old' else 35)
        assert result['equations'] == (132 if arm == 'old' else 131)
        assert result['anf_monomials'] == (2314 if arm == 'old' else 2215)
        start = json.loads((directory / 'stdout.log').read_text().splitlines()[0])
        assert start['event'] == 'GB_START' and start['variables'] == result['variables']
        target_points.append(result['target_point'])
        rows.append({'arm': arm, 'wall_seconds': receipt['wall_seconds'],
                     'gb_seconds': result['gb_seconds'],
                     'peak_rss_bytes': receipt['sampled_peak_combined_rss_bytes'],
                     'receipt_sha256': sha(directory / 'receipt.json')})
    assert all(point == target_points[0] for point in target_points)
    if panel == 'ordinary':
        assert target_points[0] == cfg['ordinary_point']
    # Match the adjacent old/new pair and the reversed new/old pair.
    pair_ratios = [rows[0]['wall_seconds'] / rows[1]['wall_seconds'],
                   rows[3]['wall_seconds'] / rows[2]['wall_seconds']]
    all_rows[panel] = {'target_point': target_points[0], 'arms': rows,
                       'old_over_new_wall_ratios': pair_ratios,
                       'old_mean_wall_seconds': (rows[0]['wall_seconds'] + rows[3]['wall_seconds']) / 2,
                       'new_mean_wall_seconds': (rows[1]['wall_seconds'] + rows[2]['wall_seconds']) / 2}

out = {'status': 'PASS_FIXEDBIT_ABBA_COMPONENT_PANEL', 'candidate_id': None,
       'protocol_sha256': sha(HERE / 'protocol.json'), 'anf_audit_sha256': sha(HERE / 'anf_audit_result.json'),
       'panels': all_rows}
with (HERE / 'verification_result.json').open('w') as stream:
    json.dump(out, stream, sort_keys=True, indent=2)
    stream.write('\n')
print(out['status'])
