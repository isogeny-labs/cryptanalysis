"""Bound and receipt checked-Sage prediction or right observation stages."""
import json
import subprocess
import sys
import time
from hashlib import sha256
from pathlib import Path

HERE = Path(__file__).resolve().parent
SAGE = '/Volumes/SSD990/cryptanalysis/sage'


def main():
    assert len(sys.argv) == 2 and sys.argv[1] in ('predict', 'fallback', 'observe', 'taylor')
    stage = sys.argv[1]
    protocol_path = HERE / {'predict': 'protocol.json',
                            'fallback': 'fallback_protocol.json',
                            'observe': 'observation_protocol.json',
                            'taylor': 'taylor_protocol.json'}[stage]
    protocol = json.loads(protocol_path.read_text())
    source_path = HERE / (stage + '_sage.py')
    command = [SAGE, '-python', str(source_path)]
    started = time.monotonic()
    try:
        run = subprocess.run(command, capture_output=True, text=True,
                             timeout=protocol['prediction_timeout_seconds'] if stage == 'predict'
                             else protocol['timeout_seconds'] if stage in ('fallback', 'taylor')
                             else protocol['observation_timeout_seconds'])
        status = 'COMPLETED' if run.returncode == 0 else 'SAGE_ERROR'
        stdout, stderr, returncode = run.stdout, run.stderr, run.returncode
    except subprocess.TimeoutExpired as exc:
        status = 'TIME_LIMIT'
        stdout = (exc.stdout or b'').decode(errors='replace')
        stderr = (exc.stderr or b'').decode(errors='replace')
        returncode = None
    out = {'status': status, 'command': command,
           'elapsed_seconds': round(time.monotonic() - started, 3),
           'protocol_sha256': sha256(protocol_path.read_bytes()).hexdigest(),
           'source_sha256': sha256(source_path.read_bytes()).hexdigest(),
           'returncode': returncode, 'stdout': stdout, 'stderr': stderr}
    (HERE / (stage + '_attempt.json')).write_text(json.dumps(out, sort_keys=True, indent=2) + '\n')
    print(json.dumps({'status': status, 'elapsed_seconds': out['elapsed_seconds'],
                      'stdout_tail': stdout[-1300:], 'stderr_tail': stderr[-1300:]},
                     sort_keys=True))


if __name__ == '__main__':
    main()
