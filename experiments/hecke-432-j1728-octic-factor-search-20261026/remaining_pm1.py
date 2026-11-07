"""One bounded p-1 continuation on the exact 210-digit residual."""
import json
import math
import time
from hashlib import sha256
from pathlib import Path

from sympy import primerange

HERE = Path(__file__).resolve().parent
SOURCE = HERE / 'prime_result.json'
BOUND = 1000000
BASES = [2, 3]


def main():
    source_bytes = SOURCE.read_bytes()
    n = int(json.loads(source_bytes)['remaining_cofactor'])
    protocol = {'status': 'FROZEN_BEFORE_REMAINING_PM1',
                'source_sha256': sha256(source_bytes).hexdigest(),
                'input_integer': str(n), 'bound': BOUND, 'bases': BASES,
                'algorithm': 'stage-one prime-power exponent'}
    path = HERE / 'remaining_pm1_protocol.json'
    if not path.exists():
        path.write_text(json.dumps(protocol, sort_keys=True, indent=2) + '\n')
    assert json.loads(path.read_text()) == protocol
    powers = []
    for raw in primerange(2, BOUND + 1):
        prime = int(raw)
        q = prime
        while q * prime <= BOUND:
            q *= prime
        powers.append(q)
    rows = []
    for base in BASES:
        start = time.monotonic()
        a = base
        for q in powers:
            a = pow(a, q, n)
        d = math.gcd(a - 1, n)
        assert n % d == 0
        rows.append({'base': base, 'bound': BOUND, 'primes': len(powers),
                     'gcd': str(d), 'status': 'FACTOR' if 1 < d < n else 'NO_PROPER_FACTOR',
                     'elapsed_seconds': round(time.monotonic() - start, 3)})
    out = {'status': 'COMPLETED_REMAINING_PM1',
           'protocol_sha256': sha256(path.read_bytes()).hexdigest(),
           'source_sha256': sha256(Path(__file__).read_bytes()).hexdigest(),
           'rows': rows}
    (HERE / 'remaining_pm1_result.json').write_text(json.dumps(out, sort_keys=True, indent=2) + '\n')
    print(json.dumps(out, sort_keys=True), flush=True)


if __name__ == '__main__':
    main()
