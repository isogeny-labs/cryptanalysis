#!/usr/bin/env sage -python
"""Identify the actual N131 Frobenius eigenvalue on the frozen subgroup."""
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
TARGET = ROOT / 'n131_fixed_seed_eight_pair_circuit_20261010/target_preimages.json'
COEFFICIENTS = HERE / 'link_coefficients.json'
RUNTIME = HERE / 'sage_runtime_info.json'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def paths():
    return {'script': Path(__file__), 'target': TARGET,
            'coefficients': COEFFICIENTS, 'runtime': RUNTIME}


def save(name, value):
    with (HERE / name).open('x') as file:
        json.dump(value, file, sort_keys=True, indent=2)
        file.write('\n')


def freeze():
    save('lambda_sage_protocol.json', {'status': 'FROZEN_ACTUAL_FROBENIUS_EIGENVALUE_AUDIT',
         'source_sha256': {name: sha(path) for name, path in paths().items()}})


def run():
    from sage.all import EllipticCurve, GF, PolynomialRing
    protocol = json.loads((HERE / 'lambda_sage_protocol.json').read_text())
    assert protocol['source_sha256'] == {name: sha(path) for name, path in paths().items()}
    target = json.loads(TARGET.read_text())
    coefficients = json.loads(COEFFICIENTS.read_text())
    assert coefficients['status'] == 'PASS_LINKED_PLUS_MINUS_NONZERO'
    ring = PolynomialRing(GF(2), 't')
    t = ring.gen()
    field = GF(2**131, name='t', modulus=t**131+t**13+t**2+t+1)
    curve = EllipticCurve(field, [1, 0, 0, 0, 1])
    def dec(value):
        return field(ring([(int(value) >> i) & 1 for i in range(131)]))
    Q = curve(*map(dec, target['public_target']))
    r = int(coefficients['subgroup_order'])
    assert Q != curve(0) and r*Q == curve(0)
    tau = curve(Q[0]**2, Q[1]**2)
    tau16 = curve(Q[0]**(1 << 16), Q[1]**(1 << 16))
    matches = []
    for row in coefficients['rows']:
        lam = int(row['lambda'])
        if lam*Q == tau:
            matches.append(lam)
            assert int(row['same_sign_coefficient'])*Q == Q + tau16
            assert int(row['opposite_sign_coefficient'])*Q == Q - tau16
            assert row['frobenius_131_identity']
    assert len(matches) == 1
    save('lambda_sage_result.json', {'status': 'PASS_ACTUAL_N131_FROBENIUS_EIGENVALUE',
         'lambda': str(matches[0]), 'source_sha256': protocol['source_sha256'],
         'protocol_sha256': sha(HERE / 'lambda_sage_protocol.json'),
         'same_and_opposite_sign_checked': True})
    print('PASS_ACTUAL_N131_FROBENIUS_EIGENVALUE')


if __name__ == '__main__':
    assert len(sys.argv) == 2 and sys.argv[1] in ('freeze', 'run')
    {'freeze': freeze, 'run': run}[sys.argv[1]]()
