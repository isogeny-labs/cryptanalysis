"""Frozen one-worker unpinned N41 public-point solver query."""
import hashlib
import json
import resource
import subprocess
import time
from pathlib import Path

D = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


base = json.loads((D / 'protocol.json').read_text())
build = json.loads((D / 'build_result.json').read_text())
formula = D / 'formula.xcnf'
assert build['status'] == 'BUILD_AND_ALL_960_STATE_COVERAGE_PASS'
assert build['protocol_sha256'] == sha(D / 'protocol.json')
assert build['formula_sha256'] == sha(formula)
solver = Path(base['solver_path'])
assert base['solver_sha256'] == sha(solver)
flags = ['--threads=1', '--maxtime=180', '--zero-exit-status',
         '--verb=1', '--printsol=1']
protocol = {'base_protocol_sha256': sha(D / 'protocol.json'),
            'build_result_sha256': sha(D / 'build_result.json'),
            'formula_sha256': sha(formula),
            'query_runner_sha256': sha(Path(__file__)),
            'solver_sha256': sha(solver), 'solver_path': str(solver),
            'solver_flags': flags, 'one_worker': True,
            'parent_wall_cap_s': 185, 'rss_boundary_bytes': 4 * 1024**3}
(D / 'query_protocol.json').write_text(json.dumps(protocol, indent=2, sort_keys=True) + '\n')
command = [str(solver)] + flags + [str(formula)]
start = time.monotonic()
try:
    process = subprocess.run(command, capture_output=True, timeout=185)
    stdout, stderr, exit_code = process.stdout, process.stderr, process.returncode
    parent_cap = False
except subprocess.TimeoutExpired as exc:
    stdout, stderr, exit_code = exc.stdout or b'', exc.stderr or b'', None
    parent_cap = True
wall = time.monotonic() - start
(D / 'solver.stdout').write_bytes(stdout)
(D / 'solver.stderr').write_bytes(stderr)
terminal = [line for line in stdout.decode('utf-8', errors='replace').splitlines()
            if line.startswith('s ') or line.startswith('c [result]')]
sat = any(line.startswith('s SATISFIABLE') for line in terminal)
unsat = any(line.startswith('s UNSATISFIABLE') for line in terminal)
assert not (sat and unsat)
status = 'SAT_PENDING_GROUP_REPLAY' if sat else 'UNSAT_FORMULA' if unsat else 'BOUNDED_UNKNOWN'
result = {'status': status, 'parent_cap': parent_cap,
          'exit_code': exit_code, 'wall_s': wall,
          'peak_child_rss_bytes': resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss,
          'terminal_lines': terminal, 'command': command,
          'protocol_sha256': sha(D / 'query_protocol.json'),
          'stdout_sha256': sha(D / 'solver.stdout'),
          'stderr_sha256': sha(D / 'solver.stderr')}
(D / 'query_result.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
print(json.dumps({k: result[k] for k in ('status', 'parent_cap',
                                        'exit_code', 'wall_s',
                                        'peak_child_rss_bytes', 'terminal_lines')}))
