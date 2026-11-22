"""Monitor the frozen one-worker N131 W20 affine search."""
import hashlib
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import psutil

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
cfg=json.loads((HERE/'affine_protocol.json').read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


for relative,digest in cfg['repo_sha256'].items():
    assert sha(ROOT/relative)==digest, relative
for name,digest in cfg['local_sha256'].items():
    assert sha(HERE/name)==digest, name
assert cfg['worker_count']==1
command=[str(HERE/'affine'),str(ROOT/cfg['support_file'])]
assert command==cfg['command']

started=time.monotonic_ns()
parent=psutil.Process()
peak=0
stop=None
degraded=False
with (HERE/'affine_stdout.txt').open('x') as out,(HERE/'affine_stderr.txt').open('x') as err:
    child=subprocess.Popen(command,stdout=out,stderr=err,start_new_session=True)
    process=psutil.Process(child.pid)
    while child.poll() is None:
        try:
            peak=max(peak,parent.memory_info().rss+process.memory_info().rss)
        except (psutil.NoSuchProcess,psutil.AccessDenied,PermissionError):
            if child.poll() is None:
                degraded=True
        if peak>cfg['rss_cap_bytes']:
            stop='RSS_CAP'
        elif time.monotonic_ns()-started>cfg['wall_cap_seconds']*10**9:
            stop='WALL_CAP'
        if stop:
            os.killpg(child.pid,signal.SIGTERM)
            break
        time.sleep(0.05)
    child.wait()
ended=time.monotonic_ns()
lines=(HERE/'affine_stdout.txt').read_text(errors='replace').splitlines()
source=[line for line in lines if line.startswith('SOURCE ')]
rows=[line for line in lines if line.startswith('TOP_LINE ')]
best=[line for line in lines if line.startswith('BEST_LINE ') or line.startswith('BEST_PLANE ')]
done=[line for line in lines if line.startswith('DONE ')]
stderr=(HERE/'affine_stderr.txt').read_text(errors='replace')
status=('COMPLETE_N131_W20_AFFINE_SEARCH'
        if child.returncode==0 and not stop and not stderr and
           len(source)==1 and len(rows)==64 and len(best)==2 and len(done)==1
        else ('BOUNDED_UNKNOWN' if stop else 'PRODUCER_FAILURE'))
receipt={'status':status,'candidate_id':None,'exit_code':child.returncode,
         'stop_reason':stop,'monitor_degraded':degraded,'wall_ns':ended-started,
         'sampled_peak_combined_rss_bytes':peak,'source_line':source,
         'best_lines':best,'done_line':done,
         'row_count':len(rows),'stdout_sha256':sha(HERE/'affine_stdout.txt'),
         'stderr_sha256':sha(HERE/'affine_stderr.txt'),
         'protocol_sha256':sha(HERE/'affine_protocol.json')}
(HERE/'affine_receipt.json').write_text(json.dumps(receipt,sort_keys=True,indent=2)+'\n')
print(json.dumps({'status':status,'wall_seconds':(ended-started)/1e9,
                  'peak_rss_bytes':peak,'best':best},sort_keys=True),flush=True)
sys.exit(0 if status=='COMPLETE_N131_W20_AFFINE_SEARCH' else 1)
