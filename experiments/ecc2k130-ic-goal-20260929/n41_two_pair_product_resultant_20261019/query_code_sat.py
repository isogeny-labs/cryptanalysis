"""Bounded, sequential one-worker SAT queries for frozen two-pair keys."""
import hashlib
import json
import os
import signal
import subprocess
import time
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parent
protocol = json.loads((HERE / 'sat_query_protocol.json').read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


for path, expected in protocol['sources'].items():
    assert sha(path) == expected, path
assert not (HERE / 'sat_query_result.json').exists()
build = json.loads((HERE / 'sat_build_result.json').read_text())
assert build['status'] == 'PASS_N41_RESULTANT_CODE_SAT_BUILD'
rows = []
for item in build['rows']:
    key_id = item['key_id']
    formula = HERE / f'{key_id}_resultant.xcnf'
    assert sha(formula) == item['formula_sha256']
    stdout_path = HERE / f'{key_id}_resultant.stdout'
    stderr_path = HERE / f'{key_id}_resultant.stderr'
    command = [protocol['solver'], '--threads=1',
               f"--maxtime={protocol['solver_cap_seconds']}",
               '--zero-exit-status', '--verb=0', '--printsol=1', str(formula)]
    start = time.monotonic()
    parent = psutil.Process(os.getpid())
    peak = 0
    samples = 0
    stop = None
    with stdout_path.open('xb') as out, stderr_path.open('xb') as err:
        child = subprocess.Popen(command, stdout=out, stderr=err, start_new_session=True)
        worker = psutil.Process(child.pid)
        while child.poll() is None:
            try:
                peak = max(peak, parent.memory_info().rss + worker.memory_info().rss)
                samples += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied, PermissionError):
                if child.poll() is None:
                    stop = 'MONITOR_FAILURE'
                    break
            if peak > protocol['rss_cap_bytes']:
                stop = 'RSS_CAP'
                break
            if time.monotonic() - start > protocol['parent_wall_cap_seconds']:
                stop = 'WALL_CAP'
                break
            time.sleep(.05)
        if stop and child.poll() is None:
            os.killpg(child.pid, signal.SIGTERM)
        exit_code = child.wait()
    wall = time.monotonic() - start
    stream = stdout_path.read_text(errors='replace')
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
    rows.append({'key_id': key_id, 'exact_member': item['exact_member'],
                 'status': status, 'stop_reason': stop,
                 'command': command, 'solver_exit_code': exit_code,
                 'wall_seconds': wall, 'sampled_peak_combined_rss_bytes': peak,
                 'rss_samples': samples, 'stdout_sha256': sha(stdout_path),
                 'stderr_sha256': sha(stderr_path)})
    print(json.dumps({k: rows[-1][k] for k in ('key_id', 'exact_member',
                                               'status', 'wall_seconds')}), flush=True)
result = {'status': 'N41_RESULTANT_CODE_SAT_QUERY_PANEL', 'candidate_id': None,
          'curve_id': protocol['curve_id'], 'rows': rows,
          'protocol_sha256': sha(HERE / 'sat_query_protocol.json')}
(HERE / 'sat_query_result.json').write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
