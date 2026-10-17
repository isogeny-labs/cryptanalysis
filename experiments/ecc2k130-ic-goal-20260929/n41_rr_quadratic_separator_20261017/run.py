"""One-worker capped execution of the frozen quadratic family screen."""
import hashlib
import json
import resource
import subprocess
import sys
import time
from pathlib import Path

D = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


base = json.loads((D / 'protocol.json').read_text())
assert base['producer_sha256'] == sha(D / 'screen.py')
run_protocol = {'base_protocol_sha256': sha(D / 'protocol.json'),
                'runner_sha256': sha(Path(__file__)),
                'producer_sha256': sha(D / 'screen.py'),
                'command': [sys.executable, str(D / 'screen.py')],
                'one_worker': True,
                'parent_wall_cap_s': base['wall_cap_s'],
                'rss_boundary_bytes': base['rss_cap_bytes']}
(D / 'run_protocol.json').write_text(json.dumps(run_protocol, indent=2, sort_keys=True) + '\n')
start = time.monotonic()
try:
    process = subprocess.run(run_protocol['command'], capture_output=True,
                             timeout=base['wall_cap_s'])
    stdout, stderr, exit_code = process.stdout, process.stderr, process.returncode
    parent_cap = False
except subprocess.TimeoutExpired as exc:
    stdout, stderr, exit_code = exc.stdout or b'', exc.stderr or b'', None
    parent_cap = True
wall = time.monotonic() - start
(D / 'worker.stdout').write_bytes(stdout)
(D / 'worker.stderr').write_bytes(stderr)
peak = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
result_path = D / 'result.json'
completed = (not parent_cap and exit_code == 0 and result_path.exists()
             and json.loads(result_path.read_text()).get('status') ==
             'QUADRATIC_FAMILY_SCREEN_COMPLETE')
status = ('COMPLETE' if completed and peak < base['rss_cap_bytes']
          else 'RSS_BOUNDARY' if peak >= base['rss_cap_bytes']
          else 'BOUNDED_UNKNOWN' if parent_cap else 'PRODUCER_FAILURE')
receipt = {'status': status, 'exit_code': exit_code, 'parent_cap': parent_cap,
           'wall_s': wall, 'peak_child_rss_bytes': peak,
           'protocol_sha256': sha(D / 'run_protocol.json'),
           'stdout_sha256': sha(D / 'worker.stdout'),
           'stderr_sha256': sha(D / 'worker.stderr'),
           'result_sha256': sha(result_path) if completed else None}
(D / 'run_result.json').write_text(json.dumps(receipt, indent=2, sort_keys=True) + '\n')
print(json.dumps({k: receipt[k] for k in ('status', 'wall_s',
                                          'peak_child_rss_bytes', 'exit_code')}))
