"""Read-only N41 sparse-control certificate and resource verification."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path):
    return json.loads(Path(path).read_text())


def equations(path):
    with Path(path).open() as stream:
        header = stream.readline().split()
        assert header == ['EQS', '12', '41', '4', '2']
        rows = []
        for bit in range(41):
            items = [int(x) for x in stream.readline().split()]
            assert items[0] == bit and items[1] == len(items) - 2
            assert items[2:] == sorted(set(items[2:]))
            rows.append(items[2:])
        assert not stream.read().strip()
    return rows


def replay_certificate(stdout, eq):
    terminal = [line for line in stdout if line.startswith('REJECT_CERTIFICATE ')]
    certificates = [line for line in stdout if line.startswith('CERT_ROWS')]
    assert len(terminal) == len(certificates) == 1
    terms = certificates[0].split()[1:]
    assert len(terms) == int(terminal[0].split()[4])
    parity = set()
    for pair in terms:
        bit, factor = map(int, pair.split(':'))
        assert 0 <= bit < 41 and factor < 1 << 12 and factor.bit_count() <= 2
        for monomial in eq[bit]:
            merged = monomial | factor
            if merged in parity:
                parity.remove(merged)
            else:
                parity.add(merged)
    assert parity == {0}
    return len(terms)


def main():
    cfg = load(HERE / 'query_protocol_n41.json')
    summary = load(HERE / 'query_result_n41.json')
    prepared = load(ROOT / 'n41_n131_sparse_block_macaulay_20261019' / 'prepare_result.json')
    prior = load(ROOT / 'n41_w11_block_macaulay_20261019' / 'result.json')
    assert cfg['status'] == 'FROZEN_BEFORE_SPARSE_BLOCK_N41'
    assert cfg['worker_count'] == 1 and cfg['wall_cap_seconds'] == 120
    assert cfg['rss_cap_bytes'] == 4294967296
    assert sha(HERE / 'supervise.py') == cfg['supervisor_sha256']
    assert sha(cfg['binary']['path']) == cfg['binary']['sha256']
    for item in cfg['inputs'].values():
        assert sha(item['path']) == item['sha256']
    for item in cfg['dependencies'].values():
        assert sha(item['path']) == item['sha256']
    assert prepared['status'] == 'PASS_SPARSE_BLOCK_PREPARATION'
    assert summary['status'] == 'COMPLETE_PANEL'
    assert summary['protocol_sha256'] == sha(HERE / 'query_protocol_n41.json')
    assert summary['labels_executed'] == cfg['labels']
    rejected = 0
    for index, label in enumerate(cfg['labels']):
        expected = prior['results'][index]
        assert label == f"n41_t{expected['target_index']}_a{expected['anchor']}"
        receipt = load(HERE / (label + '.receipt.json'))
        stdout_path = HERE / (label + '.stdout')
        stderr_path = HERE / (label + '.stderr')
        assert receipt['status'] in ('REJECT_CERTIFICATE', 'UNRESOLVED_AT_DEGREE6')
        assert receipt['exit_code'] == 0 and receipt['stop_reason'] is None
        assert receipt['wall_seconds'] < 120
        assert 0 < receipt['sampled_peak_combined_rss_bytes'] < 4294967296
        assert receipt['stdout_sha256'] == sha(stdout_path)
        assert receipt['stderr_sha256'] == sha(stderr_path)
        assert receipt['input_sha256'] == sha(cfg['inputs'][label]['path'])
        assert receipt['binary_sha256'] == cfg['binary']['sha256']
        assert receipt['protocol_sha256'] == sha(HERE / 'query_protocol_n41.json')
        assert receipt['supervisor_sha256'] == sha(HERE / 'supervise.py')
        lines = stdout_path.read_text().splitlines()
        if expected['levels'][-1]['reject']:
            assert receipt['status'] == 'REJECT_CERTIFICATE'
            assert replay_certificate(lines, equations(cfg['inputs'][label]['path'])) > 0
            rejected += 1
        else:
            assert receipt['status'] == 'UNRESOLVED_AT_DEGREE6'
            assert expected['roots'] == [[253, 63]]
            assert len([x for x in lines if x.startswith('UNRESOLVED_AT_DEGREE6 ')]) == 1
        assert summary['statuses'][index] == receipt['status']
    assert rejected == 5
    print(json.dumps({'status': 'PASS_N41_INTERLEAVED_GATE', 'candidate_id': None,
                      'rejected_blocks': rejected, 'retained_public_relation_blocks': 1},
                     sort_keys=True))


if __name__ == '__main__':
    main()
