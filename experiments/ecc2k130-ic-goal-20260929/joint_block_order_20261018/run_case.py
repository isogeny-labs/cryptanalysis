"""Bound one checked-Sage joint-block Gröbner query and retain its receipt."""
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
case_name = sys.argv[1]
design = json.loads((HERE / 'protocol.json').read_text())
assert case_name in design['cases']
case = design['cases'][case_name]
run_protocol_name = ('run_protocol_n41.json' if case['field_degree'] == 41
                     else 'run_protocol_n131.json')
cfg = json.loads((HERE / run_protocol_name).read_text())
for path, expected in cfg['sources'].items():
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == expected, path
if case['field_degree'] == 131:
    gate = json.loads((HERE / 'n41_gate.json').read_text())
    assert gate['status'] == 'PASS_N41_JOINT_BLOCK_CONTROL'
    assert hashlib.sha256((HERE / 'n41_gate.json').read_bytes()).hexdigest() == cfg['n41_gate_sha256']
outcome = HERE / (case_name + '_receipt.json')
assert not outcome.exists()
stdout = HERE / (case_name + '.stdout')
stderr = HERE / (case_name + '.stderr')
assert not stdout.exists() and not stderr.exists()
command = [cfg['sage_launcher'], '-python', str(HERE / 'joint_gb_order.py'), case_name]
parent = psutil.Process(os.getpid())
started = time.monotonic()
peak = 0
samples = 0
stop = None
monitor_error = None
with stdout.open('xb') as out, stderr.open('xb') as err:
    child = subprocess.Popen(command, cwd=cfg['workspace'], stdout=out, stderr=err,
                             start_new_session=True)
    (HERE / (case_name + '_handle.json')).write_text(json.dumps({
        'child_pid': child.pid, 'case': case_name, 'command': command,
        'started_monotonic': started}, sort_keys=True, indent=2) + '\n')
    observed = psutil.Process(child.pid)
    while child.poll() is None:
        try:
            peak = max(peak, parent.memory_info().rss + observed.memory_info().rss)
            samples += 1
        except psutil.NoSuchProcess:
            # The child may have exited between poll() and the RSS sample.
            # Confirm its exit before classifying this as a monitor failure.
            if child.poll() is not None:
                break
            time.sleep(.1)
            if child.poll() is not None:
                break
            monitor_error = 'NoSuchProcessWhileLive'
            stop = 'MONITOR_FAILURE'
            break
        except (psutil.AccessDenied, PermissionError) as exc:
            if child.poll() is None:
                monitor_error = type(exc).__name__
                stop = 'MONITOR_FAILURE'
                break
        if peak > cfg['rss_cap_bytes']:
            stop = 'RSS_CAP'
            break
        if time.monotonic() - started > case['wall_cap_seconds']:
            stop = 'WALL_CAP'
            break
        time.sleep(.1)
    if stop and child.poll() is None:
        try:
            child.terminate()
        except ProcessLookupError:
            pass
    exit_code = child.wait()
result_file = HERE / (case_name + '_result.json')
if stop == 'WALL_CAP':
    status = 'BOUNDED_UNKNOWN'
elif stop:
    status = stop
elif exit_code == 0 and result_file.exists():
    status = 'COMPLETE'
else:
    status = 'PRODUCER_FAILURE'
result = {'status': status, 'candidate_id': None, 'case': case_name,
          'curve_id': cfg['curve_ids'][str(case['field_degree'])],
          'command': command, 'child_pid': child.pid,
          'exit_code': exit_code, 'stop_reason': stop,
          'monitor_error': monitor_error, 'wall_seconds': time.monotonic() - started,
          'sampled_peak_combined_rss_bytes': peak, 'rss_samples': samples,
          'stdout_sha256': hashlib.sha256(stdout.read_bytes()).hexdigest(),
          'stderr_sha256': hashlib.sha256(stderr.read_bytes()).hexdigest(),
          'result_sha256': hashlib.sha256(result_file.read_bytes()).hexdigest()
                           if result_file.exists() else None,
          'protocol_sha256': hashlib.sha256((HERE / run_protocol_name).read_bytes()).hexdigest()}
outcome.write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
print(json.dumps({k: result[k] for k in ('case', 'status', 'wall_seconds',
                                        'sampled_peak_combined_rss_bytes')}, sort_keys=True))
