"""Bounded first-instruction launch comparison for native W9 binaries."""
import hashlib
import json
import subprocess
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
PRIOR = HERE.parent / 'n41_n131_fivepair_w9_w29_20261017'
BINARIES = [('frozen_original_path', PRIOR / 'join_orbit'),
            ('copied_original_binary', HERE / 'join_orbit_copy'),
            ('new_target_join_binary', HERE / 'join_target_conditioned')]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


rows = []
for label, path in BINARIES:
    start = time.monotonic_ns()
    try:
        run = subprocess.run([str(path)], capture_output=True,
                             text=True, timeout=5, check=False)
        status = 'EXITED'
        returncode = run.returncode
        stdout, stderr = run.stdout, run.stderr
    except subprocess.TimeoutExpired as error:
        status = 'TIMEOUT_AT_FIVE_SECONDS'
        returncode = None
        stdout = error.stdout.decode(errors='replace') if error.stdout else ''
        stderr = error.stderr.decode(errors='replace') if error.stderr else ''
    row = {'label': label, 'status': status,
           'returncode': returncode, 'elapsed_ns': time.monotonic_ns() - start,
           'binary_sha256': sha(path), 'stdout': stdout, 'stderr': stderr}
    rows.append(row)
    print(json.dumps(row), flush=True)
result = {'status': 'COMPLETE_BOUNDED_NATIVE_LAUNCH_DIAGNOSTIC',
          'input_policy': 'no arguments; each binary should immediately exit with usage error',
          'rows': rows, 'script_sha256': sha(Path(__file__)),
          'target_join_protocol_sha256': sha(HERE / 'target_join_protocol.json'),
          'interrupted_query_stdout_sha256': sha(HERE / 'target_join.stdout'),
          'interrupted_query_stderr_sha256': sha(HERE / 'target_join.stderr')}
with (HERE / 'launch_diagnostic.json').open('x') as out:
    json.dump(result, out, sort_keys=True, indent=2)
    out.write('\n')
