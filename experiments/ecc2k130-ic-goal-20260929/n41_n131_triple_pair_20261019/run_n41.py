"""Own the bounded, unpinned triple-pair N41 public-point join."""
import hashlib
import json
import os
import subprocess
import time
from pathlib import Path

import psutil

HERE=Path(__file__).resolve().parent
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def main():
    cfg=json.loads((HERE/'n41_query_protocol.json').read_text())
    assert cfg['status']=='FROZEN_BEFORE_TRIPLE_PAIR_N41_PUBLIC_QUERY'
    assert cfg['worker_count']==1 and cfg['wall_cap_seconds']==600
    assert cfg['rss_cap_bytes']==4294967296
    assert cfg['script_sha256']==sha(__file__)
    for rec in cfg['sources'].values():assert sha(rec['path'])==rec['sha256']
    command=[cfg['join_binary']['path'],cfg['join_input']['path'],
             str(cfg['query_seed']),str(cfg['max_probes'])]
    started=time.monotonic();peak=samples=0;stop=None
    parent=psutil.Process(os.getpid())
    with (HERE/'n41_join.stdout').open('xb') as out,(HERE/'n41_join.stderr').open('xb') as err:
        child=subprocess.Popen(command,stdout=out,stderr=err,cwd=HERE,start_new_session=True)
        (HERE/'n41_join.handle.json').write_text(json.dumps({'pid':child.pid,'command':command,
            'started_monotonic':started},sort_keys=True,indent=2)+'\n')
        process=psutil.Process(child.pid)
        while child.poll() is None:
            try:peak=max(peak,parent.memory_info().rss+process.memory_info().rss);samples+=1
            except psutil.NoSuchProcess:
                if child.poll() is not None:break
            if peak>cfg['rss_cap_bytes']:stop='RSS_CAP';break
            if time.monotonic()-started>cfg['wall_cap_seconds']:stop='WALL_CAP';break
            time.sleep(0.02)
        if stop and child.poll() is None:child.terminate()
        code=child.wait()
    lines=(HERE/'n41_join.stdout').read_text().splitlines()
    hits=[line for line in lines if line.startswith('HIT ')]
    status=(stop or ('PRODUCER_FAILURE' if code else
                   'COMPLETE_HIT' if len(hits)==1 else
                   'COMPLETE_NO_HIT' if any(line.startswith('NO_HIT ') for line in lines)
                   else 'SCHEMA_INCOMPLETE'))
    result={'status':status,'candidate_id':None,'exit_code':code,'stop_reason':stop,
            'command':command,'parent_wall_seconds':time.monotonic()-started,
            'sampled_peak_combined_rss_bytes':peak,'rss_samples':samples,
            'hit':hits[0] if len(hits)==1 else None,
            'stdout_sha256':sha(HERE/'n41_join.stdout'),
            'stderr_sha256':sha(HERE/'n41_join.stderr'),
            'protocol_sha256':sha(HERE/'n41_query_protocol.json')}
    (HERE/'n41_join_result.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps(result,sort_keys=True))

if __name__=='__main__':main()
