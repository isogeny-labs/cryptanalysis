"""Attach a direct-PID cap monitor to the already-running solver process."""
import hashlib
import json
import time
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


protocol = json.loads((HERE / 'rescue_protocol.json').read_text())
assert sha(Path(__file__)) == protocol['source_sha256']['script']
assert sha(HERE / 'query_protocol.json') == protocol['source_sha256']['query_protocol']
assert sha(HERE / 'query_failure_v1.json') == protocol['source_sha256']['failure']
assert not (HERE / 'rescue_result.json').exists()

query = json.loads((HERE / 'query_protocol.json').read_text())
birthtime = protocol['solver_birthtime_unix']
pid = protocol['solver_pid']
proc = psutil.Process(pid)
assert abs(proc.create_time()-birthtime) < 0.01
assert proc.name() == 'cryptominisat5'
attach_time = time.time()
peak_rss = 0
samples = 0
cap_reason = None
while True:
    try:
        if abs(proc.create_time()-birthtime) >= 0.01:
            raise RuntimeError('PID reused during monitoring')
        status = proc.status()
        if status == psutil.STATUS_ZOMBIE:
            break
        rss = proc.memory_info().rss
        peak_rss = max(peak_rss, rss)
        samples += 1
    except psutil.NoSuchProcess:
        break
    elapsed = time.time()-birthtime
    if peak_rss > query['rss_cap_bytes']:
        cap_reason = 'RSS_CAP'
    elif elapsed > query['wall_cap_seconds']:
        cap_reason = 'WALL_CAP'
    if cap_reason:
        try:
            proc.terminate()
            proc.wait(timeout=2)
        except psutil.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=2)
        except psutil.NoSuchProcess:
            pass
        break
    time.sleep(0.2)

time.sleep(0.25)
stdout = (HERE / 'solver.stdout').read_text(errors='replace')
if cap_reason:
    terminal_status = cap_reason
elif 's SATISFIABLE' in stdout:
    terminal_status = 'SAT_MODEL_UNVERIFIED'
elif 's UNSATISFIABLE' in stdout:
    terminal_status = 'UNSAT_FORMULA_INCONSISTENT_WITH_WITNESS'
elif 's INDETERMINATE' in stdout:
    terminal_status = 'INDETERMINATE_SOLVER_CAP'
else:
    terminal_status = 'PRODUCER_FAILURE_NO_TERMINAL_STATUS'
result = {
    'status': terminal_status,
    'solver_pid': pid,
    'solver_birthtime_unix': birthtime,
    'attach_time_unix': attach_time,
    'unmonitored_gap_seconds': attach_time-birthtime,
    'finish_time_unix': time.time(),
    'elapsed_since_birth_seconds': time.time()-birthtime,
    'rss_peak_after_attach_bytes': peak_rss,
    'rss_samples_after_attach': samples,
    'cap_reason': cap_reason,
    'exit_code': None,
    'stdout_sha256': sha(HERE / 'solver.stdout'),
    'stderr_sha256': sha(HERE / 'solver.stderr'),
    'query_protocol_sha256': sha(HERE / 'query_protocol.json'),
    'protocol_sha256': sha(HERE / 'rescue_protocol.json'),
}
(HERE / 'rescue_result.json').write_text(json.dumps(result, sort_keys=True, indent=2)+'\n')
print(json.dumps({'status': terminal_status,
                  'elapsed_seconds': result['elapsed_since_birth_seconds'],
                  'peak_rss': peak_rss}))
