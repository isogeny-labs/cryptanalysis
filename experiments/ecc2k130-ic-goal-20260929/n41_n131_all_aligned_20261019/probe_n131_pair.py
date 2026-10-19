"""One-worker A/B stage probe of two frozen N131 XCNF encodings."""
import hashlib
import json
import os
import signal
import subprocess
import time
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


protocol = json.loads((HERE / 'probe_protocol.json').read_text())
assert protocol['status'] == 'FROZEN_BEFORE_N131_PAIRED_STAGE_PROBE'
assert sha(Path(__file__)) == protocol['script_sha256']
for record in protocol['inputs'].values():
    assert sha(record['path']) == record['sha256']
assert sha(protocol['solver']) == protocol['solver_sha256']
assert not (HERE / 'probe_result.json').exists()

results = []
for label in protocol['order']:
    formula = protocol['inputs'][label]['path']
    cmd = [protocol['solver'], '--threads=1',
           f"--maxtime={protocol['wall_cap_seconds_per_arm']}",
           '--zero-exit-status', '--verb=1', '--printsol=0', formula]
    outpath = HERE / f'probe_{label}.stdout'
    errpath = HERE / f'probe_{label}.stderr'
    parent = psutil.Process(os.getpid())
    start = time.monotonic()
    peak = 0
    samples = 0
    stop = None
    with outpath.open('xb') as out, errpath.open('xb') as err:
        child = subprocess.Popen(cmd, stdout=out, stderr=err, start_new_session=True)
        observed = psutil.Process(child.pid)
        while child.poll() is None:
            try:
                peak = max(peak, parent.memory_info().rss + observed.memory_info().rss)
                samples += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                if child.poll() is None:
                    stop = 'MONITOR_FAILURE'
                    break
            if peak > protocol['rss_cap_bytes']:
                stop = 'RSS_CAP'
                break
            if time.monotonic() - start >= protocol['wall_cap_seconds_per_arm']:
                stop = 'WALL_CAP'
                break
            time.sleep(0.1)
        if stop and child.poll() is None:
            os.killpg(child.pid, signal.SIGTERM)
        exit_code = child.wait()
    stream = outpath.read_text(errors='replace')
    restarts = [line for line in stream.splitlines() if line.startswith('c rst')]
    status = ('SAT_MODEL_UNVERIFIED' if 's SATISFIABLE' in stream else
              'UNSAT_UNCERTIFIED' if 's UNSATISFIABLE' in stream else
              'BOUNDED_UNKNOWN' if stop == 'WALL_CAP' or 's INDETERMINATE' in stream else
              stop or 'PRODUCER_FAILURE_NO_TERMINAL_STATUS')
    results.append({'label': label, 'status': status, 'stop_reason': stop,
                    'exit_code': exit_code, 'wall_seconds': time.monotonic()-start,
                    'peak_combined_rss_bytes': peak, 'rss_samples': samples,
                    'last_restart_line': restarts[-1] if restarts else None,
                    'stdout_sha256': sha(outpath), 'stderr_sha256': sha(errpath)})
    partial = {'status': 'IN_PROGRESS', 'results': results,
               'protocol_sha256': sha(HERE / 'probe_protocol.json')}
    (HERE / 'probe_partial.json').write_text(json.dumps(partial, sort_keys=True, indent=2)+'\n')
final = {'status': 'COMPLETE_PAIRED_N131_STAGE_PROBE', 'candidate_id': None,
         'results': results, 'protocol_sha256': sha(HERE / 'probe_protocol.json')}
(HERE / 'probe_result.json').write_text(json.dumps(final, sort_keys=True, indent=2)+'\n')
print(json.dumps(final, sort_keys=True))
