"""One-worker bounded first-code-pinned N131 positive control."""
import hashlib
import json
import os
import signal
import subprocess
import time
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parent
cfg = json.loads((HERE / 'pin_query_protocol.json').read_text())
for name, digest in cfg['sources'].items():
    assert hashlib.sha256(Path(name).read_bytes()).hexdigest() == digest, name
assert json.loads((HERE / 'solver_0_result.json').read_text())['status'] == 'BOUNDED_UNKNOWN'
outcome = HERE / 'pin_query_result.json'
assert not outcome.exists()
command = [cfg['solver'], '--threads=1',
           f"--maxtime={cfg['solver_cap_seconds']}",
           '--zero-exit-status', '--verb=1', '--printsol=1',
           str(HERE / 'positive_pin_first.xcnf')]
started = time.monotonic()
peak = samples = 0
stop = monitor_error = None
parent = psutil.Process(os.getpid())
stdout, stderr = HERE / 'pin_solver.stdout', HERE / 'pin_solver.stderr'
with stdout.open('xb') as out, stderr.open('xb') as err:
    child = subprocess.Popen(command, stdout=out, stderr=err, start_new_session=True)
    observed = psutil.Process(child.pid)
    while child.poll() is None:
        try:
            peak = max(peak, parent.memory_info().rss+observed.memory_info().rss)
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
result = {'status': status, 'candidate_id': None,
          'curve_id': cfg['curve_id'], 'known_first_code': 3,
          'command': command, 'stop_reason': stop,
          'monitor_error': monitor_error, 'solver_exit_code': exit_code,
          'solver_terminal_sat': 's SATISFIABLE' in stream,
          'solver_terminal_unsat': 's UNSATISFIABLE' in stream,
          'solver_terminal_indeterminate': 's INDETERMINATE' in stream,
          'last_restart_line': restarts[-1] if restarts else None,
          'wall_seconds': time.monotonic()-started,
          'sampled_peak_combined_rss_bytes': peak, 'rss_samples': samples,
          'solver_stdout_sha256': hashlib.sha256(stdout.read_bytes()).hexdigest(),
          'solver_stderr_sha256': hashlib.sha256(stderr.read_bytes()).hexdigest(),
          'protocol_sha256': hashlib.sha256((HERE / 'pin_query_protocol.json').read_bytes()).hexdigest()}
outcome.write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')
print(json.dumps({k: result[k] for k in
                  ('status', 'wall_seconds', 'sampled_peak_combined_rss_bytes')},
                 sort_keys=True))
