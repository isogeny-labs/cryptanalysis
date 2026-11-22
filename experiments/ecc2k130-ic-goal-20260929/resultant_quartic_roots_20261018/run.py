"""One-worker resource and wall wrapper for frozen quartic-root probes."""
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
WORKSPACE = HERE.parents[2]
mode = sys.argv[1]
assert mode in ('n41_smoke', 'n41', 'n131')
cfg = json.loads((HERE / 'protocol.json').read_text())
for name, expected in cfg['sources'].items():
    path = Path(name)
    if not path.is_absolute():
        path = WORKSPACE / path
    assert hashlib.sha256(path.read_bytes()).hexdigest() == expected, name
assert not (HERE / f'{mode}_run_result.json').exists()
command = [cfg['sage_launcher'], '-python', str(HERE / 'probe.py'), mode]
started = time.monotonic()
peak = samples = 0
stop = monitor_error = None
parent = psutil.Process(os.getpid())
stdout = HERE / f'{mode}.stdout'
stderr = HERE / f'{mode}.stderr'
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
        if time.monotonic()-started > cfg['wall_caps'][mode]:
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
elif exit_code == 0 and (HERE / f'{mode}_result.json').exists():
    status = 'COMPLETE'
else:
    status = 'PRODUCER_FAILURE'
result = {'status': status, 'candidate_id': None,
          'mode': mode, 'command': command,
          'stop_reason': stop, 'monitor_error': monitor_error,
          'exit_code': exit_code, 'wall_seconds': time.monotonic()-started,
          'sampled_peak_combined_rss_bytes': peak, 'rss_samples': samples,
          'stdout_sha256': hashlib.sha256(stdout.read_bytes()).hexdigest(),
          'stderr_sha256': hashlib.sha256(stderr.read_bytes()).hexdigest(),
          'protocol_sha256': hashlib.sha256((HERE / 'protocol.json').read_bytes()).hexdigest()}
(HERE / f'{mode}_run_result.json').write_text(json.dumps(result, sort_keys=True, indent=2)+'\n')
print(json.dumps({key: result[key] for key in
                  ('mode', 'status', 'wall_seconds', 'sampled_peak_combined_rss_bytes')},
                 sort_keys=True))
