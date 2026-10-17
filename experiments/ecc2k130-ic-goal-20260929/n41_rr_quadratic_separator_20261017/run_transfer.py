"""Capped worker execution of the frozen N131 transfer experiment."""
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


protocol = json.loads((D / 'transfer_protocol.json').read_text())
assert protocol['producer_sha256'] == sha(D / 'transfer_n131.py')
run_protocol = {'transfer_protocol_sha256': sha(D / 'transfer_protocol.json'),
                'runner_sha256': sha(Path(__file__)),
                'command': [sys.executable, str(D / 'transfer_n131.py')],
                'one_worker': True, 'wall_cap_s': protocol['wall_cap_s'],
                'rss_cap_bytes': protocol['rss_cap_bytes']}
(D / 'transfer_run_protocol.json').write_text(json.dumps(run_protocol, sort_keys=True, indent=2) + '\n')
start = time.monotonic()
try:
    process = subprocess.run(run_protocol['command'], capture_output=True,
                             timeout=protocol['wall_cap_s'])
    stdout, stderr, exit_code = process.stdout, process.stderr, process.returncode
    timed_out = False
except subprocess.TimeoutExpired as exc:
    stdout, stderr, exit_code, timed_out = exc.stdout or b'', exc.stderr or b'', None, True
(D / 'transfer_worker.stdout').write_bytes(stdout)
(D / 'transfer_worker.stderr').write_bytes(stderr)
peak = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
result_path = D / 'transfer_result.json'
completed = (not timed_out and exit_code == 0 and result_path.exists() and
             json.loads(result_path.read_text()).get('status') == 'N131_FOUR_CHART_QUADRATIC_TRANSFER')
status = ('COMPLETE' if completed and peak < protocol['rss_cap_bytes']
          else 'RSS_BOUNDARY' if peak >= protocol['rss_cap_bytes']
          else 'BOUNDED_UNKNOWN' if timed_out else 'PRODUCER_FAILURE')
receipt = {'status': status, 'exit_code': exit_code, 'timed_out': timed_out,
           'wall_s': time.monotonic() - start, 'peak_child_rss_bytes': peak,
           'protocol_sha256': sha(D / 'transfer_run_protocol.json'),
           'stdout_sha256': sha(D / 'transfer_worker.stdout'),
           'stderr_sha256': sha(D / 'transfer_worker.stderr'),
           'result_sha256': sha(result_path) if completed else None}
(D / 'transfer_run_result.json').write_text(json.dumps(receipt, sort_keys=True, indent=2) + '\n')
print(json.dumps({k: receipt[k] for k in ('status', 'wall_s', 'peak_child_rss_bytes', 'exit_code')}))
