"""One-worker capped run of root-balanced certificate fitting."""
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


protocol = json.loads((D / 'protocol.json').read_text())
assert protocol['producer_sha256'] == sha(D / 'fit.py')
command = [sys.executable, str(D / 'fit.py')]
start = time.monotonic()
try:
    process = subprocess.run(command, capture_output=True, timeout=protocol['wall_cap_s'])
    stdout, stderr, code, timed_out = process.stdout, process.stderr, process.returncode, False
except subprocess.TimeoutExpired as exc:
    stdout, stderr, code, timed_out = exc.stdout or b'', exc.stderr or b'', None, True
(D / 'worker.stdout').write_bytes(stdout)
(D / 'worker.stderr').write_bytes(stderr)
peak = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
result_path = D / 'result.json'
complete = (not timed_out and code == 0 and result_path.exists() and
            json.loads(result_path.read_text()).get('status') == 'ROOT_BALANCED_FOUR_CODE_CERTIFICATE')
status = ('COMPLETE' if complete and peak < protocol['rss_cap_bytes']
          else 'RSS_BOUNDARY' if peak >= protocol['rss_cap_bytes']
          else 'BOUNDED_UNKNOWN' if timed_out else 'PRODUCER_FAILURE')
receipt = {'status': status, 'protocol_sha256': sha(D / 'protocol.json'),
           'runner_sha256': sha(Path(__file__)), 'command': command,
           'exit_code': code, 'timed_out': timed_out,
           'wall_s': time.monotonic()-start, 'peak_child_rss_bytes': peak,
           'stdout_sha256': sha(D / 'worker.stdout'),
           'stderr_sha256': sha(D / 'worker.stderr'),
           'result_sha256': sha(result_path) if complete else None}
(D / 'run_result.json').write_text(json.dumps(receipt, sort_keys=True, indent=2)+'\n')
print(json.dumps({k:receipt[k] for k in ('status','wall_s','peak_child_rss_bytes','exit_code')}))
