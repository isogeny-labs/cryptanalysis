"""Read-only archive check for the wide-eight N41 degree-six boundary."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


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


def main():
    prep = load(HERE / 'prepare_result.json')
    audit_cfg = load(HERE / 'audit_protocol.json')
    audit = load(HERE / 'audit_result.json')
    audit_receipt = load(HERE / 'audit_receipt.json')
    cfg = load(HERE / 'query_protocol_n41.json')
    panel = load(HERE / 'query_result_n41.json')
    assert prep['status'] == 'PASS_WIDE8_PREPARATION'
    assert audit_cfg['status'] == 'FROZEN_BEFORE_WIDE8_INPUT_SAGE_AUDIT'
    for rec in audit_cfg['sources'].values():
        assert sha(rec['path']) == rec['sha256']
    assert audit['status'] == 'PASS_WIDE8_INPUT_SAGE_AUDIT'
    assert audit['protocol_sha256'] == sha(HERE / 'audit_protocol.json')
    assert len(audit['checks']) == 4
    assert audit_receipt['status'] == 'COMPLETE' and audit_receipt['exit_code'] == 0
    assert audit_receipt['result_sha256'] == sha(HERE / 'audit_result.json')
    assert cfg['status'] == 'FROZEN_BEFORE_SPARSE_BLOCK_N41'
    assert cfg['left_free_bits'] == 8 and cfg['row_order'] == 'multiplier_then_field_coordinate'
    assert cfg['worker_count'] == 1 and cfg['wall_cap_seconds'] == 180
    assert cfg['rss_cap_bytes'] == 4294967296
    assert sha(HERE / 'supervise.py') == cfg['supervisor_sha256']
    assert sha(cfg['binary']['path']) == cfg['binary']['sha256']
    for rec in [*cfg['dependencies'].values(), *cfg['inputs'].values()]:
        assert sha(rec['path']) == rec['sha256']
    assert panel['status'] == 'COMPLETE_PANEL'
    assert panel['labels_executed'] == cfg['labels']
    assert panel['statuses'] == ['UNRESOLVED_AT_DEGREE6'] * 2
    assert panel['protocol_sha256'] == sha(HERE / 'query_protocol_n41.json')
    for label in cfg['labels']:
        receipt = load(HERE / (label + '.receipt.json'))
        stdout = HERE / (label + '.stdout')
        stderr = HERE / (label + '.stderr')
        assert receipt['label'] == label and receipt['status'] == 'UNRESOLVED_AT_DEGREE6'
        assert receipt['exit_code'] == 0 and receipt['stop_reason'] is None
        assert 0 < receipt['wall_seconds'] < 180
        assert 0 < receipt['sampled_peak_combined_rss_bytes'] < 4294967296
        assert receipt['protocol_sha256'] == sha(HERE / 'query_protocol_n41.json')
        assert receipt['supervisor_sha256'] == sha(HERE / 'supervise.py')
        assert receipt['input_sha256'] == cfg['inputs'][label]['sha256']
        assert receipt['binary_sha256'] == cfg['binary']['sha256']
        assert receipt['stdout_sha256'] == sha(stdout)
        assert receipt['stderr_sha256'] == sha(stderr)
        lines = stdout.read_text().splitlines()
        assert not any(line.startswith(('REJECT_CERTIFICATE ', 'CERT_ROWS')) for line in lines)
        terminal = [line for line in lines if line.startswith('UNRESOLVED_AT_DEGREE6 ')]
        assert len(terminal) == 1
        assert terminal[0].split()[1:3] == ['7052', '7052']
    positive = equations(cfg['inputs']['n41_t0_a0_w8']['path'], 18, 41)
    assignment = 253 | (63 << 8)
    assert all(sum(1 for monomial in row if monomial & assignment == monomial) % 2 == 0
               for row in positive)
    result = {'status': 'PASS_WIDE8_N41_BOUNDARY_ARCHIVE', 'candidate_id': None,
              'positive_block_status': 'UNRESOLVED_AT_DEGREE6',
              'ordinary_block_status': 'UNRESOLVED_AT_DEGREE6',
              'positive_coordinates_checked': 41,
              'rows_processed_per_cell': 7052,
              'n131_query_launched': False,
              'protocol_sha256': sha(HERE / 'query_protocol_n41.json'),
              'audit_result_sha256': sha(HERE / 'audit_result.json'),
              'script_sha256': sha(__file__)}
    (HERE / 'verification_result.json').write_text(
        json.dumps(result, sort_keys=True, indent=2) + '\n')
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
