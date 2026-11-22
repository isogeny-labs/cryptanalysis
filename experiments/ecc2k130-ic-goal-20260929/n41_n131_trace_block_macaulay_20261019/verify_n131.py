"""Read-only verification of frozen N131 sparse degree-six outcomes."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path):
    return json.loads(Path(path).read_text())


def equations(path):
    with Path(path).open() as stream:
        assert stream.readline().split() == ['EQS', '34', '131', '4', '2']
        rows = []
        for bit in range(131):
            row = [int(x) for x in stream.readline().split()]
            assert row[0] == bit and row[1] == len(row) - 2
            assert row[2:] == sorted(set(row[2:]))
            rows.append(row[2:])
        assert not stream.read().strip()
    return rows


def replay_certificate(lines, eq):
    terminal = [line for line in lines if line.startswith('REJECT_CERTIFICATE ')]
    certificates = [line for line in lines if line.startswith('CERT_ROWS')]
    assert len(terminal) == len(certificates) == 1
    pairs = certificates[0].split()[1:]
    assert len(pairs) == int(terminal[0].split()[4])
    parity = set()
    for pair in pairs:
        bit, factor = map(int, pair.split(':'))
        assert 0 <= bit < 131 and 0 <= factor < 1 << 34
        assert factor.bit_count() <= 2
        for monomial in eq[bit]:
            value = monomial | factor
            if value in parity:
                parity.remove(value)
            else:
                parity.add(value)
    assert parity == {0}
    return len(pairs)


def main():
    cfg = load(HERE / 'query_protocol_n131.json')
    result = load(HERE / 'query_result_n131.json')
    prep = load(HERE.parent / 'n41_n131_sparse_block_macaulay_20261019' / 'prepare_result.json')
    audit = load(HERE.parent / 'n41_n131_sparse_block_macaulay_20261019' / 'audit_result.json')
    audit_receipt = load(HERE.parent / 'n41_n131_sparse_block_macaulay_20261019' / 'audit_receipt.json')
    assert cfg['status'] == 'FROZEN_BEFORE_SPARSE_BLOCK_N131'
    assert cfg['curve_id'] == 'EC1N131Ckb1heb5f1998f20b'
    assert cfg['worker_count'] == 1 and cfg['wall_cap_seconds'] == 590
    assert cfg['rss_cap_bytes'] == 4294967296
    assert sha(HERE / 'supervise.py') == cfg['supervisor_sha256']
    assert sha(cfg['binary']['path']) == cfg['binary']['sha256']
    for item in [*cfg['inputs'].values(), *cfg['dependencies'].values()]:
        assert sha(item['path']) == item['sha256']
    assert prep['status'] == 'PASS_SPARSE_BLOCK_PREPARATION'
    assert audit['status'] == 'PASS_SPARSE_INPUT_SAGE_AUDIT'
    assert len(audit['checks']) == 8
    assert audit_receipt['status'] == 'COMPLETE' and audit_receipt['exit_code'] == 0
    assert audit_receipt['result_sha256'] == sha(HERE.parent / 'n41_n131_sparse_block_macaulay_20261019' / 'audit_result.json')
    assert result['protocol_sha256'] == sha(HERE / 'query_protocol_n131.json')
    assert result['supervisor_sha256'] == sha(HERE / 'supervise.py')
    assert result['labels_executed'] == cfg['labels'][:len(result['labels_executed'])]
    assert result['statuses'] and len(result['statuses']) == len(result['labels_executed'])
    assert result['status'] == ('COMPLETE_PANEL' if len(result['labels_executed']) == 2
                                 else 'PARTIAL_PANEL')
    for index, label in enumerate(result['labels_executed']):
        receipt = load(HERE / (label + '.receipt.json'))
        stdout = HERE / (label + '.stdout')
        stderr = HERE / (label + '.stderr')
        assert receipt['label'] == label and receipt['status'] == result['statuses'][index]
        assert receipt['protocol_sha256'] == sha(HERE / 'query_protocol_n131.json')
        assert receipt['supervisor_sha256'] == sha(HERE / 'supervise.py')
        assert receipt['input_sha256'] == sha(cfg['inputs'][label]['path'])
        assert receipt['binary_sha256'] == cfg['binary']['sha256']
        assert receipt['stdout_sha256'] == sha(stdout)
        assert receipt['stderr_sha256'] == sha(stderr)
        lines = stdout.read_text().splitlines()
        if receipt['status'] == 'REJECT_CERTIFICATE':
            assert index == 1
            assert receipt['stop_reason'] is None and receipt['exit_code'] == 0
            assert replay_certificate(lines, equations(cfg['inputs'][label]['path'])) > 0
        elif receipt['status'] == 'UNRESOLVED_AT_DEGREE6':
            assert receipt['stop_reason'] is None and receipt['exit_code'] == 0
            assert len([line for line in lines if line.startswith('UNRESOLVED_AT_DEGREE6 ')]) == 1
        else:
            assert receipt['status'] in ('WALL_CAP', 'RSS_CAP')
            assert receipt['stop_reason'] == receipt['status']
            assert receipt['exit_code'] != 0
            assert not any(line.startswith('REJECT_CERTIFICATE ') or
                           line.startswith('UNRESOLVED_AT_DEGREE6 ') for line in lines)
            if receipt['status'] == 'WALL_CAP':
                assert 590 <= receipt['wall_seconds'] <= 591
            else:
                assert receipt['sampled_peak_combined_rss_bytes'] > 4294967296
        if receipt['status'] != 'RSS_CAP':
            assert receipt['sampled_peak_combined_rss_bytes'] <= 4294967296
    assert result['statuses'][0] != 'REJECT_CERTIFICATE'
    if result['statuses'][0] != 'UNRESOLVED_AT_DEGREE6':
        assert result['labels_executed'] == [cfg['labels'][0]]
    print(json.dumps({'status': 'PASS_N131_TRACE_ARCHIVE_VERIFICATION',
                      'candidate_id': None, 'executed': result['labels_executed'],
                      'statuses': result['statuses']}, sort_keys=True))


if __name__ == '__main__':
    main()
