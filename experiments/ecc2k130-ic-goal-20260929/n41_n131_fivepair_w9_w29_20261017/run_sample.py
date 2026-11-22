"""Run and retain the frozen W29 source sample."""
import hashlib
import json
import subprocess
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parent.parent / 'koblitz-s5-invariant-20260924/lowpoly_w23_geometry.cpp'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


protocol_path = HERE / 'sample_protocol.json'
protocol = json.loads(protocol_path.read_text())
paths = {'sample_w29.cpp': HERE / 'sample_w29.cpp',
         'sample_w29': HERE / 'sample_w29',
         'lowpoly_w23_geometry.cpp': KERNEL,
         'sage_runtime_info.json': HERE / 'sage_runtime_info.json'}
for name, digest in protocol['source_sha256'].items():
    assert sha(paths[name]) == digest
start = time.monotonic_ns()
try:
    process = subprocess.run([str(HERE / 'sample_w29')], capture_output=True,
                             timeout=protocol['wall_cap_seconds'])
    outcome = 'COMPLETE' if process.returncode == 0 else 'PRODUCER_FAILURE'
    stdout, stderr, exit_code = process.stdout, process.stderr, process.returncode
except subprocess.TimeoutExpired as exc:
    outcome = 'BOUNDED_UNKNOWN'
    stdout, stderr, exit_code = exc.stdout or b'', exc.stderr or b'', None
elapsed = (time.monotonic_ns() - start) / 1e9
(HERE / 'sample.stdout').write_bytes(stdout)
(HERE / 'sample.stderr').write_bytes(stderr)
data = json.loads(stdout) if outcome == 'COMPLETE' else None
result = {'status': outcome, 'sample': data, 'exit_code': exit_code,
          'parent_wall_seconds': elapsed,
          'protocol_sha256': sha(protocol_path),
          'stdout_sha256': sha(HERE / 'sample.stdout'),
          'stderr_sha256': sha(HERE / 'sample.stderr')}
with (HERE / 'sample_result.json').open('x') as out:
    json.dump(result, out, sort_keys=True, indent=2)
    out.write('\n')
print(json.dumps(result, sort_keys=True))
