#!/usr/bin/env sage -python
"""Test all N41 p-r source cells with q implicit in a sparse annihilator."""
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


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def independent_basis(values):
    pivots, chosen = {}, []
    for original in values:
        value = original
        while value:
            pivot = value.bit_length() - 1
            if pivot in pivots:
                value ^= pivots[pivot]
            else:
                pivots[pivot] = value
                chosen.append(original)
                break
    return chosen


def annihilator(field, basis):
    coefficients = [field.one()]
    for value in basis:
        at_value = sum((c * value**(1 << i)
                        for i, c in enumerate(coefficients)), field.zero())
        assert at_value
        updated = [field.zero()] * (len(coefficients) + 1)
        for i, c in enumerate(coefficients):
            updated[i] += at_value * c
            updated[i + 1] += c**2
        coefficients = updated
    return coefficients


def main():
    signal.alarm(180)
    protocol_path = HERE / 'protocol_v2.json'
    protocol = json.loads(protocol_path.read_text())
    files = {'factored_gcd_v2.py': Path(__file__), 'geometry.json': GEOMETRY,
             'witness_result_v2.json': SOURCE / 'witness_result_v2.json',
             'negative_result_v2.json': SOURCE / 'negative_result_v2.json',
             'sweep_result.json': SOURCE / 'sweep_result.json',
             'sage_runtime_info.json': HERE / 'sage_runtime_info.json'}
    assert protocol['source_sha256'] == {name: sha(path) for name, path in files.items()}
    geo = json.loads(GEOMETRY.read_text())
    sweep = json.loads((SOURCE / 'sweep_result.json').read_text())
    F2 = PolynomialRing(GF(2), 't')
    t = F2.gen()
    field = GF(2**41, name='t', modulus=t**41+t**3+1)
    def dec(value):
        return field(F2([(int(value) >> i) & 1 for i in range(41)]))
    def enc(value):
        return sum(int(bit) << i for i, bit in enumerate(value.polynomial().list()))
    R = PolynomialRing(field, 'q')
    q = R.gen()
    def product(slot, mask):
        value = 0
        for i, basis in enumerate(geo['blocks'][slot]['product_basis']):
            if mask >> i & 1:
                value ^= basis
        return value
    valid = [sorted({product(slot, mask) for mask in geo['permitted_canonical_a']})
             for slot in range(3)]
    assert all(len(row) == 40 for row in valid)
    basis = independent_basis(geo['blocks'][1]['product_basis'])
    assert len(basis) == 7
    coeff = annihilator(field, [dec(value) for value in basis])
    L = sum((R(c)*q**(1 << i) for i, c in enumerate(coeff)), R.zero())
    assert L.degree() == 128 and L.is_monic()
    qspan = [0]
    for value in basis:
        qspan += [x ^ value for x in qspan]
    assert len(qspan) == 128 and all(L(dec(value)) == 0 for value in qspan)
    panels = []
    for label in protocol['panels']:
        tensor = json.loads((SOURCE / (label + '_result_v2.json')).read_text())
        terms = [(qi, ri, [(pi, dec(c)) for pi, c in pc])
                 for qi, ri, pc in tensor['coefficient_terms']]
        cells = 0
        gcd_positives = []
        usable = []
        phase = {'p_specialization_ns': 0, 'q_polynomial_ns': 0,
                 'modular_annihilator_ns': 0, 'small_gcd_ns': 0, 'root_check_ns': 0}
        start_query = time.monotonic_ns()
        for pvalue in valid[0]:
            start = time.monotonic_ns()
            pp = [dec(pvalue)**i for i in range(17)]
            specialized = [(qi, ri, sum((c*pp[pi] for pi, c in pc), field.zero()))
                           for qi, ri, pc in terms]
            phase['p_specialization_ns'] += time.monotonic_ns() - start
            for rvalue in valid[2]:
                start = time.monotonic_ns()
                rr = [dec(rvalue)**i for i in range(25)]
                coefficients = [field.zero()] * 17
                for qi, ri, c in specialized:
                    coefficients[qi] += c*rr[ri]
                f = R(coefficients)
                phase['q_polynomial_ns'] += time.monotonic_ns() - start
                start = time.monotonic_ns()
                if f:
                    xpower = q % f
                    remainder = R.zero()
                    for i, c in enumerate(coeff):
                        remainder += c*xpower
                        if i + 1 < len(coeff):
                            xpower = (xpower*xpower) % f
                    assert remainder == L % f if cells < 4 else True
                    phase['modular_annihilator_ns'] += time.monotonic_ns() - start
                    start = time.monotonic_ns()
                    g = f.gcd(remainder)
                else:
                    phase['modular_annihilator_ns'] += time.monotonic_ns() - start
                    start = time.monotonic_ns()
                    g = L
                phase['small_gcd_ns'] += time.monotonic_ns() - start
                cells += 1
                if g.degree() > 0:
                    start = time.monotonic_ns()
                    roots = sorted(enc(root) for root, multiplicity in g.roots()
                                   if multiplicity > 0)
                    assert len(roots) == int(g.degree())
                    assert all(f(dec(root)) == 0 and root in qspan for root in roots)
                    gcd_positives.append({'first_product': pvalue,
                                          'third_product': rvalue,
                                          'qspan_roots': roots})
                    usable.extend([pvalue, root, rvalue] for root in roots
                                  if root in valid[1])
                    phase['root_check_ns'] += time.monotonic_ns() - start
        query_ns = time.monotonic_ns() - start_query
        expected = sorted(tuple(row['products']) for row in next(
            panel for panel in sweep['panels'] if panel['name'] == label)['zero_triples'])
        assert sorted(tuple(row) for row in usable) == expected
        panel = {'label': label, 'p_r_cells': cells,
                 'qspan_size': len(qspan), 'valid_q_count': len(valid[1]),
                 'gcd_positive_cells': gcd_positives, 'usable_triples': usable,
                 'phase_ns': phase, 'query_ns': query_ns,
                 'peak_self_rss_raw': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
        panels.append(panel)
        print(label, cells, len(gcd_positives), len(usable), query_ns/1e9, flush=True)
    result = {'status': 'PASS_FACTORED_QSPAN_GCD_SOURCE_GRID', 'candidate_id': None,
              'curve_id': geo['curve_id'], 'protocol_sha256': sha(protocol_path),
              'source_sha256': protocol['source_sha256'], 'panels': panels,
              'peak_self_rss_raw': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    (HERE / 'result_v2.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')


if __name__ == '__main__':
    main()
