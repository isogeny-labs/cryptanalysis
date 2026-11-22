"""Replay the frozen full W29 source census boundary and its Sage overlap."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
PRIOR=ROOT/'n41_n131_implicit_pair_output_20261019'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def load(path):return json.loads(Path(path).read_text())


def limb(value):
    parts=json.loads(value)
    assert len(parts)==3 and all(0<=x<1<<64 for x in parts)
    return parts[0] | parts[1]<<64 | parts[2]<<128


def main():
    cfg=load(HERE/'query_protocol_n131_full.json')
    receipt=load(HERE/'n131_full.receipt.json')
    assert cfg['status']=='FROZEN_BEFORE_NATIVE_PAIR_SOURCE_N131_FULL'
    assert cfg['worker_count']==1 and cfg['wall_cap_seconds']==590
    assert cfg['rss_cap_bytes']==4294967296 and cfg['candidate_id'] is None
    assert sha(HERE/'supervise_full.py')==cfg['supervisor_sha256']
    for rec in [cfg['binary'],cfg['input'],*cfg['dependencies'].values()]:
        assert sha(rec['path'])==rec['sha256']
    full=(HERE/'source_n131_full.txt').read_text().splitlines()
    prefix=(HERE/'source_n131.txt').read_text().splitlines()
    a,b=full[0].split(),prefix[0].split()
    assert a[:6]==b[:6] and a[7:]==b[7:]
    assert a[6]==str(1<<28) and b[6]==str(1<<20)
    assert full[1:]==prefix[1:]
    assert receipt['protocol_sha256']==sha(HERE/'query_protocol_n131_full.json')
    assert receipt['stdout_sha256']==sha(HERE/'n131_full.stdout')
    assert receipt['stderr_sha256']==sha(HERE/'n131_full.stderr')
    assert receipt['sampled_peak_combined_rss_bytes']<4294967296
    lines=(HERE/'n131_full.stdout').read_text().splitlines()
    final=[line.split() for line in lines if line.startswith('RESULT ')]
    trace=[line.split() for line in lines if line.startswith('TRACE ')]
    assert len(final)==len(trace)==1 and limb(trace[0][1])==(1|(1<<129))
    assert final[0][2:5]==['131','28',str(1<<28)]
    sage=[]
    ref=(PRIOR/'terminal_n131.txt').read_text().splitlines()
    d=int(ref[0].split()[2])
    for line in ref[1+d:]:
        c,code=map(int,line.split());sage.append((c,code))
    found=[]
    for line in lines:
        if not line.startswith('PREFIX '):continue
        _,code,c0,c1=line.split()
        found.extend([(limb(c0),int(code)),(limb(c1),int(code))])
    assert len(found)==len(sage)==2128 and sorted(found)==sorted(sage)
    complete=receipt['status']=='COMPLETE' and final[0][1]=='COMPLETE'
    if complete:
        assert receipt['exit_code']==0 and receipt['stop_reason'] is None
        valid,outputs,fail,batches=map(int,final[0][5:9])
        assert outputs==2*valid and fail==0 and batches==2*(1<<16)
        assert int(final[0][9])/1e9<590
        status='PASS_FULL_W29_SOURCE_CENSUS_ARCHIVE'
    else:
        assert receipt['status'] in ('WALL_CAP','WORKER_WALL_CAP','RSS_CAP')
        valid=outputs=None
        status='PASS_FULL_W29_SOURCE_CENSORED_ARCHIVE'
    result={'status':status,'candidate_id':None,'curve_id':cfg['curve_id'],
            'source_codes_declared':1<<28,'valid_codes_reported':valid,
            'outputs_reported':outputs,'sage_prefix_outputs_replayed':len(found),
            'native_wall_seconds':int(final[0][9])/1e9,
            'parent_wall_seconds':receipt['wall_seconds'],
            'sampled_peak_combined_rss_bytes':receipt['sampled_peak_combined_rss_bytes'],
            'protocol_sha256':sha(HERE/'query_protocol_n131_full.json'),
            'receipt_sha256':sha(HERE/'n131_full.receipt.json'),
            'stdout_sha256':sha(HERE/'n131_full.stdout'),
            'script_sha256':sha(__file__)}
    (HERE/'full_audit_result.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps(result,sort_keys=True))


if __name__=='__main__':main()
