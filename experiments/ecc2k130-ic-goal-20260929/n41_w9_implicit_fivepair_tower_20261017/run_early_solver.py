"""Bound the early-target SAT query with direct child RSS monitoring."""
import hashlib
import json
import resource
import subprocess
import time
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parent
SOLVER = Path('/opt/homebrew/bin/cryptominisat5')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


protocol = json.loads((HERE / 'early_query_protocol.json').read_text())
for name, path in {
    'script': Path(__file__), 'runtime': HERE / 'early_query_runtime_info.json',
    'formula': HERE / 'formula_early.xcnf',
    'build': HERE / 'early_build_result.json',
    'wires': HERE / 'input_wires_early.json',
    'fixture': HERE / 'fixture.json', 'solver': SOLVER,
}.items():
    assert sha(path) == protocol['source_sha256'][name], name
assert not (HERE / 'early_query_result.json').exists()
assert protocol['solver_argv'][0] == str(SOLVER)
assert protocol['solver_argv'][-1] == str(HERE / 'formula_early.xcnf')

start = time.monotonic()
peak_rss = 0
peak_combined_rss = 0
samples = 0
cap_reason = None
monitor_error = None
with (HERE / 'solver_early.stdout').open('xb') as stdout, \
     (HERE / 'solver_early.stderr').open('xb') as stderr:
    child = subprocess.Popen(protocol['solver_argv'], cwd=HERE,
                             stdout=stdout, stderr=stderr)
    observed = psutil.Process(child.pid)
    parent = psutil.Process()
    (HERE / 'early_solver_pid.json').write_text(json.dumps({
        'pid': child.pid, 'create_time_unix': observed.create_time(),
        'query_protocol_sha256': sha(HERE / 'early_query_protocol.json')},
        sort_keys=True, indent=2)+'\n')
    try:
        while child.poll() is None:
            try:
                rss = observed.memory_info().rss
                peak_rss = max(peak_rss, rss)
                peak_combined_rss = max(peak_combined_rss,
                                        rss + parent.memory_info().rss)
                samples += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied) as exc:
                if child.poll() is None:
                    monitor_error = type(exc).__name__
                    break
            elapsed = time.monotonic()-start
            if peak_combined_rss > protocol['rss_cap_bytes']:
                cap_reason = 'RSS_CAP'
                break
            if elapsed > protocol['wall_cap_seconds']:
                cap_reason = 'WALL_CAP'
                break
            time.sleep(0.2)
    finally:
        if child.poll() is None:
            child.terminate()
            try:
                child.wait(timeout=3)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait()
    returncode = child.wait()

elapsed = time.monotonic()-start
stdout_text = (HERE / 'solver_early.stdout').read_text(errors='replace')
if monitor_error:
    status = 'MONITOR_FAILURE'
elif cap_reason:
    status = cap_reason
elif 's SATISFIABLE' in stdout_text:
    status = 'SAT_MODEL_UNVERIFIED'
elif 's UNSATISFIABLE' in stdout_text:
    status = 'UNSAT_FORMULA_INCONSISTENT_WITH_WITNESS'
elif 's INDETERMINATE' in stdout_text:
    status = 'INDETERMINATE_SOLVER_CAP'
else:
    status = 'PRODUCER_FAILURE_NO_TERMINAL_STATUS'

restart_lines = [line for line in stdout_text.splitlines()
                 if line.startswith('c rst')]
result = {
    'status': status,
    'candidate_id': None,
    'one_worker': True,
    'solver_argv': protocol['solver_argv'],
    'solver_pid': child.pid,
    'returncode': returncode,
    'parent_wall_seconds': elapsed,
    'peak_sampled_solver_rss_bytes': peak_rss,
    'peak_sampled_process_tree_rss_bytes': peak_combined_rss,
    'rss_samples': samples,
    'cap_reason': cap_reason,
    'monitor_error': monitor_error,
    'last_restart_line': restart_lines[-1] if restart_lines else None,
    'stdout_sha256': sha(HERE / 'solver_early.stdout'),
    'stderr_sha256': sha(HERE / 'solver_early.stderr'),
    'protocol_sha256': sha(HERE / 'early_query_protocol.json'),
    'parent_self_maxrss_bytes': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
}
(HERE / 'early_query_result.json').write_text(json.dumps(result, sort_keys=True, indent=2)+'\n')
print(json.dumps({'status': status, 'returncode': returncode,
                  'seconds': elapsed, 'peak_rss': peak_rss}))
