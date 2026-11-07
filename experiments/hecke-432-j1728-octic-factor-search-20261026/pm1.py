"""Bounded Pollard p-1 stage-one search on the pinned octic cofactor."""
import json
import math
import time
from hashlib import sha256
from pathlib import Path

from sympy import primerange

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / 'hecke-432-j1728-norm-power-20261026/power_certificate.json'
BOUNDS = [10000, 100000, 1000000]
BASES = [2, 3]


def main():
    source_bytes = SOURCE.read_bytes()
    n = int(json.loads(source_bytes)['pair_resultant_8']['remaining_cofactor'])
    protocol = {
        'status': 'FROZEN_BEFORE_PM1_SEARCH',
        'source_sha256': sha256(source_bytes).hexdigest(),
        'input_integer': str(n),
        'bounds': BOUNDS,
        'bases': BASES,
        'algorithm': 'stage-one prime-power exponent for each bound, independent base per attempt',
    }
    path = HERE / 'pm1_protocol.json'
    if not path.exists():
        path.write_text(json.dumps(protocol, sort_keys=True, indent=2) + '\n')
    assert json.loads(path.read_text()) == protocol
    rows = []
    for bound in BOUNDS:
        prime_powers = []
        for raw in primerange(2, bound + 1):
            prime = int(raw)
            q = prime
            while q * prime <= bound:
                q *= prime
            prime_powers.append(q)
        for base in BASES:
            start = time.monotonic()
            a = base
            for q in prime_powers:
                a = pow(a, q, n)
            divisor = math.gcd(a - 1, n)
            row = {'bound': bound, 'base': base, 'primes': len(prime_powers),
                   'elapsed_seconds': round(time.monotonic() - start, 3),
                   'gcd': str(divisor),
                   'status': 'FACTOR' if 1 < divisor < n else 'NO_PROPER_FACTOR'}
            assert n % divisor == 0
            rows.append(row)
    receipt = {
        'status': 'COMPLETED_BOUNDED_PM1_SEARCH',
        'protocol_sha256': sha256(path.read_bytes()).hexdigest(),
        'source_sha256': sha256(Path(__file__).read_bytes()).hexdigest(),
        'rows': rows,
    }
    (HERE / 'pm1_result.json').write_text(json.dumps(receipt, sort_keys=True, indent=2) + '\n')
    print(json.dumps({'status': receipt['status'],
                      'proper_factors': [r for r in rows if r['status'] == 'FACTOR']},
                     sort_keys=True), flush=True)


if __name__ == '__main__':
    main()
