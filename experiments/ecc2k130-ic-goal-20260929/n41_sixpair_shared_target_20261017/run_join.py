"""Run the frozen exact three-plus-three public-point join under explicit caps."""
import hashlib
import json
import os
import signal
import subprocess
import time
from pathlib import Path

import psutil

HERE=Path(__file__).resolve().parent
record=json.loads((HERE/'join_protocol.json').read_text())
sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
for path,digest in record['sources'].items():
    assert sha(path)==digest,path
start=time.monotonic_ns()
parent=psutil.Process(os.getpid())
peak=0
stop=None
with (HERE/'join.stdout.txt').open('x') as out,(HERE/'join.stderr.txt').open('x') as err:
    child=subprocess.Popen([str(HERE/'join_exact'),str(HERE/'join_input.tsv')],stdout=out,stderr=err,start_new_session=True)
    proc=psutil.Process(child.pid)
    while child.poll() is None:
        try:peak=max(peak,parent.memory_info().rss+proc.memory_info().rss)
        except (psutil.NoSuchProcess,psutil.AccessDenied,PermissionError):pass
        if peak>record['rss_cap_bytes']:stop='RSS_CAP'
        elif time.monotonic_ns()-start>record['wall_cap_seconds']*10**9:stop='WALL_CAP'
        if stop:os.killpg(child.pid,signal.SIGTERM);break
        time.sleep(.1)
    code=child.wait()
lines=(HERE/'join.stdout.txt').read_text().splitlines()
hits=[line for line in lines if line.startswith('HIT ')]
status=('CENSORED_'+stop if stop else
        'PRODUCER_FAILURE' if code or not lines or not lines[0].startswith('CHECK_PASS 960 ') else
        'HIT_PENDING_SAGE_REPLAY' if hits else
        'COMPLETE_RESTRICTED_SOURCE_MISS' if any(line.startswith('MISS_COMPLETE') for line in lines)
        else 'PRODUCER_FAILURE')
result={'status':status,'exit_code':code,'stop_reason':stop,'wall_ns':time.monotonic_ns()-start,
        'sampled_peak_combined_rss_bytes':peak,'hit_lines':hits,
        'phase_lines':[line for line in lines if line.startswith(('CHECK_PASS','LEFT_DONE','MISS_COMPLETE'))],
        'protocol_sha256':sha(HERE/'join_protocol.json'),
        'stdout_sha256':sha(HERE/'join.stdout.txt'),'stderr_sha256':sha(HERE/'join.stderr.txt')}
with (HERE/'join_result.json').open('x') as out:json.dump(result,out,sort_keys=True,indent=2);out.write('\n')
print(status,result['wall_ns']/1e9,hits,flush=True)
