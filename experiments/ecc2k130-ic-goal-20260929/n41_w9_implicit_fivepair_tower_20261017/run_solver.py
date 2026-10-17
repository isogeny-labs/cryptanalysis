"""Bounded one-worker public-point SAT query with RSS and raw-output custody."""
import hashlib
import json
import os
import resource
import signal
import subprocess
import time
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parent
SOLVER = Path('/opt/homebrew/bin/cryptominisat5')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


protocol = json.loads((HERE / 'query_protocol.json').read_text())
for name, path in {
    'script': Path(__file__), 'runtime': HERE / 'query_runtime_info.json',
    'formula': HERE / 'formula.xcnf', 'build': HERE / 'build_result.json',
    'wires': HERE / 'input_wires.json', 'fixture': HERE / 'fixture.json',
    'solver': SOLVER,
}.items():
    assert sha(path) == protocol['source_sha256'][name], name
assert not (HERE / 'query_result.json').exists()
assert protocol['solver_argv'][0] == str(SOLVER)
assert protocol['solver_argv'][-1] == str(HERE / 'formula.xcnf')

start = time.monotonic()
peak_rss = 0
cap_reason = None
samples = 0
with (HERE / 'solver.stdout').open('xb') as stdout, \
     (HERE / 'solver.stderr').open('xb') as stderr:
    child = subprocess.Popen(protocol['solver_argv'], cwd=HERE,
                             stdout=stdout, stderr=stderr,
                             start_new_session=True)
    observed = psutil.Process(child.pid)
    while child.poll() is None:
        try:
            rss = observed.memory_info().rss
            for descendant in observed.children(recursive=True):
                rss += descendant.memory_info().rss
            peak_rss = max(peak_rss, rss)
            samples += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
        elapsed = time.monotonic()-start
        if peak_rss > protocol['rss_cap_bytes']:
            cap_reason = 'RSS_CAP'
        elif elapsed > protocol['wall_cap_seconds']:
            cap_reason = 'WALL_CAP'
        if cap_reason:
            try:
                os.killpg(child.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            try:
                child.wait(timeout=2)
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(child.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                child.wait()
            break
        time.sleep(0.2)
    returncode = child.wait()
elapsed = time.monotonic()-start
stdout_text = (HERE / 'solver.stdout').read_text(errors='replace')
if cap_reason:
    status = cap_reason
elif 's SATISFIABLE' in stdout_text:
    status = 'SAT_MODEL_UNVERIFIED'
elif 's UNSATISFIABLE' in stdout_text:
    status = 'UNSAT_FORMULA_INCONSISTENT_WITH_WITNESS'
elif 's INDETERMINATE' in stdout_text:
    status = 'INDETERMINATE_SOLVER_CAP'
else:
    status = 'PRODUCER_FAILURE_NO_TERMINAL_STATUS'

result = {
    'status': status,
    'candidate_id': None,
    'one_worker': True,
    'solver_argv': protocol['solver_argv'],
    'returncode': returncode,
    'parent_wall_seconds': elapsed,
    'peak_sampled_process_tree_rss_bytes': peak_rss,
    'rss_samples': samples,
    'cap_reason': cap_reason,
    'stdout_sha256': sha(HERE / 'solver.stdout'),
    'stderr_sha256': sha(HERE / 'solver.stderr'),
    'protocol_sha256': sha(HERE / 'query_protocol.json'),
    'parent_self_maxrss_bytes': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
}
(HERE / 'query_result.json').write_text(json.dumps(result, sort_keys=True, indent=2)+'\n')
print(json.dumps({'status': status, 'returncode': returncode,
                  'seconds': elapsed, 'peak_rss': peak_rss}))
