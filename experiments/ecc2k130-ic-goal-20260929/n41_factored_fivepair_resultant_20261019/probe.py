"""Frozen one-worker N41 public-point SAT conflict diagnostic."""
import hashlib
import json
import subprocess
import time
from pathlib import Path

HERE=Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


protocol=json.loads((HERE/'probe_protocol.json').read_text())
for path,digest in protocol['sources'].items():
    assert sha(path)==digest,path
assert not (HERE/'probe_result.json').exists()
formula=HERE/'fivepair_factored.xcnf'
solver=Path(protocol['solver'])
command=[str(solver),'--threads=1','--maxconfl=100000','--maxtime=60',
         '--zero-exit-status','--verb=1','--printsol=1',str(formula)]
stdout_path=HERE/'probe.stdout'
stderr_path=HERE/'probe.stderr'
started=time.monotonic_ns()
with stdout_path.open('x') as stdout,stderr_path.open('x') as stderr:
    try:
        process=subprocess.run(command,stdout=stdout,stderr=stderr,
                               timeout=65,check=False)
        exit_code=process.returncode
        stop_reason=None
    except subprocess.TimeoutExpired:
        exit_code=None
        stop_reason='PARENT_TIMEOUT'
elapsed=time.monotonic_ns()-started
output=stdout_path.read_text(errors='replace')
statuses=[line for line in output.splitlines() if line.startswith('s ')]
last_restart=next((line for line in reversed(output.splitlines())
                   if line.startswith('c rst ')),None)
status=('BOUNDED_UNKNOWN' if stop_reason or not statuses else
        ('SAT_MODEL_UNVERIFIED' if statuses[-1].strip()=='s SATISFIABLE' else
         'UNSAT_UNCERTIFIED' if statuses[-1].strip()=='s UNSATISFIABLE' else
         'INDETERMINATE'))
result={'status':status,'candidate_id':None,'curve_id':protocol['curve_id'],
        'command':command,'exit_code':exit_code,'stop_reason':stop_reason,
        'elapsed_ns':elapsed,'status_lines':statuses,'last_restart':last_restart,
        'stdout_sha256':sha(stdout_path),'stderr_sha256':sha(stderr_path),
        'protocol_sha256':sha(HERE/'probe_protocol.json')}
(HERE/'probe_result.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
print(json.dumps(result,sort_keys=True))
