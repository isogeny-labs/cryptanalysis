"""Bound and receipt the independently scripted quartic observation."""
import json
import subprocess
import time
from hashlib import sha256
from pathlib import Path

HERE = Path(__file__).resolve().parent
SAGE = '/Volumes/SSD990/cryptanalysis/sage'


def main():
    seal_path = HERE / 'observation_protocol.json'
    seal = json.loads(seal_path.read_text())
    source_path = HERE / 'observe_sage.py'
    command = [SAGE, '-python', str(source_path)]
    started = time.monotonic()
    try:
        run = subprocess.run(command, capture_output=True, text=True,
                             timeout=seal['timeout_seconds'])
        status = 'COMPLETED' if run.returncode == 0 else 'SAGE_ERROR'
        stdout, stderr, returncode = run.stdout, run.stderr, run.returncode
    except subprocess.TimeoutExpired as exc:
        status = 'TIME_LIMIT'
        stdout = (exc.stdout or b'').decode(errors='replace')
        stderr = (exc.stderr or b'').decode(errors='replace')
        returncode = None
    out = {'status': status, 'command': command,
           'elapsed_seconds': round(time.monotonic() - started, 3),
           'observation_protocol_sha256': sha256(seal_path.read_bytes()).hexdigest(),
           'source_sha256': sha256(source_path.read_bytes()).hexdigest(),
           'returncode': returncode, 'stdout': stdout, 'stderr': stderr}
    (HERE / 'observation_attempt.json').write_text(json.dumps(out, sort_keys=True, indent=2) + '\n')
    print(json.dumps({'status': status, 'elapsed_seconds': out['elapsed_seconds'],
                      'stdout_tail': stdout[-1000:], 'stderr_tail': stderr[-1000:]},
                     sort_keys=True))


if __name__ == '__main__':
    main()
