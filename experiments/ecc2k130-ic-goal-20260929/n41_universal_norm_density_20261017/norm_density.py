#!/usr/bin/env sage -python
"""Frozen q-family norm of the N41 target-conditioned eliminant."""
import hashlib
import json
import resource
import signal
import time
from pathlib import Path

from sage.all import GF, PolynomialRing

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SOURCE = ROOT / 'n41_first_product_interpolated_eliminant_20261017'
GEOMETRY = ROOT / 'n41_w8_fixed_sum_table_20261009/geometry.json'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def independent_basis(values):
    pivots = {}
    result = []
    for original in values:
        value = original
        while value:
            pivot = value.bit_length() - 1
            if pivot in pivots:
                value ^= pivots[pivot]
            else:
                pivots[pivot] = value
                result.append(original)
                break
    return result


def span_annihilator(field, basis):
    coefficients = [field.one()]
    for v in basis:
        value = sum((c * v ** (1 << i) for i, c in enumerate(coefficients)), field.zero())
        assert value
        new = [field.zero()] * (len(coefficients) + 1)
        for i, c in enumerate(coefficients):
            new[i] += value * c
            new[i + 1] += c ** 2
        coefficients = new
    return coefficients


def main():
    signal.alarm(180)
    protocol = json.loads((HERE / 'protocol.json').read_text())
    paths = {'norm_density.py': Path(__file__), 'geometry.json': GEOMETRY,
             'witness_result_v2.json': SOURCE / 'witness_result_v2.json',
             'negative_result_v2.json': SOURCE / 'negative_result_v2.json',
             'sage_runtime_info.json': HERE / 'sage_runtime_info.json'}
    assert protocol['source_sha256'] == {name: digest(path) for name, path in paths.items()}
    geometry = json.loads(GEOMETRY.read_text())
    F2 = PolynomialRing(GF(2), 't')
    t = F2.gen()
    field = GF(2**41, name='t', modulus=t**41 + t**3 + 1)
    def dec(v):
        return field(F2([(int(v) >> i) & 1 for i in range(41)]))
    def enc(v):
        return sum(int(bit) << i for i, bit in enumerate(v.polynomial().list()))
    S = PolynomialRing(field, 'p')
    p = S.gen()
    T = PolynomialRing(S, 'r')
    r = T.gen()
    rb = independent_basis(geometry['blocks'][2]['product_basis'])
    assert len(rb) == 7
    linear = span_annihilator(field, [dec(v) for v in rb])
    annihilator = sum((T(c) * r ** (1 << i) for i, c in enumerate(linear)), T.zero())
    assert annihilator.degree() == 128 and annihilator.is_monic()
    q_order = protocol['q_order']
    assert len(q_order) == 8 and len(set(q_order)) == 8
    panels = []
    for label in ('witness', 'negative'):
        source = json.loads((SOURCE / (label + '_result_v2.json')).read_text())
        assert source['status'] == 'PASS_ISOLATED_FIRST_PRODUCT_INTERPOLATION'
        grouped = {}
        for qi, ri, pc in source['coefficient_terms']:
            grouped.setdefault(qi, {})[ri] = S({int(pi): dec(c) for pi, c in pc})
        q_degrees = sorted(grouped)
        accumulator = T.one()
        checkpoints = []
        for count, qvalue in enumerate(q_order, 1):
            q = dec(qvalue)
            qpower = {i: q**i for i in q_degrees}
            specialized = T({ri: sum((qpower[qi]*poly for qi, rows in grouped.items()
                                       if (poly := rows.get(ri)) is not None), S.zero())
                             for ri in range(25)})
            start = time.monotonic_ns()
            accumulator = (accumulator * specialized) % annihilator
            interval = time.monotonic_ns() - start
            if count in protocol['checkpoints']:
                degree = max((int(c.degree()) for c in accumulator if c), default=-1)
                occupied = sum(len(c.dict()) for c in accumulator)
                capacity = (degree + 1) * 128
                witness_p = dec(protocol['witness_first_product'])
                witness_r = dec(protocol['witness_third_product'])
                evaluated = accumulator(witness_r)(witness_p)
                direct = field.one()
                for qv in q_order[:count]:
                    qq = dec(qv)
                    f = field.zero()
                    for qi, rows in grouped.items():
                        for ri, poly in rows.items():
                            f += qq**qi * witness_r**ri * poly(witness_p)
                    direct *= f
                assert evaluated == direct
                if label == 'witness':
                    assert evaluated == 0
                else:
                    assert evaluated != 0
                row = {'q_count': count, 'p_degree': degree,
                       'r_degree': int(accumulator.degree()),
                       'nonzero_coefficients': occupied,
                       'rectangular_capacity': capacity,
                       'density': occupied / capacity,
                       'multiply_reduce_ns': interval,
                       'witness_evaluation': enc(evaluated),
                       'direct_evaluation_matches': True,
                       'peak_self_rss_raw': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
                checkpoints.append(row)
                print(label, row, flush=True)
        panels.append({'label': label, 'checkpoints': checkpoints})
    result = {'status': 'PASS_N41_UNIVERSAL_NORM_DENSITY',
              'candidate_id': None, 'source_sha256': protocol['source_sha256'],
              'protocol_sha256': digest(HERE / 'protocol.json'),
              'panels': panels,
              'peak_self_rss_raw': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    (HERE / 'result.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')


if __name__ == '__main__':
    main()
