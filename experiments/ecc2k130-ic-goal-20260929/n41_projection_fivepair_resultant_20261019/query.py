"""One-worker, resource-capped public-point SAT query for the frozen circuit."""
import hashlib
import json
import subprocess
import time
from pathlib import Path

HERE=Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


protocol=json.loads((HERE/'query_protocol.json').read_text())
for path,digest in protocol['sources'].items():
    assert sha(path)==digest,path
assert not (HERE/'query_result.json').exists()
limit=protocol['rss_cap_bytes']


solver=Path(protocol['solver'])
formula=HERE/'fivepair_projection.xcnf'
command=[str(solver),'--threads=1','--maxtime=60','--zero-exit-status',
         '--verb=1','--printsol=1',str(formula)]
stdout_path=HERE/'query.stdout'
stderr_path=HERE/'query.stderr'
started=time.monotonic_ns()
peak_rss=None
rss_samples=0
monitor_errors=0
stop_reason=None
with stdout_path.open('x') as stdout,stderr_path.open('x') as stderr:
    proc=subprocess.Popen(command,stdout=stdout,stderr=stderr)
    while proc.poll() is None:
        elapsed=(time.monotonic_ns()-started)/1e9
        if elapsed>=protocol['parent_wall_cap_seconds']:
            proc.kill()
            stop_reason='PARENT_WALL_CAP'
            break
        sample=subprocess.run(['/bin/ps','-o','rss=','-p',str(proc.pid)],
                              capture_output=True,text=True,check=False)
        try:
            rss=int(sample.stdout.strip())*1024
            peak_rss=max(peak_rss or 0,rss)
            rss_samples+=1
            if rss>limit:
                proc.kill()
                stop_reason='WORKER_RSS_CAP'
                break
        except ValueError:
            monitor_errors+=1
            proc.kill()
            stop_reason='RSS_MONITOR_FAILURE'
            break
        time.sleep(0.2)
    exit_code=proc.wait()
elapsed_ns=time.monotonic_ns()-started
output=stdout_path.read_text(errors='replace')
statuses=[line for line in output.splitlines() if line.startswith('s ')]
if stop_reason:
    status=('PRODUCER_FAILURE_MONITOR' if stop_reason=='RSS_MONITOR_FAILURE'
            else 'BOUNDED_UNKNOWN')
elif not statuses:
    status='PRODUCER_FAILURE_NO_TERMINAL_STATUS' if exit_code else 'BOUNDED_UNKNOWN'
elif statuses[-1].strip()=='s SATISFIABLE':
    status='SAT_MODEL_UNVERIFIED'
elif statuses[-1].strip()=='s UNSATISFIABLE':
    status='UNSAT_UNCERTIFIED'
else:
    status='BOUNDED_UNKNOWN'
result={'status':status,'candidate_id':None,'curve_id':protocol['curve_id'],
        'command':command,'exit_code':exit_code,'stop_reason':stop_reason,
        'elapsed_ns':elapsed_ns,'status_lines':statuses,
        'sampled_peak_worker_rss_bytes':peak_rss,'rss_samples':rss_samples,
        'monitor_errors':monitor_errors,'rss_cap_bytes':limit,
        'stdout_sha256':sha(stdout_path),'stderr_sha256':sha(stderr_path),
        'protocol_sha256':sha(HERE/'query_protocol.json')}
(HERE/'query_result.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
print(json.dumps(result,sort_keys=True))
