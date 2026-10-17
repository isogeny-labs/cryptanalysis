"""Bounded one-worker public-point CryptoMiniSat query with raw logs."""
import hashlib
import json
import resource
import subprocess
import time
from pathlib import Path

D = Path(__file__).resolve().parent

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

base = json.loads((D/'protocol_v2.json').read_text())
build = json.loads((D/'build_result_v2.json').read_text())
formula = D/'formula_v2.xcnf'
assert build['status'] == 'BUILD_AND_WITNESS_PASS_SELECTED_ROW'
assert build['protocol_sha256'] == sha(D/'protocol_v2.json')
assert build['formula_sha256'] == sha(formula)
solver = Path(base['solver_path'])
assert base['solver_sha256'] == sha(solver)
flags = ['--threads=1', '--maxtime=180', '--zero-exit-status',
         '--verb=1', '--printsol=1']
protocol = {'base_protocol_sha256': sha(D/'protocol_v2.json'),
            'build_result_sha256': sha(D/'build_result_v2.json'),
            'formula_sha256': sha(formula),
            'solver_sha256': sha(solver), 'solver_path': str(solver),
            'solver_flags': flags, 'one_worker': True,
            'parent_wall_cap_s': 185, 'rss_boundary_bytes': 4294967296}
(D/'query_protocol_v2.json').write_text(json.dumps(protocol, indent=2, sort_keys=True)+'\n')
command = [str(solver)] + flags + [str(formula)]
start = time.monotonic()
try:
    process = subprocess.run(command, capture_output=True, timeout=185)
    stdout = process.stdout
    stderr = process.stderr
    exit_code = process.returncode
    parent_cap = False
except subprocess.TimeoutExpired as exc:
    stdout = exc.stdout or b''
    stderr = exc.stderr or b''
    exit_code = None
    parent_cap = True
wall = time.monotonic()-start
(D/'solver_v2.stdout').write_bytes(stdout)
(D/'solver_v2.stderr').write_bytes(stderr)
lines = stdout.decode('utf-8', errors='replace').splitlines()
terminal = [line for line in lines if line.startswith('s ') or line.startswith('c [result]')]
sat = any(line.startswith('s SATISFIABLE') for line in terminal)
unsat = any(line.startswith('s UNSATISFIABLE') for line in terminal)
assert not (sat and unsat)
status = 'SAT_PENDING_GROUP_REPLAY' if sat else 'UNSAT_FORMULA' if unsat else 'BOUNDED_UNKNOWN'
result = {'status': status, 'parent_cap': parent_cap,
          'exit_code': exit_code, 'wall_s': wall,
          'peak_child_rss_bytes': resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss,
          'terminal_lines': terminal, 'command': command,
          'protocol_sha256': sha(D/'query_protocol_v2.json'),
          'stdout_sha256': sha(D/'solver_v2.stdout'),
          'stderr_sha256': sha(D/'solver_v2.stderr')}
(D/'query_result_v2.json').write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')
print(json.dumps({k: result[k] for k in ('status','parent_cap','exit_code','wall_s','peak_child_rss_bytes','terminal_lines')}))
