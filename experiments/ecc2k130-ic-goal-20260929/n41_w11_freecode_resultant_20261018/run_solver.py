"""Bounded one-worker XCNF checks for the free-code resultant."""
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
index = int(sys.argv[1])
assert index in (0, 1)
cfg = json.loads((HERE / 'solver_protocol.json').read_text())
for name, digest in cfg['sources'].items():
    assert hashlib.sha256(Path(name).read_bytes()).hexdigest() == digest, name
formula = HERE / ('positive.xcnf' if index == 0 else 'ordinary.xcnf')
outcome = HERE / f'solver_{index}_result.json'
assert not outcome.exists()
command = [cfg['solver'], '--threads=1',
           f"--maxtime={cfg['solver_cap_seconds']}",
           '--zero-exit-status', '--verb=1', '--printsol=1', str(formula)]
started = time.monotonic()
peak = 0
samples = 0
stop = None
monitor_error = None
parent = psutil.Process(os.getpid())
stdout = HERE / f'solver_{index}.stdout'
stderr = HERE / f'solver_{index}.stderr'
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
stream = stdout.read_text(errors='replace')
if stop == 'WALL_CAP' or 's INDETERMINATE' in stream:
    status = 'BOUNDED_UNKNOWN'
elif stop:
    status = stop
elif 's SATISFIABLE' in stream:
    status = 'SAT_MODEL_UNVERIFIED'
elif 's UNSATISFIABLE' in stream:
    status = 'UNSAT_UNCERTIFIED'
else:
    status = 'PRODUCER_FAILURE_NO_TERMINAL_STATUS'
restarts = [line for line in stream.splitlines() if line.startswith('c rst')]
result = {'status': status, 'candidate_id': None, 'target_index': index,
          'curve_id': cfg['curve_id'], 'command': command,
          'stop_reason': stop, 'monitor_error': monitor_error,
          'solver_exit_code': exit_code,
          'solver_terminal_sat': 's SATISFIABLE' in stream,
          'solver_terminal_unsat': 's UNSATISFIABLE' in stream,
          'solver_terminal_indeterminate': 's INDETERMINATE' in stream,
          'last_restart_line': restarts[-1] if restarts else None,
          'wall_seconds': time.monotonic()-started,
          'sampled_peak_combined_rss_bytes': peak, 'rss_samples': samples,
          'solver_stdout_sha256': hashlib.sha256(stdout.read_bytes()).hexdigest(),
          'solver_stderr_sha256': hashlib.sha256(stderr.read_bytes()).hexdigest(),
          'protocol_sha256': hashlib.sha256((HERE / 'solver_protocol.json').read_bytes()).hexdigest()}
outcome.write_text(json.dumps(result, sort_keys=True, indent=2)+'\n')
print(json.dumps({k: result[k] for k in
                  ('status', 'wall_seconds', 'sampled_peak_combined_rss_bytes')},
                 sort_keys=True))
