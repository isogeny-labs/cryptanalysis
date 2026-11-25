"""Read-only replay of the wide-three N41 certificate and positive gates."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
W3 = HERE.parent / 'n41_n131_wide3_block_macaulay_20261019'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path):
    return json.loads(Path(path).read_text())


def equations(path, variables, field_bits):
    with Path(path).open() as stream:
        assert stream.readline().split() == ['EQS', str(variables), str(field_bits), '4', '2']
        rows = []
        for bit in range(field_bits):
            row = [int(value) for value in stream.readline().split()]
            assert row[0] == bit and row[1] == len(row) - 2
            assert row[2:] == sorted(set(row[2:]))
            rows.append(row[2:])
        assert not stream.read().strip()
    return rows


def evaluate(rows, assignment):
    return [bit for bit, row in enumerate(rows)
            if sum(1 for monomial in row if monomial & assignment == monomial) & 1]


def replay(lines, rows, variables, field_bits):
    terminal = [line for line in lines if line.startswith('REJECT_CERTIFICATE ')]
    cert = [line for line in lines if line.startswith('CERT_ROWS')]
    assert len(terminal) == len(cert) == 1
    pairs = [tuple(map(int, pair.split(':'))) for pair in cert[0].split()[1:]]
    assert len(pairs) == int(terminal[0].split()[4])
    assert len(pairs) == len(set(pairs))
    parity = set()
    for bit, factor in pairs:
        assert 0 <= bit < field_bits and 0 <= factor < 1 << variables
        assert factor.bit_count() <= 2
        for monomial in rows[bit]:
            value = monomial | factor
            if value in parity:
                parity.remove(value)
            else:
                parity.add(value)
    assert parity == {0}
    return len(pairs)


def main():
    prep = load(W3 / 'prepare_result.json')
    audit_cfg = load(W3 / 'audit_protocol.json')
    audit = load(W3 / 'audit_result.json')
    audit_receipt = load(W3 / 'audit_receipt.json')
    cfg = load(HERE / 'query_protocol_n41.json')
    panel = load(HERE / 'query_result_n41.json')
    assert prep['status'] == 'PASS_WIDE3_PREPARATION'
    assert audit_cfg['status'] == 'FROZEN_BEFORE_WIDE3_INPUT_SAGE_AUDIT'
    for rec in audit_cfg['sources'].values():
        assert sha(rec['path']) == rec['sha256']
    assert audit['status'] == 'PASS_WIDE3_INPUT_SAGE_AUDIT'
    assert audit['protocol_sha256'] == sha(W3 / 'audit_protocol.json')
    assert len(audit['checks']) == 4
    assert audit_receipt['status'] == 'COMPLETE' and audit_receipt['exit_code'] == 0
    assert audit_receipt['result_sha256'] == sha(W3 / 'audit_result.json')
    assert cfg['status'] == 'FROZEN_BEFORE_SPARSE_BLOCK_N41'
    assert cfg['left_free_bits'] == 3 and cfg['row_order'] == 'certificate_guided_factor_then_field_coordinate'
    assert cfg['worker_count'] == 1 and cfg['wall_cap_seconds'] == 120
    assert cfg['rss_cap_bytes'] == 4294967296
    assert sha(HERE / 'supervise.py') == cfg['supervisor_sha256']
    assert sha(cfg['binary']['path']) == cfg['binary']['sha256']
    assert sha(cfg['schedule']['path']) == cfg['schedule']['sha256']
    for rec in [*cfg['dependencies'].values(), *cfg['inputs'].values()]:
        assert sha(rec['path']) == rec['sha256']
    assert panel['status'] == 'COMPLETE_PANEL'
    assert panel['labels_executed'] == cfg['labels']
    assert panel['statuses'] == ['UNRESOLVED_AT_DEGREE6', 'REJECT_CERTIFICATE']
    assert panel['protocol_sha256'] == sha(HERE / 'query_protocol_n41.json')
    for label, status in zip(cfg['labels'], panel['statuses']):
        receipt = load(HERE / (label + '.receipt.json'))
        stdout = HERE / (label + '.stdout')
        stderr = HERE / (label + '.stderr')
        assert receipt['label'] == label and receipt['status'] == status
        assert receipt['exit_code'] == 0 and receipt['stop_reason'] is None
        assert 0 < receipt['wall_seconds'] < 120
        assert 0 < receipt['sampled_peak_combined_rss_bytes'] < 4294967296
        assert receipt['protocol_sha256'] == sha(HERE / 'query_protocol_n41.json')
        assert receipt['supervisor_sha256'] == sha(HERE / 'supervise.py')
        assert receipt['input_sha256'] == cfg['inputs'][label]['sha256']
        assert receipt['binary_sha256'] == cfg['binary']['sha256']
        assert receipt['schedule_sha256'] == cfg['schedule']['sha256']
        assert receipt['stdout_sha256'] == sha(stdout)
        assert receipt['stderr_sha256'] == sha(stderr)
    positive = equations(cfg['inputs']['n41_t0_a248_w3']['path'], 13, 41)
    assert evaluate(positive, (253 - 248) | (63 << 3)) == []
    ordinary = equations(cfg['inputs']['n41_t1_a0_w3']['path'], 13, 41)
    count = replay((HERE / 'n41_t1_a0_w3.stdout').read_text().splitlines(),
                   ordinary, 13, 41)
    n131_positive = equations(W3 / 'n131_t0_a0_w3.eqs', 35, 131)
    assert evaluate(n131_positive, 3 | (16722 << 3)) == []
    result = {'status': 'PASS_GUIDED_WIDE3_N41_AND_N131_POSITIVE_GATES',
              'candidate_id': None, 'n41_ordinary_certificate_rows': count,
              'n41_positive_coordinates_checked': 41,
              'n131_positive_coordinates_checked': 131,
              'n41_protocol_sha256': sha(HERE / 'query_protocol_n41.json'),
              'audit_result_sha256': sha(W3 / 'audit_result.json'),
              'script_sha256': sha(__file__)}
    (HERE / 'control_verification.json').write_text(
        json.dumps(result, sort_keys=True, indent=2) + '\n')
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
