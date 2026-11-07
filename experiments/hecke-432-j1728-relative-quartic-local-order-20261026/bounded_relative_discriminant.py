"""Bound one exact relative discriminant ideal computation."""
import argparse
import json
import subprocess
import time
from hashlib import sha256
from pathlib import Path

HERE = Path(__file__).resolve().parent
SAGE = '/Volumes/SSD990/cryptanalysis/sage'


def main(side):
    protocol_path = HERE / 'relative_discriminant_protocol.json'
    protocol = json.loads(protocol_path.read_text())
    command = [SAGE, '-python', str(HERE / 'relative_discriminant_sage.py'), '--side', str(side)]
    start = time.monotonic()
    try:
        run = subprocess.run(command, capture_output=True, text=True,
                             timeout=protocol['timeout_seconds_per_side'])
        status = 'COMPLETED' if run.returncode == 0 else 'SAGE_ERROR'
        stdout, stderr, returncode = run.stdout, run.stderr, run.returncode
    except subprocess.TimeoutExpired as exc:
        status = 'TIME_LIMIT'
        stdout = (exc.stdout or b'').decode(errors='replace')
        stderr = (exc.stderr or b'').decode(errors='replace')
        returncode = None
    receipt = {'status': status, 'command': command,
               'protocol_sha256': sha256(protocol_path.read_bytes()).hexdigest(),
               'source_sha256': sha256((HERE / 'relative_discriminant_sage.py').read_bytes()).hexdigest(),
               'elapsed_seconds': round(time.monotonic() - start, 3),
               'returncode': returncode, 'stdout': stdout, 'stderr': stderr}
    (HERE / f'relative_discriminant_attempt_side{side}.json').write_text(
        json.dumps(receipt, sort_keys=True, indent=2) + '\n')
    print(json.dumps({'side': side, 'status': status,
                      'elapsed_seconds': receipt['elapsed_seconds'],
                      'stdout_tail': stdout[-700:], 'stderr_tail': stderr[-700:]}, sort_keys=True))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--side', type=int, choices=(0, 1), required=True)
    main(parser.parse_args().side)
