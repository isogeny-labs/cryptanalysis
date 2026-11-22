"""Run the frozen ordinary N41 SAT query with monitored limits."""
import hashlib,json,os,signal,subprocess,time
from pathlib import Path
import psutil
HERE=Path(__file__).resolve().parent
record=json.loads((HERE/'sat_protocol.json').read_text())
for path,digest in record['sources'].items():
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==digest,path
command=[record['solver_path'],*record['solver_flags'],str(HERE/'ordinary.xcnf')]
parent=psutil.Process(os.getpid());start=time.monotonic_ns();peak=0;degraded=False;stop=None
with (HERE/'sat.stdout').open('x') as out,(HERE/'sat.stderr').open('x') as err:
    child=subprocess.Popen(command,stdout=out,stderr=err,start_new_session=True)
    proc=psutil.Process(child.pid)
    while child.poll() is None:
        try:peak=max(peak,parent.memory_info().rss+proc.memory_info().rss)
        except (psutil.NoSuchProcess,psutil.AccessDenied,PermissionError):
            if child.poll() is None:degraded=True
        if peak>record['rss_cap_bytes']:stop='RSS_CAP'
        elif time.monotonic_ns()-start>record['parent_wall_cap_seconds']*10**9:stop='PARENT_WALL_CAP'
        if stop:os.killpg(child.pid,signal.SIGTERM);break
        time.sleep(.1)
    child.wait()
stdout=(HERE/'sat.stdout').read_text(errors='replace')
terminal=[line for line in stdout.splitlines() if line.startswith('s ')]
result={'status':'SAT' if any(line.strip()=='s SATISFIABLE' for line in terminal)
        else 'UNSAT' if any(line.strip()=='s UNSATISFIABLE' for line in terminal)
        else 'BOUNDED_UNKNOWN' if stop or any('INDETERMINATE' in line for line in terminal)
        else 'PRODUCER_FAILURE',
        'exit_code':child.returncode,'command':command,
        'wall_ns':time.monotonic_ns()-start,'stop_reason':stop,
        'terminal_lines':terminal,
        'sampled_peak_combined_rss_bytes':peak,'monitor_degraded':degraded,
        'protocol_sha256':hashlib.sha256((HERE/'sat_protocol.json').read_bytes()).hexdigest(),
        'sha256':{name:hashlib.sha256((HERE/name).read_bytes()).hexdigest()
                  for name in ('sat.stdout','sat.stderr')}}
with (HERE/'sat_result.json').open('x') as out:
    json.dump(result,out,sort_keys=True,indent=2);out.write('\n')
print(result['status'],result['wall_ns']/1e9,terminal[-1:] if terminal else [])
