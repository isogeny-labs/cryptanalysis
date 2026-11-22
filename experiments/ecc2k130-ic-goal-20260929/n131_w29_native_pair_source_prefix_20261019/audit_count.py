"""Bind the numeric-order W29 count to the full Gray-code source census."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def load(path):return json.loads(Path(path).read_text())


def limb(value):
    parts=json.loads(value)
    assert len(parts)==3 and all(0<=x<1<<64 for x in parts)
    return parts[0] | parts[1]<<64 | parts[2]<<128


def main():
    cfg=load(HERE/'query_protocol_n131_count.json')
    receipt=load(HERE/'n131_count.receipt.json')
    producer=load(HERE/'full_audit_result.json')
    assert cfg['status']=='FROZEN_BEFORE_INDEPENDENT_W29_SOURCE_COUNT'
    assert cfg['worker_count']==1 and cfg['wall_cap_seconds']==590
    assert cfg['rss_cap_bytes']==4294967296 and cfg['candidate_id'] is None
    assert cfg['supervisor_sha256']==sha(HERE/'supervise_count.py')
    for rec in [cfg['binary'],cfg['input'],*cfg['dependencies'].values()]:
        assert sha(rec['path'])==rec['sha256']
    assert receipt['protocol_sha256']==sha(HERE/'query_protocol_n131_count.json')
    assert receipt['stdout_sha256']==sha(HERE/'n131_count.stdout')
    assert receipt['stderr_sha256']==sha(HERE/'n131_count.stderr')
    assert receipt['sampled_peak_combined_rss_bytes']<4294967296
    lines=(HERE/'n131_count.stdout').read_text().splitlines()
    trace=[line.split() for line in lines if line.startswith('TRACE ')]
    final=[line.split() for line in lines if line.startswith('RESULT ')]
    assert len(trace)==len(final)==1
    assert limb(trace[0][1])==(1|(1<<129))
    assert producer['status']=='PASS_FULL_W29_SOURCE_CENSUS_ARCHIVE'
    if receipt['status']=='COMPLETE':
        assert final[0][1]=='COMPLETE' and receipt['exit_code']==0
        checked,valid,batches=map(int,final[0][2:5])
        assert checked==1<<28 and batches==1<<15
        assert valid==producer['valid_codes_reported']
        status='PASS_INDEPENDENT_W29_SOURCE_COUNT'
    else:
        assert receipt['status'] in ('WALL_CAP','WORKER_WALL_CAP','RSS_CAP')
        checked=valid=None
        status='PASS_INDEPENDENT_W29_SOURCE_CENSORED_ARCHIVE'
    result={'status':status,'candidate_id':None,'curve_id':cfg['curve_id'],
            'codes_checked':checked,'valid_codes':valid,
            'producer_valid_codes':producer['valid_codes_reported'],
            'native_wall_seconds':int(final[0][5])/1e9,
            'parent_wall_seconds':receipt['wall_seconds'],
            'sampled_peak_combined_rss_bytes':receipt['sampled_peak_combined_rss_bytes'],
            'protocol_sha256':sha(HERE/'query_protocol_n131_count.json'),
            'receipt_sha256':sha(HERE/'n131_count.receipt.json'),
            'stdout_sha256':sha(HERE/'n131_count.stdout'),
            'script_sha256':sha(__file__)}
    (HERE/'count_audit_result.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps(result,sort_keys=True))


if __name__=='__main__':main()
