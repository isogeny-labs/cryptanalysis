"""Exact gcd and bounded prime-support replay for the discriminant roots."""
import json
import sys
from hashlib import sha256
from math import gcd, prod
from pathlib import Path

from sympy import primerange

sys.set_int_max_str_digits(10000)
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def divide_small_primes(n, primes):
    factors = []
    for p in primes:
        exponent = 0
        while n % p == 0:
            n //= p
            exponent += 1
        if exponent:
            factors.append([int(p), exponent])
    return factors, n


def main():
    protocol_path = HERE / 'protocol.json'
    protocol = json.loads(protocol_path.read_text())
    source = ROOT / protocol['input_path']
    assert sha256(source.read_bytes()).hexdigest() == protocol['input_sha256']
    saved = json.loads(source.read_text())
    assert saved['status'] == 'PASS_RELATIVE_DISCRIMINANT_PRODUCT_AND_SIXTH_POWER'
    primes = list(primerange(2, protocol['prime_cap_inclusive'] + 1))
    rows = []
    for r in saved['rows']:
        a = int(r['relative_discriminant_sixth_root'])
        b = int(r['pair_resultant_norm_cube_root'])
        g = gcd(a, b)
        gf, residual_g = divide_small_primes(g, primes)
        assert residual_g == 1
        af, residual_a = divide_small_primes(a, primes)
        bf, residual_b = divide_small_primes(b, primes)
        assert gcd(residual_a, residual_b) == 1
        assert a == residual_a * prod(p ** e for p, e in af)
        assert b == residual_b * prod(p ** e for p, e in bf)
        assert g == prod(p ** e for p, e in gf)
        rows.append({'base_degree': r['base_degree'],
                     'relative_root_digits': len(str(a)),
                     'pair_root_digits': len(str(b)),
                     'exact_common_gcd': str(g),
                     'complete_common_gcd_factorization': gf,
                     'relative_root_small_prime_factors': af,
                     'relative_root_residual': str(residual_a),
                     'pair_root_small_prime_factors': bf,
                     'pair_root_residual': str(residual_b),
                     'residuals_coprime': True})
    out = {'status': 'PASS_EXACT_COMMON_PRIME_SUPPORT',
           'protocol_sha256': sha256(protocol_path.read_bytes()).hexdigest(),
           'source_sha256': sha256(Path(__file__).read_bytes()).hexdigest(),
           'small_prime_cap_inclusive': protocol['prime_cap_inclusive'],
           'rows': rows}
    (HERE / 'result.json').write_text(json.dumps(out, sort_keys=True, indent=2) + '\n')
    print(json.dumps({'status': out['status'],
                      'gcd_factors': {str(r['base_degree']): r['complete_common_gcd_factorization']
                                      for r in rows}}, sort_keys=True))


if __name__ == '__main__':
    main()
