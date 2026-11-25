"""Bound a single checked-Sage Boolean Gröbner case and preserve its receipt."""
import hashlib
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parent
case = sys.argv[1]
assert case in ('n41_positive', 'n41_ordinary', 'n131_positive_48')
cfg = json.loads((HERE / 'protocol.json').read_text())
for name, expected in cfg['sources'].items():
    path = Path(name)
    if not path.is_absolute():
        path = HERE.parents[2] / path
    assert hashlib.sha256(path.read_bytes()).hexdigest() == expected, name
assert not (HERE / f'{case}_run_result.json').exists()
cap = cfg['wall_caps'][case]
command = [cfg['sage_launcher'], '-python', str(HERE / 'solve.py'), case]
started = time.monotonic()
peak = samples = 0
stop = monitor_error = None
parent = psutil.Process(os.getpid())
stdout = HERE / f'{case}.stdout'
stderr = HERE / f'{case}.stderr'
with stdout.open('xb') as out, stderr.open('xb') as err:
    child = subprocess.Popen(command, stdout=out, stderr=err, start_new_session=True)
    observed = psutil.Process(child.pid)
    while child.poll() is None:
        try:
            descendants = observed.children(recursive=True)
            processes = [parent, observed, *descendants]
            rss = sum(process.memory_info().rss for process in processes
                      if process.is_running())
            peak = max(peak, rss)
            samples += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied, PermissionError) as exc:
            if child.poll() is None:
                monitor_error = type(exc).__name__
                stop = 'MONITOR_FAILURE'
                break
        if peak > cfg['rss_cap_bytes']:
            stop = 'RSS_CAP'
            break
        if time.monotonic()-started > cap:
            stop = 'WALL_CAP'
            break
        time.sleep(.1)
    if stop and child.poll() is None:
        os.killpg(child.pid, signal.SIGTERM)
    exit_code = child.wait()
if stop == 'WALL_CAP':
    status = 'BOUNDED_UNKNOWN'
elif stop:
    status = stop
elif exit_code == 0 and (HERE / f'{case}_result.json').exists():
    status = 'GB_COMPLETE'
else:
    status = 'PRODUCER_FAILURE'
result = {'status': status, 'candidate_id': None,
          'case': case, 'command': command,
          'stop_reason': stop, 'monitor_error': monitor_error,
          'exit_code': exit_code, 'wall_seconds': time.monotonic()-started,
          'sampled_peak_combined_rss_bytes': peak, 'rss_samples': samples,
          'stdout_sha256': hashlib.sha256(stdout.read_bytes()).hexdigest(),
          'stderr_sha256': hashlib.sha256(stderr.read_bytes()).hexdigest(),
          'protocol_sha256': hashlib.sha256((HERE / 'protocol.json').read_bytes()).hexdigest()}
(HERE / f'{case}_run_result.json').write_text(json.dumps(result, sort_keys=True, indent=2)+'\n')
print(json.dumps({k: result[k] for k in ('case', 'status', 'wall_seconds',
                                        'sampled_peak_combined_rss_bytes')},
                 sort_keys=True))
