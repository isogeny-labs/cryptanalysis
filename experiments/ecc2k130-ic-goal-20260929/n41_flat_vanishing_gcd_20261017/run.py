#!/usr/bin/env sage -python
"""Matched target-conditioned N41 direct and all-valid-flat GCD scans."""
from itertools import combinations
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
FLATS = ROOT / 'n41_valid_affine_flat_target_20261017/result.json'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def horner(coefficients, value, zero):
    out = zero
    for coefficient in reversed(coefficients):
        out = out * value + coefficient
    return out


def main():
    signal.alarm(300)
    protocol_path = HERE / 'protocol.json'
    protocol = json.loads(protocol_path.read_text())
    assert protocol['panels'] == ['witness', 'negative']
    files = {'run.py': Path(__file__), 'protocol.json': protocol_path,
             'geometry.json': GEOMETRY, 'flat_result.json': FLATS,
             'witness_result_v2.json': SOURCE / 'witness_result_v2.json',
             'negative_result_v2.json': SOURCE / 'negative_result_v2.json',
             'sweep_result.json': SOURCE / 'sweep_result.json',
             'sage_runtime_info.json': HERE / 'sage_runtime_info.json'}
    source_sha256 = {name: sha(path) for name, path in files.items()}
    geo = json.loads(GEOMETRY.read_text())
    flat_result = json.loads(FLATS.read_text())
    legal = sorted(geo['permitted_canonical_a'])
    flats = [tuple(row) for row in flat_result['flats']]
    union = set().union(*(set(flat) for flat in flats))
    covers = [indices for indices in combinations(range(8), 6)
              if set().union(*(set(flats[i]) for i in indices)) == union]
    assert covers
    cover = covers[0]
    leftover = sorted(set(legal)-union)
    assert len(leftover) == 13
    F2 = PolynomialRing(GF(2), 't')
    t = F2.gen()
    field = GF(2**41, name='t', modulus=t**41 + t**3 + 1)
    zero = field.zero()
    one = field.one()
    poly = PolynomialRing(field, 'R')
    R = poly.gen()
    def dec(value):
        return field(F2([(int(value) >> i) & 1 for i in range(41)]))
    def product(slot, mask):
        value = 0
        for i, basis in enumerate(geo['blocks'][slot]['product_basis']):
            if mask >> i & 1:
                value ^= basis
        return dec(value)
    products = [[product(slot, mask) for mask in legal] for slot in range(3)]
    by_mask = {mask: products[2][i] for i, mask in enumerate(legal)}
    setup_start = time.perf_counter_ns()
    vanish = {}
    for index in cover:
        v = poly(one)
        for mask in flats[index]:
            v *= (R - by_mask[mask])
        assert v.degree() == 8
        assert all(v(by_mask[mask]) == 0 for mask in flats[index])
        vanish[index] = v
    setup_ns = time.perf_counter_ns() - setup_start
    sweep = json.loads((SOURCE / 'sweep_result.json').read_text())
    panels = []
    for label in protocol['panels']:
        tensor = json.loads((SOURCE / (label + '_result_v2.json')).read_text())
        terms = [(qi, ri, [(pi, dec(c)) for pi, c in coeff])
                 for qi, ri, coeff in tensor['coefficient_terms']]
        phase_ns = {'coefficient': 0, 'direct': 0, 'gcd_route': 0}
        direct_zeros = set()
        gcd_zeros = set()
        nonconstant_gcds = gcds = leftovers = root_checks = 0
        for ip, pvalue in enumerate(products[0]):
            pp = [pvalue**i for i in range(17)]
            start = time.perf_counter_ns()
            specialized = [(qi, ri, sum((c*pp[pi] for pi, c in coeff), zero))
                           for qi, ri, coeff in terms]
            phase_ns['coefficient'] += time.perf_counter_ns() - start
            for iq, qvalue in enumerate(products[1]):
                start = time.perf_counter_ns()
                qp = [qvalue**i for i in range(17)]
                cp = [zero] * 25
                for qi, ri, c in specialized:
                    cp[ri] += c*qp[qi]
                phase_ns['coefficient'] += time.perf_counter_ns() - start
                masks = (legal[ip], legal[iq])
                def direct():
                    for ir, rvalue in enumerate(products[2]):
                        if horner(cp, rvalue, zero) == 0:
                            direct_zeros.add(masks + (legal[ir],))
                def grouped():
                    nonlocal nonconstant_gcds, gcds, leftovers, root_checks
                    polynomial = poly(cp)
                    for index in cover:
                        gcd = polynomial.gcd(vanish[index])
                        gcds += 1
                        if gcd.degree() > 0:
                            nonconstant_gcds += 1
                            for mask in flats[index]:
                                root_checks += 1
                                if horner(cp, by_mask[mask], zero) == 0:
                                    gcd_zeros.add(masks + (mask,))
                    for mask in leftover:
                        leftovers += 1
                        if horner(cp, by_mask[mask], zero) == 0:
                            gcd_zeros.add(masks + (mask,))
                if (ip+iq) & 1:
                    start = time.perf_counter_ns(); grouped(); phase_ns['gcd_route'] += time.perf_counter_ns()-start
                    start = time.perf_counter_ns(); direct(); phase_ns['direct'] += time.perf_counter_ns()-start
                else:
                    start = time.perf_counter_ns(); direct(); phase_ns['direct'] += time.perf_counter_ns()-start
                    start = time.perf_counter_ns(); grouped(); phase_ns['gcd_route'] += time.perf_counter_ns()-start
        expected = {tuple(row['masks']) for row in next(x for x in sweep['panels'] if x['name']==label)['zero_triples']}
        assert direct_zeros == gcd_zeros == expected
        panels.append({'label': label, 'phase_ns': phase_ns, 'specialized_pair_count': 1600,
                       'direct_horner_evaluations': 64000, 'gcd_count': gcds,
                       'nonconstant_gcds': nonconstant_gcds,
                       'post_gcd_root_checks': root_checks,
                       'leftover_horner_evaluations': leftovers,
                       'zero_masks': [list(row) for row in sorted(gcd_zeros)]})
        print(label, panels[-1], flush=True)
    result = {'status': 'PASS_N41_FLAT_VANISHING_GCD_MATCHED_SCAN',
              'candidate_id': None, 'source_sha256': source_sha256,
              'cover_indices': list(cover), 'cover_mask_count': len(union),
              'leftover_masks': leftover, 'vanishing_setup_ns': setup_ns,
              'panels': panels, 'peak_self_rss_raw': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    (HERE / 'result.json').write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
    print(result['status'], flush=True)


if __name__ == '__main__':
    main()
