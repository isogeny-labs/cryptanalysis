"""Bound and record the fixed-first-code Boolean Groebner solve."""
import hashlib
import json
import os
import signal
import subprocess
import time
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parent
cfg = json.loads((HERE / 'quadratic_protocol.json').read_text())
for name, expected in cfg['sources'].items():
    assert hashlib.sha256(Path(name).read_bytes()).hexdigest() == expected, name
assert not (HERE / 'quadratic_run_result.json').exists()
command = [cfg['sage_launcher'], '-python', str(HERE / 'quadratic_solver.py')]
started = time.monotonic()
peak = samples = 0
stop = monitor_error = None
parent = psutil.Process(os.getpid())
stdout = HERE / 'quadratic.stdout'
stderr = HERE / 'quadratic.stderr'
with stdout.open('xb') as out, stderr.open('xb') as err:
    child = subprocess.Popen(command, stdout=out, stderr=err, start_new_session=True)
    observed = psutil.Process(child.pid)
    while child.poll() is None:
        try:
            peak = max(peak, parent.memory_info().rss + observed.memory_info().rss)
            samples += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied, PermissionError) as exc:
            if child.poll() is None:
                monitor_error = type(exc).__name__
                stop = 'MONITOR_FAILURE'
                break
        if peak > cfg['rss_cap_bytes']:
            stop = 'RSS_CAP'
            break
        if time.monotonic()-started > cfg['parent_wall_cap_seconds']:
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
elif exit_code == 0 and (HERE / 'quadratic_result.json').exists():
    status = 'GB_COMPLETE'
else:
    status = 'PRODUCER_FAILURE'
result = {'status': status, 'candidate_id': None,
          'curve_id': cfg['curve_id'], 'command': command,
          'stop_reason': stop, 'monitor_error': monitor_error,
          'exit_code': exit_code, 'wall_seconds': time.monotonic()-started,
          'sampled_peak_combined_rss_bytes': peak, 'rss_samples': samples,
          'stdout_sha256': hashlib.sha256(stdout.read_bytes()).hexdigest(),
          'stderr_sha256': hashlib.sha256(stderr.read_bytes()).hexdigest(),
          'protocol_sha256': hashlib.sha256((HERE / 'quadratic_protocol.json').read_bytes()).hexdigest()}
(HERE / 'quadratic_run_result.json').write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')
print(json.dumps({k: result[k] for k in
                  ('status', 'wall_seconds', 'sampled_peak_combined_rss_bytes')},
                 sort_keys=True))
