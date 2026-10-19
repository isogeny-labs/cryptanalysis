"""Read-only replay of the frozen N41 block Macaulay receipts."""
import hashlib
import json
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
    protocol = load('protocol.json')
    receipt = load('receipt.json')
    result = load('result.json')
    audit_protocol = load('audit_protocol.json')
    audit_receipt = load('audit_receipt.json')
    audit = load('audit_result.json')
    check_sources(protocol)
    check_sources(audit_protocol)
    assert protocol['status'] == 'FROZEN_BEFORE_N41_W11_BLOCK_MACAULAY'
    assert audit_protocol['status'] == 'FROZEN_BEFORE_N41_W11_BLOCK_SAGE_AUDIT'
    assert protocol['worker_count'] == audit_protocol['worker_count'] == 1
    assert protocol['rss_cap_bytes'] == audit_protocol['rss_cap_bytes'] == 4294967296
    for row, source, name in [(receipt, result, 'run'),
                              (audit_receipt, audit, 'audit')]:
        assert row['status'] == 'COMPLETE' and row['exit_code'] == 0
        assert row['stop_reason'] is None and row['wall_seconds'] < 180
        assert row['sampled_peak_combined_rss_bytes'] < 4294967296
        assert row['result_sha256'] == sha(HERE / ('result.json' if name == 'run' else 'audit_result.json'))
        assert row['stdout_sha256'] == sha(HERE / (name + '.stdout'))
        assert row['stderr_sha256'] == sha(HERE / (name + '.stderr'))
    assert receipt['protocol_sha256'] == sha(HERE / 'protocol.json')
    assert audit_receipt['protocol_sha256'] == sha(HERE / 'audit_protocol.json')
    assert result['status'] == 'COMPLETE_N41_W11_BLOCK_MACAULAY'
    assert result['protocol_sha256'] == sha(HERE / 'protocol.json')
    assert result['script_sha256'] == sha(HERE / 'run.py')
    assert audit['status'] == 'PASS_N41_W11_BLOCK_SAGE_AUDIT'
    assert audit['protocol_sha256'] == sha(HERE / 'audit_protocol.json')
    assert audit['script_sha256'] == sha(HERE / 'audit_sage.py')
    assert audit['run_sha256'] == sha(HERE / 'result.json')
    assert audit['cells_checked'] == len(result['results']) == 6
    assert audit['certificates_checked'] == 5
    assert audit['truth_table_values'] == 24576
    assert [(x['target_index'], x['anchor']) for x in result['results']] == [
        (0, 0), (0, 252), (0, 512), (1, 0), (1, 252), (1, 512)]
    for producer, checked in zip(result['results'], audit['checks']):
        assert producer['target_index'] == checked['target_index']
        assert producer['anchor'] == checked['anchor']
        assert producer['roots'] == checked['roots']
        assert producer['anf_terms'] == checked['anf_terms']
        assert producer['anf_degree'] == 4
        assert checked['certificates_checked'] == sum(x['reject'] for x in producer['levels'])
        assert [x['degree'] for x in producer['levels']] == [4, 5, 6]
        assert not any(x['reject'] for x in producer['levels'][:2])
        assert producer['levels'][-1]['reject'] == ((producer['target_index'], producer['anchor']) != (0, 252))
    assert result['results'][1]['roots'] == [[253, 63]]
    assert not any(x['roots'] for i, x in enumerate(result['results']) if i != 1)
    old_receipt = load('audit_receipt_attempt1.json')
    old_audit = load('audit_result_attempt1.json')
    assert old_receipt['status'] == 'MONITOR_FAILURE' and old_receipt['exit_code'] == 0
    assert old_audit['checks'] == audit['checks']
    lean = (HERE / 'lean.stdout').read_text()
    assert not (HERE / 'lean.stderr').read_text()
    assert 'error:' not in lean and 'sorryAx' not in lean
    assert "'BlockCertificate.constant_one_block_certificate_sound' depends on axioms: [propext, Classical.choice, Quot.sound]" in lean
    print(json.dumps({'status': 'PASS_ARCHIVE_VERIFICATION', 'candidate_id': None,
                      'cells': 6, 'rejected_blocks': 5}, sort_keys=True))


if __name__ == '__main__':
    main()
