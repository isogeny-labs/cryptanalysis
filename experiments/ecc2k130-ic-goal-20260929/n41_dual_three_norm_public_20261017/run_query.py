"""Monitor one ordinary CryptoMiniSat query against the public point."""
import hashlib
import json
import os
import signal
import subprocess
import time
from pathlib import Path
import psutil

D=Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


protocol=json.loads((D/'query_protocol.json').read_text())
assert protocol['producer_sha256']==sha(Path(__file__))
assert protocol['formula_sha256']==sha(D/'public.xcnf')
assert protocol['solver_sha256']==sha(Path(protocol['solver_path']))
assert protocol['build_result_sha256']==sha(D/'build_result.json')
command=[protocol['solver_path'],*protocol['flags'],str(D/'public.xcnf')]
parent=psutil.Process(os.getpid())
start=time.monotonic()
peak=0;stop=None;degraded=False
with (D/'solver.stdout').open('x') as out,(D/'solver.stderr').open('x') as err:
    child=subprocess.Popen(command,stdout=out,stderr=err,start_new_session=True)
    process=psutil.Process(child.pid)
    while child.poll() is None:
        try:
            peak=max(peak,parent.memory_info().rss+process.memory_info().rss)
        except (psutil.NoSuchProcess,psutil.AccessDenied,PermissionError):
            if child.poll() is None:degraded=True
        if peak>protocol['rss_cap_bytes']:stop='RSS_CAP'
        elif time.monotonic()-start>protocol['parent_cap_s']:stop='PARENT_WALL_CAP'
        if stop:
            os.killpg(child.pid,signal.SIGTERM)
            break
        time.sleep(.1)
    child.wait()
stdout=(D/'solver.stdout').read_text(errors='replace')
terminal=[line.strip() for line in stdout.splitlines() if line.startswith('s ')]
status=('SAT_PENDING_INDEPENDENT_REPLAY' if 's SATISFIABLE' in terminal
        else 'UNSAT_UNCERTIFIED' if 's UNSATISFIABLE' in terminal
        else 'BOUNDED_UNKNOWN' if stop or any('INDETERMINATE' in line for line in terminal)
        else 'PRODUCER_FAILURE')
result={'status':status,'protocol_sha256':sha(D/'query_protocol.json'),
        'command':command,'exit_code':child.returncode,
        'wall_s':time.monotonic()-start,'stop_reason':stop,
        'terminal_lines':terminal,
        'restart_lines':sum(line.startswith('c rst ') for line in stdout.splitlines()),
        'sampled_peak_combined_rss_bytes':peak,'monitor_degraded':degraded,
        'stdout_sha256':sha(D/'solver.stdout'),
        'stderr_sha256':sha(D/'solver.stderr')}
(D/'query_result.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
print(json.dumps({k:result[k] for k in ('status','wall_s','exit_code',
                                         'sampled_peak_combined_rss_bytes','terminal_lines')},
                 sort_keys=True))
