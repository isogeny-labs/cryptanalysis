"""Audit frozen W20 subset norms and independent native finite scans."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SUPPORT = ROOT / 'n131_w20_sevenpair_gate_20261010/support_w20.tsv'
COEFF = ROOT / 'n131_w33_freecode_resultant_20261018/coefficients.json'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_row(label):
    suffix = '_' + label if label else ''
    protocol = json.loads((HERE / ('protocol' + suffix + '.json')).read_text())
    receipt = json.loads((HERE / ('receipt' + suffix + '.json')).read_text())
    result = json.loads((HERE / ('result' + suffix + '.json')).read_text())
    assert protocol['source_sha256']['support_w20.tsv'] == sha(SUPPORT)
    assert protocol['source_sha256']['coefficients.json'] == sha(COEFF)
    assert protocol['source_sha256']['pilot.py'] == sha(HERE / 'pilot.py')
    assert protocol['source_sha256']['run.py'] == sha(HERE / 'run.py')
    assert protocol['source_sha256']['sage_runtime_info.json'] == sha(HERE / 'sage_runtime_info.json')
    assert receipt['protocol_sha256'] == sha(HERE / ('protocol' + suffix + '.json'))
    assert receipt['result_sha256'] == sha(HERE / ('result' + suffix + '.json'))
    assert receipt['stdout_sha256'] == sha(HERE / ('stdout' + suffix + '.txt'))
    assert receipt['stderr_sha256'] == sha(HERE / ('stderr' + suffix + '.txt'))
    assert receipt['status'] == result['status'] == 'COMPLETE_N131_W20_GLOBAL_NORM_PILOT'
    assert receipt['exit_code'] == 0 and receipt['stop_reason'] is None
    assert receipt['sampled_peak_combined_rss_bytes'] < protocol['rss_cap_bytes']
    assert result['self_maxrss_raw'] < protocol['rss_cap_bytes']
    assert result['subset_size'] == protocol['subset_size']
    assert result['valid_source_size'] == 132045
    assert result['protocol_sha256'] == receipt['protocol_sha256']
    assert [row['target_index'] for row in result['rows']] == protocol['target_indices']
    for row in result['rows']:
        assert row['norm_degree'] == 4 * result['subset_size']
        assert row['gcd_degree'] == len(row['first_code_hits'])
        assert sorted({a for a, _ in row['code_pair_hits']}) == row['first_code_hits']
    return protocol, receipt, result


def main():
    coeff = json.loads(COEFF.read_text())
    lines = []
    for i, row in enumerate(coeff['rows']):
        lines.append(f'T {i}')
        lines.extend(f'C {i} {x} {y} {z}' for x, y, z in row['terms'])
    assert (HERE / 'coefficients.tsv').read_text() == '\n'.join(lines) + '\n'
    direct = json.loads((HERE / 'direct_protocol.json').read_text())
    direct_files = {
        'direct_audit.cpp': HERE / 'direct_audit.cpp',
        'direct_audit': HERE / 'direct_audit',
        'field.hpp': ROOT / 'n131_w20_paired_raw_quotient_20261016/field.hpp',
        'coefficients.tsv': HERE / 'coefficients.tsv',
        'support_w20.tsv': SUPPORT,
        'direct_audit_stdout.txt': HERE / 'direct_audit_stdout.txt',
        'direct_audit_1024_stdout.txt': HERE / 'direct_audit_1024_stdout.txt',
    }
    assert direct['status'] == 'FROZEN_INDEPENDENT_NATIVE_DIRECT_AUDIT'
    assert direct['source_sha256'] == {name: sha(path) for name, path in direct_files.items()}
    p256, r256, a256 = verify_row('256')
    p1024, r1024, a1024 = verify_row('1024')
    p4096, r4096, a4096 = verify_row('')
    assert not r256['monitor_degraded'] and not r1024['monitor_degraded']
    assert r4096['monitor_degraded']
    assert (HERE / 'direct_audit_stdout.txt').read_text().splitlines() == [
        'ROW 0 1 3,16722', 'ROW 1 0']
    assert (HERE / 'direct_audit_1024_stdout.txt').read_text().splitlines() == [
        'ROW 0 1 3,16722', 'ROW 1 0']
    assert [row['code_pair_hits'] for row in a256['rows']] == [[[3, 16722]], []]
    assert [row['code_pair_hits'] for row in a1024['rows']] == [[[3, 16722]]]
    assert a4096['rows'][0]['code_pair_hits'] == [[3, 16722]]
    assert len(a4096['rows']) == 1
    print(json.dumps({'status': 'PASS_N131_SUBSET_NORM_AUDIT',
                      'subsets': [256, 1024, 4096],
                      'native_complete_scan_subsets': [256, 1024],
                      'largest_monitor_degraded': r4096['monitor_degraded'],
                      'largest_wall_seconds': r4096['wall_ns']/1e9}, sort_keys=True))


if __name__ == '__main__':
    main()
