"""Audit frozen cubic, matched quartic, and wider-branch result receipts."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
BASELINE = ROOT / 'nonzero_branch_quartic_baseline_20261023'
WIDE = ROOT / 'nonzero_branch_cubic_w4_20261023'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


protocols = {}
for label, directory in (('cubic', HERE), ('quartic', BASELINE), ('width4', WIDE)):
    cfg = read(directory / 'protocol.json')
    assert cfg['status'].startswith('FROZEN_BEFORE_')
    assert cfg['candidate_id'] is None and cfg['worker_count'] == 1
    assert cfg['rss_cap_bytes'] == 4 * 1024**3
    assert cfg['sage_launcher'] == '/Volumes/SSD990/cryptanalysis/sage'
    for path, digest in cfg['sources'].items():
        assert sha(Path(path)) == digest, path
    runtime = read(directory / 'sage_runtime_info.json')
    assert runtime['status'] == 'verified'
    protocols[label] = cfg


def completed(directory, case_name, expected, codes):
    cfg = read(directory / 'protocol.json')
    receipt_path = directory / (case_name + '_receipt.json')
    result_path = directory / (case_name + '_result.json')
    receipt, result = read(receipt_path), read(result_path)
    assert receipt['status'] == 'COMPLETE' and receipt['exit_code'] == 0
    assert receipt['sampled_peak_combined_rss_bytes'] < cfg['rss_cap_bytes']
    assert receipt['wall_seconds'] < cfg['cases'][case_name]['wall_cap_seconds']
    assert receipt['result_sha256'] == sha(result_path)
    assert receipt['stdout_sha256'] == sha(directory / (case_name + '.stdout'))
    assert receipt['stderr_sha256'] == sha(directory / (case_name + '.stderr'))
    assert receipt['protocol_sha256'] == result['protocol_sha256'] == sha(directory / 'protocol.json')
    assert result['case'] == case_name and result['status'] == expected
    assert result['recovered_codes'] == codes
    assert result['nonzero_branch_exhaustive'] is True
    assert result['first_base_code'] == cfg['cases'][case_name]['first_base_code']
    assert result['free_code_positions'] == cfg['cases'][case_name]['free_code_positions']
    assert result['target_index'] == cfg['cases'][case_name]['target_index']
    return {'status': expected, 'wall_seconds': receipt['wall_seconds'],
            'peak_rss_bytes': receipt['sampled_peak_combined_rss_bytes'],
            'anf_monomials': result['anf_monomials'],
            'gb_seconds': result['gb_seconds'], 'receipt_sha256': sha(receipt_path)}


rows = {}
for label, directory in (('cubic', HERE), ('quartic', BASELINE)):
    rows[label] = {}
    for degree in (41, 131):
        for name, expected, codes in (
            ('positive', 'GB_COMPLETE', {'first_code': 253, 'second_code': 63} if degree == 41 else {'first_code': 3, 'second_code': 16722}),
            ('ordinary', 'GB_UNIT_IDEAL', None),
        ):
            case_name = f'n{degree}_{name}'
            rows[label][case_name] = completed(directory, case_name, expected, codes)
            cubic_case = protocols['cubic']['cases'][case_name]
            assert protocols['quartic']['cases'][case_name] == cubic_case
            result = read(directory / (case_name + '_result.json'))
            if label == 'cubic':
                assert max(map(int, result['degree_histogram'])) == 3
            else:
                assert max(map(int, result['degree_histogram'])) == 4

wide_cfg = protocols['width4']
wide_receipt = read(WIDE / 'n131_positive_receipt.json')
assert wide_receipt['status'] == wide_receipt['stop_reason'] == 'RSS_CAP'
assert wide_receipt['result_sha256'] is None and not (WIDE / 'n131_positive_result.json').exists()
assert wide_receipt['wall_seconds'] < 600
assert wide_receipt['sampled_peak_combined_rss_bytes'] > wide_cfg['rss_cap_bytes']
assert wide_receipt['stdout_sha256'] == sha(WIDE / 'n131_positive.stdout')
assert wide_receipt['stderr_sha256'] == sha(WIDE / 'n131_positive.stderr')
assert wide_receipt['protocol_sha256'] == sha(WIDE / 'protocol.json')
assert not (WIDE / 'n131_ordinary_receipt.json').exists()
wide_stdout = (WIDE / 'n131_positive.stdout').read_text().splitlines()
assert len(wide_stdout) == 1
wide_start = json.loads(wide_stdout[0])
assert wide_start['event'] == 'GB_START' and wide_start['variables'] == 36
assert wide_start['anf_monomials'] == 2843

for directory in (HERE, BASELINE):
    gate = read(directory / 'n41_gate.json')
    assert gate['status'] == 'PASS_N41_NONZERO_BRANCH_CONTROL'
    assert gate['protocol_sha256'] == sha(directory / 'protocol.json')
assert sha(WIDE / 'n41_gate.json') == sha(HERE / 'n41_gate.json')

audit = read(HERE / 'audit_result.json')
assert audit['status'] == 'PASS_SAGE_NONZERO_BRANCH_AUDIT'
assert [(r['degree'], r['nonzero_codes']) for r in audit['rows']] == [(41, 16), (131, 8), (131, 16)]
assert audit['rows'][0]['positive_valid_code_roots'] == [[253, 63]]
assert audit['rows'][0]['ordinary_valid_code_roots'] == []
replay_path = ROOT / 'n131_w33_resultant_core_20261018/replay_result.json'
assert audit['n131_prior_group_replay_sha256'] == sha(replay_path)
assert read(replay_path)['status'] == 'PASS_INDEPENDENT_N131_CURVE_REPLAY'

lean_log = (HERE / 'lean_check.log').read_text()
for declaration in ('excludes_zero_and_seed', 'product_ne_zero', 'cubic_branch_exact'):
    assert "'NonzeroBranch." + declaration + "' depends on axioms:" in lean_log
assert 'sorryAx' not in lean_log and 'error:' not in lean_log
assert (HERE / 'lean-toolchain').read_text().strip() == 'leanprover/lean4:v4.34.1'

ratio = {name: rows['quartic'][name]['wall_seconds'] / rows['cubic'][name]['wall_seconds']
         for name in ('n131_positive', 'n131_ordinary')}
out = {'status': 'PASS_NONZERO_BRANCH_COMPONENT_PANEL', 'candidate_id': None,
       'rows': rows, 'width4_positive': {'status': 'RSS_CAP',
           'wall_seconds': wide_receipt['wall_seconds'],
           'peak_rss_bytes': wide_receipt['sampled_peak_combined_rss_bytes'],
           'anf_monomials': wide_start['anf_monomials'],
           'receipt_sha256': sha(WIDE / 'n131_positive_receipt.json')},
       'width4_ordinary': {'status': 'GATED'},
       'quartic_over_cubic_wall_ratio_exploratory': ratio,
       'audit_sha256': sha(HERE / 'audit_result.json'),
       'lean_source_sha256': sha(HERE / 'NonzeroBranch.lean'),
       'lean_log_sha256': sha(HERE / 'lean_check.log')}
with (HERE / 'verification_result.json').open('w') as stream:
    json.dump(out, stream, sort_keys=True, indent=2)
    stream.write('\n')
print(out['status'])
