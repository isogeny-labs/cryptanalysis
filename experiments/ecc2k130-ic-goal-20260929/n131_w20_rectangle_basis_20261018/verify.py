"""Verify the saved one-shot source-partition receipts without rerunning them."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_run(prefix, expected, source_name, binary_name, code_name, runner_name):
    protocol_name = prefix + 'protocol.json'
    receipt_name = prefix + 'receipt.json'
    stdout_name = prefix + 'stdout.txt'
    stderr_name = prefix + 'stderr.txt'
    protocol = json.loads((HERE / protocol_name).read_text())
    receipt = json.loads((HERE / receipt_name).read_text())
    assert protocol['worker_count'] == 1
    assert protocol['wall_cap_seconds'] == 180
    assert protocol['rss_cap_bytes'] == 4 * 1024**3
    assert protocol['support_file'] == source_name
    for rel, digest in protocol['repo_sha256'].items():
        assert sha(ROOT / rel) == digest
    for name, digest in protocol['local_sha256'].items():
        path = HERE / name
        if prefix == 'affine_attempt1_':
            path = HERE / {'affine': binary_name, 'affine.cpp': code_name}.get(name, name)
        assert sha(path) == digest, name
    assert receipt['protocol_sha256'] == sha(HERE / protocol_name)
    assert receipt['stdout_sha256'] == sha(HERE / stdout_name)
    assert receipt['stderr_sha256'] == sha(HERE / stderr_name)
    assert receipt['status'] == expected
    assert receipt['candidate_id'] is None
    assert receipt['sampled_peak_combined_rss_bytes'] < protocol['rss_cap_bytes']
    if expected.startswith('COMPLETE'):
        assert receipt['exit_code'] == 0
        assert receipt['stop_reason'] is None
        assert not receipt['monitor_degraded']
    return receipt


def main():
    source = 'n131_w20_sevenpair_gate_20261010/support_w20.tsv'
    census = check_run('', 'COMPLETE_N131_W20_RECTANGLE_BASIS_CENSUS',
                       source, 'census', 'census.cpp', 'run.py')
    affine = check_run('affine_', 'COMPLETE_N131_W20_AFFINE_SEARCH',
                       source, 'affine', 'affine.cpp', 'affine_run.py')
    failed = check_run('affine_attempt1_', 'PRODUCER_FAILURE',
                       source, 'affine_attempt1_binary', 'affine_attempt1.cpp', 'affine_run.py')
    assert census['row_count'] == 5016
    assert affine['row_count'] == 64
    assert failed['exit_code'] == 1
    assert (HERE / 'affine_attempt1_stderr.txt').read_text().strip() == 'pair count'
    audit = json.loads((HERE / 'audit_result.json').read_text())
    affine_audit = json.loads((HERE / 'affine_audit_result.json').read_text())
    assert audit['status'] == 'INDEPENDENT_AUDIT_PASS'
    assert affine_audit['status'] == 'INDEPENDENT_AFFINE_AUDIT_PASS'
    assert audit['census_stdout_sha256'] == census['stdout_sha256']
    assert affine_audit['affine_stdout_sha256'] == affine['stdout_sha256']
    assert audit['valid_codes'] == 132045
    assert audit['all_two_bit_partitions_replayed'] == 171
    assert affine_audit['full_direction_count'] == 524287
    assert affine_audit['selected_plane_pairs_replayed'] == 2016
    assert affine_audit['selected_plane']['nonempty_cosets'] == 89346
    lean = (HERE / 'lean_check.txt').read_text()
    assert 'sorryAx' not in lean and 'error:' not in lean
    assert lean.count('depends on axioms: [propext]') == 3
    print(json.dumps({'status': 'PASS', 'coordinate_rows': census['row_count'],
                      'affine_directions': affine_audit['full_direction_count'],
                      'affine_planes': affine_audit['selected_plane_pairs_replayed'],
                      'first_attempt': failed['status']}, sort_keys=True))


if __name__ == '__main__':
    main()
