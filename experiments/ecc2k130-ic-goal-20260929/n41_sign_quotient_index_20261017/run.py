"""Compile receipt and one-worker cap for the sign quotient index."""
import hashlib
import json
import os
import psutil
import signal
import subprocess
import time
from pathlib import Path

D=Path(__file__).resolve().parent


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


p=json.loads((D/'protocol.json').read_text())
assert sha(D/'sign_join.cpp')==p['source_sha256']
assert sha(D/'run.py')==p['runner_sha256']
assert sha(D.parent/'n41_sixpair_shared_target_20261017'/'join_exact.cpp')==p['included_source_sha256']
assert sha(Path(p['input_path']))==p['input_sha256']
compile_result=subprocess.run(p['compile_command'],cwd=D,capture_output=True)
(D/'compile.stdout').write_bytes(compile_result.stdout)
(D/'compile.stderr').write_bytes(compile_result.stderr)
assert compile_result.returncode==0,compile_result.stderr.decode(errors='replace')
binary=D/'sign_join'
binary_sha=sha(binary)
command=[str(binary),p['input_path']]
parent=psutil.Process(os.getpid())
start=time.monotonic()
peak=0;stop=None;degraded=False
with (D/'run.stdout').open('x') as out,(D/'run.stderr').open('x') as err:
    child=subprocess.Popen(command,stdout=out,stderr=err,start_new_session=True)
    process=psutil.Process(child.pid)
    while child.poll() is None:
        try:peak=max(peak,parent.memory_info().rss+process.memory_info().rss)
        except (psutil.NoSuchProcess,psutil.AccessDenied,PermissionError):
            if child.poll() is None:degraded=True
        if peak>p['rss_cap_bytes']:stop='RSS_CAP'
        elif time.monotonic()-start>p['wall_cap_s']:stop='PARENT_WALL_CAP'
        if stop:
            os.killpg(child.pid,signal.SIGTERM)
            break
        time.sleep(.05)
    child.wait()
stdout=(D/'run.stdout').read_text()
lines=stdout.splitlines()
hits=[line for line in lines if line.startswith('HIT ')]
status=('HIT_PENDING_INDEPENDENT_REPLAY' if child.returncode==0 and len(hits)==1
        else 'MISS_COMPLETE' if child.returncode==0 and any(x.startswith('MISS_COMPLETE ') for x in lines)
        else 'BOUNDED_UNKNOWN' if stop else 'PRODUCER_FAILURE')
result={'status':status,'protocol_sha256':sha(D/'protocol.json'),
        'runner_sha256':sha(Path(__file__)),
        'binary_sha256':binary_sha,'compile_stdout_sha256':sha(D/'compile.stdout'),
        'compile_stderr_sha256':sha(D/'compile.stderr'),
        'command':command,'exit_code':child.returncode,'stop_reason':stop,
        'wall_s':time.monotonic()-start,'sampled_peak_combined_rss_bytes':peak,
        'monitor_degraded':degraded,'hit_lines':hits,
        'stdout_sha256':sha(D/'run.stdout'),'stderr_sha256':sha(D/'run.stderr')}
(D/'run_result.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
print(json.dumps({k:result[k] for k in ('status','wall_s',
                 'sampled_peak_combined_rss_bytes','hit_lines')},sort_keys=True))
