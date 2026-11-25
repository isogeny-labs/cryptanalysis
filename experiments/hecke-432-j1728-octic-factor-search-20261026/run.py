"""Bounded PARI factor search with explicit timeout and exact replay checks."""
import json
import subprocess
import time
from hashlib import sha256
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / 'hecke-432-j1728-norm-power-20261026/power_certificate.json'
PARI = '/opt/homebrew/bin/gp'
TIMEOUT_SECONDS = 45


def main():
    source_bytes = SOURCE.read_bytes()
    source = json.loads(source_bytes)
    n = int(source['pair_resultant_8']['remaining_cofactor'])
    protocol = {
        'status': 'FROZEN_BEFORE_BOUNDED_PARI_SEARCH',
        'source_sha256': sha256(source_bytes).hexdigest(),
        'input_integer': str(n),
        'pari_command': 'factorint(n,8)',
        'pari_flag_meaning': 'skip final ECM; returned cofactors require independent primality checks',
        'timeout_seconds': TIMEOUT_SECONDS,
    }
    path = HERE / 'protocol.json'
    if not path.exists():
        path.write_text(json.dumps(protocol, sort_keys=True, indent=2) + '\n')
    assert json.loads(path.read_text()) == protocol
    gp_input = f'print(factorint({n},8))\n\\q\n'
    start = time.monotonic()
    try:
        run = subprocess.run([PARI, '-q'], input=gp_input, text=True,
                             capture_output=True, timeout=TIMEOUT_SECONDS)
        status = 'COMPLETED' if run.returncode == 0 else 'PARI_ERROR'
        stdout = run.stdout
        stderr = run.stderr
        returncode = run.returncode
    except subprocess.TimeoutExpired as exc:
        status = 'TIME_LIMIT'
        stdout = (exc.stdout or b'').decode(errors='replace')
        stderr = (exc.stderr or b'').decode(errors='replace')
        returncode = None
    receipt = {
        'status': status,
        'protocol_sha256': sha256(path.read_bytes()).hexdigest(),
        'source_sha256': sha256(Path(__file__).read_bytes()).hexdigest(),
        'elapsed_seconds': round(time.monotonic() - start, 3),
        'returncode': returncode,
        'stdout': stdout,
        'stderr': stderr,
    }
    (HERE / 'result.json').write_text(json.dumps(receipt, sort_keys=True, indent=2) + '\n')
    print(json.dumps({'status': status, 'elapsed_seconds': receipt['elapsed_seconds'],
                      'stdout': stdout[-1000:]}, sort_keys=True), flush=True)


if __name__ == '__main__':
    main()
