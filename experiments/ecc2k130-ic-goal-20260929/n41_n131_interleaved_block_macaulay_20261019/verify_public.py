"""Read-only replay of the public N131 constant-one block certificate."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
BASE = ROOT / 'n41_n131_sparse_block_macaulay_20261019'
SOURCE = ROOT / 'n131_w33_freecode_resultant_20261018'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path):
    return json.loads(Path(path).read_text())


def equations(path):
    with Path(path).open() as stream:
        assert stream.readline().split() == ['EQS', '34', '131', '4', '2']
        rows = []
        for bit in range(131):
            line = [int(x) for x in stream.readline().split()]
            assert line[0] == bit and line[1] == len(line) - 2
            assert line[2:] == sorted(set(line[2:]))
            assert all(mask < 1 << 34 and mask.bit_count() <= 4
                       for mask in line[2:])
            rows.append(line[2:])
        assert not stream.read().strip()
    return rows


def evaluate(rows, assignment):
    return [bit for bit, row in enumerate(rows)
            if sum(1 for mask in row if mask & assignment == mask) & 1]


def main():
    cfg = load(HERE / 'query_protocol_n131_public.json')
    summary = load(HERE / 'query_result_n131_public.json')
    receipt = load(HERE / 'n131_t1_a0.receipt.json')
    witness_cfg = load(HERE / 'witness_protocol.json')
    witness = load(HERE / 'witness_result.json')
    audit_cfg = load(BASE / 'audit_protocol.json')
    audit = load(BASE / 'audit_result.json')
    audit_receipt = load(BASE / 'audit_receipt.json')
    source = load(SOURCE / 'coefficients.json')

    assert cfg['status'] == 'FROZEN_BEFORE_N131_PUBLIC_BLOCK'
    assert cfg['row_order'] == 'multiplier_then_field_coordinate'
    assert cfg['worker_count'] == 1 and cfg['wall_cap_seconds'] == 590
    assert cfg['rss_cap_bytes'] == 4294967296
    assert cfg['labels'] == ['n131_t1_a0'] and cfg['candidate_id'] is None
    assert sha(HERE / 'supervise_public.py') == cfg['public_supervisor_sha256']
    assert sha(HERE / 'supervise.py') == cfg['supervisor_sha256']
    assert sha(cfg['binary']['path']) == cfg['binary']['sha256']
    for rec in [*cfg['inputs'].values(), *cfg['dependencies'].values()]:
        assert sha(rec['path']) == rec['sha256']
    assert source['curve_id'] == cfg['curve_id']
    assert source['rows'][1]['name'] == 'frozen_public_raw_point'
    assert source['rows'][1]['point'] == [
        877610862732227974378969808549299291499,
        2063336771837286479337213121437715536874]
    assert audit_cfg['sources']['n131_coefficients']['sha256'] == sha(
        SOURCE / 'coefficients.json')
    for rec in audit_cfg['sources'].values():
        assert sha(rec['path']) == rec['sha256']
    assert audit['status'] == 'PASS_SPARSE_INPUT_SAGE_AUDIT'
    assert audit['protocol_sha256'] == sha(BASE / 'audit_protocol.json')
    assert audit_receipt['status'] == 'COMPLETE' and audit_receipt['exit_code'] == 0
    assert audit_receipt['result_sha256'] == sha(BASE / 'audit_result.json')
    assert witness_cfg['status'] == 'FROZEN_BEFORE_N131_WITNESS_GATE'
    assert sha(HERE / 'witness_gate.py') == witness_cfg['script_sha256']
    for rec in witness_cfg['dependencies'].values():
        assert sha(rec['path']) == rec['sha256']
    assert witness['status'] == 'PASS_N131_POSITIVE_WITNESS'
    assert witness['protocol_sha256'] == sha(HERE / 'witness_protocol.json')
    assert witness['script_sha256'] == sha(HERE / 'witness_gate.py')
    assert witness['field_coordinates_checked'] == 131
    assert witness['witness'] == {'left_code': 3, 'right_code': 16722}
    positive = equations(witness_cfg['positive_equations']['path'])
    assert sha(witness_cfg['positive_equations']['path']) == witness_cfg[
        'positive_equations']['sha256']
    assert evaluate(positive, 3 | (16722 << 2)) == []
    n41 = load(HERE / 'query_result_n41.json')
    assert n41['status'] == 'COMPLETE_PANEL'
    assert n41['statuses'].count('REJECT_CERTIFICATE') == 5
    assert n41['statuses'].count('UNRESOLVED_AT_DEGREE6') == 1
    assert load(HERE / 'verify_n41.stdout')['status'] == 'PASS_N41_INTERLEAVED_GATE'

    assert summary['status'] == 'COMPLETE_PUBLIC_BLOCK'
    assert summary['block_status'] == 'REJECT_CERTIFICATE'
    assert summary['label'] == 'n131_t1_a0'
    assert summary['protocol_sha256'] == sha(HERE / 'query_protocol_n131_public.json')
    assert summary['public_supervisor_sha256'] == sha(HERE / 'supervise_public.py')
    assert receipt['status'] == 'REJECT_CERTIFICATE'
    assert receipt['exit_code'] == 0 and receipt['stop_reason'] is None
    assert 0 < receipt['wall_seconds'] < 590
    assert 0 < receipt['sampled_peak_combined_rss_bytes'] < 4294967296
    assert receipt['protocol_sha256'] == sha(HERE / 'query_protocol_n131_public.json')
    assert receipt['supervisor_sha256'] == sha(HERE / 'supervise.py')
    assert receipt['input_sha256'] == cfg['inputs']['n131_t1_a0']['sha256']
    assert receipt['binary_sha256'] == cfg['binary']['sha256']
    stdout = HERE / 'n131_t1_a0.stdout'
    stderr = HERE / 'n131_t1_a0.stderr'
    assert receipt['stdout_sha256'] == sha(stdout)
    assert receipt['stderr_sha256'] == sha(stderr)
    lines = stdout.read_text().splitlines()
    terminal = [line for line in lines if line.startswith('REJECT_CERTIFICATE ')]
    certs = [line for line in lines if line.startswith('CERT_ROWS')]
    assert len(terminal) == len(certs) == 1
    _, processed, rank, reductions, count, internal_seconds, raw_peak = (
        terminal[0].split())
    processed, rank, reductions, count, raw_peak = map(
        int, (processed, rank, reductions, count, raw_peak))
    assert 0 < processed <= 78076 and 0 < rank <= processed
    assert reductions >= 0 and 0 < count <= processed
    assert 0 < float(internal_seconds) < receipt['wall_seconds']
    assert raw_peak <= receipt['sampled_peak_combined_rss_bytes']
    pairs = [tuple(map(int, item.split(':'))) for item in certs[0].split()[1:]]
    assert len(pairs) == count and len(set(pairs)) == count
    rows = equations(cfg['inputs']['n131_t1_a0']['path'])
    parity = set()
    for bit, factor in pairs:
        assert 0 <= bit < 131 and 0 <= factor < 1 << 34
        assert factor.bit_count() <= 2
        for monomial in rows[bit]:
            value = monomial | factor
            if value in parity:
                parity.remove(value)
            else:
                parity.add(value)
    assert parity == {0}
    result = {'status': 'PASS_N131_PUBLIC_BLOCK_CERTIFICATE_REPLAY',
              'candidate_id': None, 'curve_id': cfg['curve_id'],
              'block_status': receipt['status'], 'rows_processed': processed,
              'rank_at_certificate': rank, 'row_reductions': reductions,
              'certificate_rows': count, 'xor_support': [0],
              'parent_wall_seconds': receipt['wall_seconds'],
              'sampled_peak_combined_rss_bytes': receipt[
                  'sampled_peak_combined_rss_bytes'],
              'protocol_sha256': sha(HERE / 'query_protocol_n131_public.json'),
              'receipt_sha256': sha(HERE / 'n131_t1_a0.receipt.json'),
              'stdout_sha256': sha(stdout), 'script_sha256': sha(__file__)}
    (HERE / 'verification_result.json').write_text(
        json.dumps(result, sort_keys=True, indent=2) + '\n')
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
