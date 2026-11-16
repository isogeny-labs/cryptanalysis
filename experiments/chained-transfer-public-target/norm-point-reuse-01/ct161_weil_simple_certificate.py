#!/usr/bin/env python3
"""CT161 fixed-nu12 F_223 Weil-restriction irreducibility certificate.

Pure-Python finite-field arithmetic; checks the CT160 fixed census schema.
Not a Jacobian native execution, benchmark, or signed PCC verification.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

P = 5
Q = 223
T = 2724
ORDER = 11086844
CENSUS = 'CT160_FULL_CENSUS.json'


def require(ok, why):
    if not ok:
        raise ValueError('CT161 rejected: ' + why)


def strict_json(path):
    def no_duplicates(pairs):
        out = {}
        for k, v in pairs:
            require(k not in out, 'duplicate key: ' + k)
            out[k] = v
        return out

    def reject_constant(s):
        raise ValueError('CT161 rejected: invalid JSON constant ' + s)

    raw = Path(path).read_bytes()
    obj = json.loads(raw, object_pairs_hook=no_duplicates, parse_constant=reject_constant)
    return obj, hashlib.sha256(raw).hexdigest()


def check_census(d):
    require(type(d) is dict and d.get('schema') == 'ct160-fixed-nu12-whole-field-census/v1',
            'CT160 census schema')
    require(type(d.get('field_cardinality')) is int and d['field_cardinality'] == Q**3,
            'field cardinality')
    for name in ('actual_fixed_nu12_source', 'actual_fixed_nu12_target'):
        row = d.get(name)
        require(type(row) is dict, 'missing ' + name)
        for k, val in (('zeros', 3), ('nonzero_squares', 5543420),
                       ('nonsquares', 5546144), ('order', ORDER)):
            require(type(row.get(k)) is int and row[k] == val, name + '/' + k)
        require(row['zeros'] + row['nonzero_squares'] + row['nonsquares'] == Q**3,
                name + '/RHS partition')
        require(1 + row['zeros'] + 2 * row['nonzero_squares'] == row['order'],
                name + '/point count')
    require(d.get('mutant') is False and d.get('accepted') is True,
            'expected nominal, accepted CT160 census')
    require(Q**3 + 1 - ORDER == T, 'trace vs count')


def norm(a):
    a = [int(i) % P for i in a]
    while a and a[-1] == 0:
        a.pop()
    return a


def subtract(a, b):
    return norm([(a[i] if i < len(a) else 0) - (b[i] if i < len(b) else 0)
                 for i in range(max(len(a), len(b)))])


def mul(a, b):
    if not a or not b:
        return []
    c = [0] * (len(a) + len(b) - 1)
    for i, x in enumerate(a):
        for j, y in enumerate(b):
            c[i + j] = (c[i + j] + x*y) % P
    return norm(c)


def quotient_remainder(a, b):
    a, b = norm(a), norm(b)
    require(b, 'division by zero polynomial')
    if len(a) < len(b):
        return [], a
    quot = [0] * (len(a)-len(b)+1)
    lead_inv = pow(b[-1], -1, P)
    while a and len(a) >= len(b):
        k = len(a)-len(b)
        coeff = a[-1]*lead_inv % P
        quot[k] = coeff
        for i, val in enumerate(b):
            a[i+k] = (a[i+k]-coeff*val) % P
        a = norm(a)
    return norm(quot), a


def remainder(a, b):
    return quotient_remainder(a, b)[1]


def power_mod(base, n, modulus):
    require(type(n) is int and n >= 0, 'invalid power')
    z = [1]
    base = remainder(base, modulus)
    while n:
        if n & 1:
            z = remainder(mul(z, base), modulus)
        base = remainder(mul(base, base), modulus)
        n //= 2
    return z


def monic_gcd(a, b):
    while b:
        a, b = b, remainder(a, b)
    if not a:
        return []
    k = pow(a[-1], -1, P)
    return norm([(k*x) % P for x in a])


def certificate(trace=T, field=Q):
    # Coefficients are listed in ascending order. Reduction modulo 5 is legal
    # because the integer Weil polynomial is monic.
    integer_coeffs = [field**3, 0, 0, -trace, 0, 0, 1]
    f = norm(integer_coeffs)
    require(len(f) == 7 and f[-1] == 1, 'degree-six monic polynomial required')
    x = [0, 1]
    frob = x
    powers = {}
    for i in range(1, 7):
        frob = power_mod(frob, P, f)
        if i in (2, 3, 6):
            powers[i] = frob
    g2 = monic_gcd(f, subtract(powers[2], x))
    g3 = monic_gcd(f, subtract(powers[3], x))
    # Rabin's criterion for n=6: X^(5^6) = X and no factors
    # of degrees dividing 6/2=3 or 6/3=2.
    require(powers[6] == x and g2 == [1] and g3 == [1],
            'Rabin irreducibility criterion failed')
    require(powers[2] == [0,1,0,0,3] and powers[3] == [0,0,1,0,0,1],
            'explicit residue control failed')
    require(f == [2,0,0,1,0,0,1], 'frozen mod-5 polynomial mismatch')
    return {'integer_Weil_coeffs_ascending': integer_coeffs,
            'reduction_prime': P, 'mod5_coeffs_ascending': f,
            'x_to_5pow2_remainder': powers[2],
            'x_to_5pow3_remainder': powers[3],
            'x_to_5pow6_remainder': powers[6],
            'gcd_f_with_x_to_5pow2_minus_x': g2,
            'gcd_f_with_x_to_5pow3_minus_x': g3,
            'irreducible_over_Q': True}


def self_test(fixture):
    check_census(fixture)
    cert = certificate()
    rejects = 0
    for mutation in (
        lambda d: d['actual_fixed_nu12_source'].update(order=ORDER+1),
        lambda d: d.update(field_cardinality=Q**3+1),
        lambda d: d['actual_fixed_nu12_target'].update(order=True),
        lambda d: d.update(mutant=True),
    ):
        candidate = json.loads(json.dumps(fixture))
        mutation(candidate)
        try:
            check_census(candidate)
        except ValueError:
            rejects += 1
    # Reducible: X^6+1 over F5 has factor X^2+1.
    try:
        certificate(trace=0, field=1)
    except ValueError:
        rejects += 1
    require(rejects == 5, 'mutation control escaped')
    return cert, rejects


def main():
    path = Path(__file__).with_name(CENSUS)
    fixture, source_sha256 = strict_json(path)
    cert, mutants = self_test(fixture)
    result = {'schema': 'ct161-weil-simple-obstruction/v1',
              'ct160_census_sha256': source_sha256,
              'ct160_source_target_orders': [ORDER, ORDER],
              'source_target_trace': T,
              'field': 'F_223',
              'finite_certificate': cert,
              'mutations_rejected': mutants,
              'consequence': 'Res_(F223^3/F223)(E_fixed) is F223-simple, dimension 3; no F223 homs in either direction to abelian varieties of dimension 1 or 2',
              'scope': 'specific fixed CT160 source and target; not geometrically simple; no arbitrary prime-field ECDLP result',
              'standing': '[pcc:unverified]'}
    print(json.dumps(result, sort_keys=True, separators=(',', ':')))


if __name__ == '__main__':
    main()
