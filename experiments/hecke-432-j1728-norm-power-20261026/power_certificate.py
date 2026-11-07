"""Exact perfect-power certificates and bounded factors of norm numerators."""
import json
from hashlib import sha256
from pathlib import Path

from sympy import integer_nthroot, primerange

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
GATE = ROOT / 'experiments/hecke-432-j1728-sqrt2-resultants-20261026/bridge_gate.json'


def nth_power(n, exponent):
    assert n > 0
    root, exact = integer_nthroot(n, exponent)
    assert exact and root ** exponent == n
    return int(root)


def bounded_factors(n, cap):
    factors = []
    remaining = n
    for raw in primerange(2, cap):
        p = int(raw)
        if remaining % p:
            continue
        exponent = 0
        while remaining % p == 0:
            remaining //= p
            exponent += 1
        factors.append([p, exponent])
    assert n == remaining * int_product(p ** exponent for p, exponent in factors)
    return factors, remaining


def int_product(values):
    result = 1
    for value in values:
        result *= value
    return result


def main():
    pp = HERE / 'protocol.json'
    protocol = json.loads(pp.read_text())
    assert protocol['status'] == 'FROZEN_BEFORE_REGISTERED_POWER_AND_FIBER_REPLAY'
    assert sha256(GATE.read_bytes()).hexdigest() == protocol['input_sha256']['bridge_gate']
    gate = json.loads(GATE.read_text())
    norms = {row['name']: row for row in gate['norms']}
    base = nth_power(abs(int(norms['base_unit']['numerator'])), 6)
    quartic = nth_power(abs(int(norms['pair_resultant_4']['numerator'])), 3)
    octic = nth_power(abs(int(norms['pair_resultant_8']['numerator'])), 3)
    assert base == 3 ** 138
    frozen_factors = protocol['frozen_factorization_of_quartic_cube_root']
    assert quartic == int_product(p ** exponent for p, exponent in frozen_factors)
    assert protocol['large_prime'] in [p for p, _ in frozen_factors]
    assert protocol['large_prime'] % 24 == protocol['large_prime_class_mod_24']
    octic_small, octic_cofactor = bounded_factors(octic, 10000000)
    out = {
        'status': 'EXACT_NORM_POWER_AND_QUARTIC_FACTOR_CERTIFICATE',
        'protocol_sha256': sha256(pp.read_bytes()).hexdigest(),
        'source_sha256': sha256(Path(__file__).read_bytes()).hexdigest(),
        'input_gate_sha256': sha256(GATE.read_bytes()).hexdigest(),
        'base_unit': {'exponent': 6, 'root': str(base), 'root_factorization': [[3, 138]]},
        'pair_resultant_4': {'exponent': 3, 'root': str(quartic),
                             'root_factorization': frozen_factors,
                             'factorization_complete_pending_primality_check': True},
        'pair_resultant_8': {'exponent': 3, 'root': str(octic),
                             'factors_below_10000000': octic_small,
                             'remaining_cofactor': str(octic_cofactor),
                             'remaining_cofactor_digits': len(str(octic_cofactor))},
    }
    (HERE / 'power_certificate.json').write_text(
        json.dumps(out, sort_keys=True, indent=2) + '\n')
    print(json.dumps({'status': out['status'],
                      'quartic_cube_root_digits': len(str(quartic)),
                      'octic_cube_root_digits': len(str(octic)),
                      'octic_cofactor_digits': len(str(octic_cofactor))},
                     sort_keys=True))


if __name__ == '__main__':
    main()
