"""Bounded fixed-code/output control for the functional S3 circuit."""
import hashlib
import json
import os
import signal
import subprocess
import time
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parent
protocol = json.loads((HERE / 'fixed_query_protocol.json').read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


for path, expected in protocol['sources'].items():
    assert sha(path) == expected, path
assert not (HERE / 'fixed_query_result.json').exists()
build = json.loads((HERE / 'fixed_build_result.json').read_text())
assert build['status'] == 'PASS_N41_FUNCTIONAL_S3_FIXED_CODES_OUTPUTS_CONTROL_BUILD'
assert build['formula_sha256'] == sha(HERE / 'fixed_formula.xcnf')
command = [protocol['solver'], '--threads=1',
           f"--maxtime={protocol['solver_cap_seconds']}",
           '--zero-exit-status', '--verb=1', '--printsol=1',
           str(HERE / 'fixed_formula.xcnf')]
started = time.monotonic()
parent = psutil.Process(os.getpid())
peak = 0
samples = 0
stop = None
monitor_error = None
with (HERE / 'fixed_solver.stdout').open('xb') as out, (HERE / 'fixed_solver.stderr').open('xb') as err:
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
        if peak > protocol['rss_cap_bytes']:
            stop = 'RSS_CAP'
            break
        if time.monotonic() - started > protocol['parent_wall_cap_seconds']:
            stop = 'WALL_CAP'
            break
        time.sleep(.1)
    if stop and child.poll() is None:
        os.killpg(child.pid, signal.SIGTERM)
    exit_code = child.wait()
wall = time.monotonic() - started
stream = (HERE / 'fixed_solver.stdout').read_text(errors='replace')
if stop:
    status = 'BOUNDED_UNKNOWN' if stop == 'WALL_CAP' else stop
elif 's SATISFIABLE' in stream:
    status = 'SAT_MODEL_UNVERIFIED'
elif 's UNSATISFIABLE' in stream:
    status = 'UNSAT_UNCERTIFIED'
elif 's INDETERMINATE' in stream:
    status = 'BOUNDED_UNKNOWN'
else:
    status = 'PRODUCER_FAILURE_NO_TERMINAL_STATUS'
result = {'status': status, 'candidate_id': None,
          'curve_id': protocol['curve_id'], 'worker_count': 1,
          'command': command, 'solver_exit_code': exit_code,
          'stop_reason': stop, 'monitor_error': monitor_error,
          'solver_terminal_sat': 's SATISFIABLE' in stream,
          'solver_terminal_unsat': 's UNSATISFIABLE' in stream,
          'solver_terminal_indeterminate': 's INDETERMINATE' in stream,
          'solver_stdout_sha256': sha(HERE / 'fixed_solver.stdout'),
          'solver_stderr_sha256': sha(HERE / 'fixed_solver.stderr'),
          'query_parent_wall_seconds': wall,
          'sampled_peak_combined_rss_bytes': peak,
          'rss_samples': samples,
          'protocol_sha256': sha(HERE / 'fixed_query_protocol.json')}
(HERE / 'fixed_query_result.json').write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
print(json.dumps({key: result[key] for key in
                  ('status', 'stop_reason', 'query_parent_wall_seconds',
                   'sampled_peak_combined_rss_bytes')}, sort_keys=True))
