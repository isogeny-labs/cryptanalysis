"""Read-only verification of the bounded W33 block and Sage slice pilot."""
import hashlib
import json
from math import comb
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(name):
    return json.loads((HERE / name).read_text())


def check_sources(protocol):
    for item in protocol['sources'].values():
        assert sha(item['path']) == item['sha256']


def main():
    protocol, receipt, result = [load(x) for x in
                                 ('protocol.json', 'receipt.json', 'result.json')]
    audit_protocol, audit_receipt, audit = [load(x) for x in
                                            ('audit_protocol.json', 'audit_receipt.json',
                                             'audit_result.json')]
    resources = load('resource_bound.json')
    check_sources(protocol)
    check_sources(audit_protocol)
    assert protocol['status'] == 'FROZEN_BEFORE_N131_W33_BLOCK_PILOT'
    assert audit_protocol['status'] == 'FROZEN_BEFORE_N131_W33_BLOCK_SAGE_AUDIT'
    assert protocol['worker_count'] == audit_protocol['worker_count'] == 1
    assert protocol['rss_cap_bytes'] == audit_protocol['rss_cap_bytes'] == 4294967296
    for row, result_file, stdout, stderr in [
            (receipt, 'result.json', 'run.stdout', 'run.stderr'),
            (audit_receipt, 'audit_result.json', 'audit.stdout', 'audit.stderr')]:
        assert row['status'] == 'COMPLETE' and row['exit_code'] == 0
        assert row['stop_reason'] is None and row['wall_seconds'] < 180
        assert row['sampled_peak_combined_rss_bytes'] < 4294967296
        assert row['result_sha256'] == sha(HERE / result_file)
        assert row['stdout_sha256'] == sha(HERE / stdout)
        assert row['stderr_sha256'] == sha(HERE / stderr)
    assert result['status'] == 'COMPLETE_N131_W33_BLOCK_PILOT'
    assert result['protocol_sha256'] == sha(HERE / 'protocol.json')
    assert result['script_sha256'] == sha(HERE / 'run_n131.py')
    assert audit['status'] == 'PASS_N131_W33_BLOCK_SAGE_SLICE_AUDIT'
    assert audit['protocol_sha256'] == sha(HERE / 'audit_protocol.json')
    assert audit['script_sha256'] == sha(HERE / 'audit_sage.py')
    assert audit['result_sha256'] == sha(HERE / 'result.json')
    assert audit['values_checked'] == 16384
    assert len(result['rows']) == len(audit['checks']) == 2
    for index, (row, check) in enumerate(zip(result['rows'], audit['checks'])):
        assert row['target_index'] == check['target_index'] == index
        assert row['anchor'] == 0 and row['anf_terms'] == check['anf_terms'] == 1619
        assert row['anf_degree'] == 4 and check['slice_values_checked'] == 8192
        assert [x['degree'] for x in row['levels']] == [4, 5]
        assert [x['rank'] for x in row['levels']] == [131, 4585]
        assert all(not x['reject'] and x['certificate_rows'] is None
                   for x in row['levels'])
    assert audit['checks'][0]['roots_in_slices'] == [[3, 16722]]
    assert audit['checks'][1]['roots_in_slices'] == []
    assert resources['status'] == 'PASS_N131_W33_DENSE_REPRESENTATION_COUNT'
    assert resources['protocol_sha256'] == sha(HERE / 'protocol.json')
    assert resources['script_sha256'] == sha(HERE / 'resource_bound.py')
    for row in resources['levels']:
        assert row['columns'] == sum(comb(34, i) for i in range(row['degree'] + 1))
        assert row['rows'] == 131 * sum(comb(34, i) for i in range(row['degree'] - 3))
        assert row['matrix_bytes_rectangular'] == row['rows'] * ((row['columns'] + 7) // 8)
    assert resources['levels'][-1]['matrix_bytes_rectangular'] == 16358093140
    print(json.dumps({'status': 'PASS_ARCHIVE_VERIFICATION', 'candidate_id': None,
                      'n131_rows': 2, 'sage_slice_values': 16384}, sort_keys=True))


if __name__ == '__main__':
    main()
