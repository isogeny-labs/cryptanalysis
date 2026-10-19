"""One bounded public N131 block query after frozen N41 and witness gates."""
import hashlib
import json
from pathlib import Path

from supervise import one_query

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    name = 'query_protocol_n131_public.json'
    cfg = json.loads((HERE / name).read_text())
    assert cfg['status'] == 'FROZEN_BEFORE_N131_PUBLIC_BLOCK'
    assert cfg['protocol_name'] == name
    assert cfg['labels'] == ['n131_t1_a0_w4']
    assert cfg['worker_count'] == 1
    assert cfg['wall_cap_seconds'] == 590
    assert cfg['rss_cap_bytes'] == 4294967296
    assert sha(__file__) == cfg['public_supervisor_sha256']
    assert sha(HERE / 'supervise.py') == cfg['supervisor_sha256']
    assert sha(cfg['binary']['path']) == cfg['binary']['sha256']
    for rec in cfg['dependencies'].values():
        assert sha(rec['path']) == rec['sha256']
    for rec in cfg['inputs'].values():
        assert sha(rec['path']) == rec['sha256']
    witness = json.loads((HERE / 'control_verification.json').read_text())
    assert witness['status'] == 'PASS_WIDE4_N41_AND_N131_POSITIVE_GATES'
    n41 = json.loads((HERE / 'query_result_n41.json').read_text())
    assert n41['status'] == 'COMPLETE_PANEL'
    assert n41['statuses'].count('REJECT_CERTIFICATE') == 1
    assert n41['statuses'].count('UNRESOLVED_AT_DEGREE6') == 1
    row = one_query(cfg, cfg['labels'][0])
    terminal = row['status'] in ('REJECT_CERTIFICATE', 'UNRESOLVED_AT_DEGREE6')
    summary = {'status': 'COMPLETE_PUBLIC_BLOCK' if terminal else 'PARTIAL_PUBLIC_BLOCK',
               'candidate_id': None, 'curve_id': cfg['curve_id'],
               'label': row['label'], 'block_status': row['status'],
               'protocol_sha256': sha(HERE / name),
               'public_supervisor_sha256': sha(__file__)}
    (HERE / 'query_result_n131_public.json').write_text(
        json.dumps(summary, sort_keys=True, indent=2) + '\n')
    print(json.dumps(summary, sort_keys=True))


if __name__ == '__main__':
    main()
