"""One-worker bounded native-XOR solver run on frozen public-point formula."""
import hashlib,json,resource,subprocess,time
from pathlib import Path
import psutil
h=Path(__file__).resolve().parent
p=json.loads((h/'solver_protocol_v3.json').read_text())
def sha(q):return hashlib.sha256(q.read_bytes()).hexdigest()
paths={'runner':h/'run_n41_solver_v3.py','formula':h/'v2_n41_control.xcnf',
       'solver':Path(p['solver_path']),'build_receipt':h/'v2_n41_control.json',
       'control_check':h/'v2_n41_control.json'}
assert {k:sha(v) for k,v in paths.items()}==p['sha256']
assert not (h/'n41_solver_receipt_v3.json').exists()
start=time.monotonic_ns();before=resource.getrusage(resource.RUSAGE_CHILDREN)
parent=psutil.Process();peak=0;stop=None
with (h/'n41_solver_v3.stdout').open('x') as out,(h/'n41_solver_v3.stderr').open('x') as err:
    child=subprocess.Popen([p['solver_path'],*p['solver_flags'],str(h/'v2_n41_control.xcnf')],stdout=out,stderr=err)
    proc=psutil.Process(child.pid)
    while child.poll() is None:
        try:rss=parent.memory_info().rss+proc.memory_info().rss
        except psutil.NoSuchProcess:rss=parent.memory_info().rss
        peak=max(peak,rss)
        if rss>p['rss_cap_bytes']:stop='RSS_CAP'
        elif time.monotonic_ns()-start>=p['parent_wall_cap_seconds']*10**9:stop='WALL_CAP'
        if stop:child.kill();break
        time.sleep(.05)
    code=child.wait()
end=time.monotonic_ns();after=resource.getrusage(resource.RUSAGE_CHILDREN)
lines=(h/'n41_solver_v3.stdout').read_text().splitlines()
terminal=[v for v in lines if v.startswith('s ')]
status='BOUNDED_UNKNOWN' if stop else 'SAT_PENDING_MODEL_AUDIT' if any(v=='s SATISFIABLE' for v in terminal) else 'UNSAT' if any(v=='s UNSATISFIABLE' for v in terminal) else 'BOUNDED_UNKNOWN' if any(v=='s INDETERMINATE' for v in terminal) else 'ERROR'
r={'status':status,'stop_reason':stop,'exit_code':code,'worker_count':1,'solver_terminal_lines':terminal,
   'parent_wall_ns':end-start,'peak_combined_rss_bytes_sampled':peak,
   'child_user_seconds':after.ru_utime-before.ru_utime,'child_system_seconds':after.ru_stime-before.ru_stime,
   'stdout_sha256':sha(h/'n41_solver_v3.stdout'),'stderr_sha256':sha(h/'n41_solver_v3.stderr'),
   'protocol_sha256':sha(h/'solver_protocol_v3.json')}
(h/'n41_solver_receipt_v3.json').write_text(json.dumps(r,sort_keys=True,indent=2)+'\n')
print(status,(end-start)/1e9,peak,flush=True)
