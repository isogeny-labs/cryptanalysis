"""Launch the exact Sage job through the checked repository launcher."""
import json
import subprocess
import time
from hashlib import sha256
from pathlib import Path

HERE = Path(__file__).resolve().parent
SAGE = '/Volumes/SSD990/cryptanalysis/sage'


def main():
    path = HERE / 'exact_protocol.json'
    protocol = json.loads(path.read_text())
    assert protocol['status'] == 'FROZEN_BEFORE_EXACT_SOURCE_FIELD_RESULTANT_IDENTITY'
    command = [SAGE, '-python', str(HERE / 'exact_field_sage.py')]
    start = time.monotonic()
    try:
        run = subprocess.run(command, text=True, capture_output=True,
                             timeout=protocol['timeout_seconds'])
        status = 'COMPLETED' if run.returncode == 0 else 'SAGE_ERROR'
        stdout, stderr, returncode = run.stdout, run.stderr, run.returncode
    except subprocess.TimeoutExpired as exc:
        status = 'TIME_LIMIT'
        stdout = (exc.stdout or b'').decode(errors='replace')
        stderr = (exc.stderr or b'').decode(errors='replace')
        returncode = None
    out = {'status': status,
           'protocol_sha256': sha256(path.read_bytes()).hexdigest(),
           'source_sha256': sha256(Path(__file__).read_bytes()).hexdigest(),
           'command': command,
           'elapsed_seconds': round(time.monotonic() - start, 3),
           'returncode': returncode, 'stdout': stdout, 'stderr': stderr}
    (HERE / 'exact_attempt.json').write_text(json.dumps(out, sort_keys=True, indent=2) + '\n')
    print(json.dumps({'status': status, 'elapsed_seconds': out['elapsed_seconds'],
                      'stdout_tail': stdout[-500:], 'stderr_tail': stderr[-500:]},
                     sort_keys=True), flush=True)


if __name__ == '__main__':
    main()
