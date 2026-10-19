"""Own one bounded native stream producer or target query."""
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import psutil

HERE=Path(__file__).resolve().parent

def sha(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for chunk in iter(lambda:f.read(8<<20),b''):h.update(chunk)
    return h.hexdigest()

def main():
    label=sys.argv[1]
    cfg=json.loads((HERE/f'{label}.protocol.json').read_text())
    assert cfg['status']=='FROZEN_BEFORE_'+label.upper()
    assert cfg['worker_count']==1 and cfg['wall_cap_seconds']<=600
    assert cfg['rss_cap_bytes']==4294967296
    for record in cfg['inputs'].values():assert sha(record['path'])==record['sha256']
    command=cfg['command']
    out=HERE/f'{label}.stdout';err=HERE/f'{label}.stderr'
    start=time.monotonic();peak=samples=0;stop=None
    parent=psutil.Process(os.getpid())
    with out.open('xb') as stdout,err.open('xb') as stderr:
        child=subprocess.Popen(command,stdout=stdout,stderr=stderr,cwd=HERE,start_new_session=True)
        (HERE/f'{label}.handle.json').write_text(json.dumps({'pid':child.pid,'command':command,
            'started_monotonic':start},sort_keys=True,indent=2)+'\n')
        process=psutil.Process(child.pid)
        while child.poll() is None:
            try:peak=max(peak,parent.memory_info().rss+process.memory_info().rss);samples+=1
            except psutil.NoSuchProcess:
                if child.poll() is not None:break
            if peak>cfg['rss_cap_bytes']:stop='RSS_CAP';break
            if time.monotonic()-start>cfg['wall_cap_seconds']:stop='WALL_CAP';break
            time.sleep(0.05)
        if stop and child.poll() is None:child.terminate()
        code=child.wait()
    lines=out.read_text(errors='replace').splitlines()
    terminal=[line for line in lines if line.startswith(cfg['terminal_prefix'])]
    if stop:status=stop
    elif code!=0:status='PRODUCER_FAILURE'
    elif len(terminal)!=1:status='SCHEMA_INCOMPLETE'
    elif terminal[0].split()[1]=='COMPLETE':status='COMPLETE'
    else:status='BOUNDED_UNKNOWN'
    receipt={'status':status,'candidate_id':None,'label':label,'command':command,
        'exit_code':code,'stop_reason':stop,'wall_seconds':time.monotonic()-start,
        'sampled_peak_combined_rss_bytes':peak,'rss_samples':samples,
        'stdout_sha256':sha(out),'stderr_sha256':sha(err),
        'terminal_line':terminal[0] if len(terminal)==1 else None,
        'protocol_sha256':sha(HERE/f'{label}.protocol.json')}
    if label=='produce' and status=='COMPLETE':
        stream=HERE/'all.bin';receipt['stream_bytes']=stream.stat().st_size
        receipt['stream_sha256']=sha(stream)
    (HERE/f'{label}.receipt.json').write_text(json.dumps(receipt,sort_keys=True,indent=2)+'\n')
    print(json.dumps(receipt,sort_keys=True))

if __name__=='__main__':main()
