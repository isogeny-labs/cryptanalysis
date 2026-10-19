"""Run the second width-two public case under the composite 600-second cap."""
import hashlib
import json
from pathlib import Path

from supervise import one_query

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PRIOR = ROOT / 'n41_n131_interleaved_block_macaulay_20261019'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    name = 'query_protocol_n131_public.json'
    cfg = json.loads((HERE / name).read_text())
    assert cfg['status'] == 'FROZEN_BEFORE_SPLIT_N131_PUBLIC'
    assert cfg['protocol_name'] == name and cfg['labels'] == ['n131_t1_a4']
    assert cfg['worker_count'] == 1 and cfg['wall_cap_seconds'] == 390
    assert cfg['rss_cap_bytes'] == 4294967296
    assert cfg['prior_target_wall_seconds'] + cfg['wall_cap_seconds'] < 600
    assert sha(__file__) == cfg['public_supervisor_sha256']
    assert sha(HERE / 'supervise.py') == cfg['supervisor_sha256']
    assert sha(cfg['binary']['path']) == cfg['binary']['sha256']
    for rec in [*cfg['inputs'].values(), *cfg['dependencies'].values()]:
        assert sha(rec['path']) == rec['sha256']
    assert json.loads((HERE / 'verification_n41.json').read_text())['status'] == 'PASS_SPLIT_N41_GATE'
    assert json.loads((PRIOR / 'verification_result.json').read_text())['status'] == 'PASS_N131_PUBLIC_BLOCK_CERTIFICATE_REPLAY'
    row = one_query(cfg, 'n131_t1_a4')
    result = {'status': 'COMPLETE_SPLIT_CASE' if row['status'] in
              ('REJECT_CERTIFICATE','UNRESOLVED_AT_DEGREE6') else 'PARTIAL_SPLIT_CASE',
              'candidate_id':None,'curve_id':cfg['curve_id'],'label':row['label'],
              'block_status':row['status'],'prior_target_wall_seconds':cfg['prior_target_wall_seconds'],
              'composite_target_wall_seconds':cfg['prior_target_wall_seconds'] + row['wall_seconds'],
              'protocol_sha256':sha(HERE / name),'public_supervisor_sha256':sha(__file__)}
    (HERE / 'query_result_n131_public.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps(result,sort_keys=True))


if __name__ == '__main__':
    main()
