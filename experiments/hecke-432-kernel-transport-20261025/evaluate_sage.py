"""Evaluate X0(432) chain pairs using kernel polynomials, without a 432-generator."""
import argparse
import json
import sys
from pathlib import Path

import sage.misc.lazy_import_cache as lazy_cache
lazy_cache.DOT_SAGE = '/Volumes/SSD990/llm/tmp/hecke432sage'

from sage.all import EllipticCurve, GF, PolynomialRing
from sage.schemes.elliptic_curves.hom_composite import EllipticCurveHom_composite

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / 'hecke-27-coordinate-bridge-20261025'))
from evaluate_sage import roots_for_pair, dual_image, dual_preimages  # noqa: E402


def chain(curve, edges):
    x = PolynomialRing(curve.base_field(), 'x').gen()
    maps = []
    current = curve
    for edge in edges:
        phi = current.isogeny(x - curve.base_field()(edge['kernel_x']))
        assert [int(a) for a in phi.codomain().a_invariants()] == edge['target_ainvs']
        maps.append(phi)
        current = phi.codomain()
    return EllipticCurveHom_composite.from_factors(maps), maps


def order_four_kernel_generator(phi):
    E = phi.domain()
    for xx, _ in phi.kernel_polynomial().roots():
        for P in E.lift_x(xx, all=True):
            if P.order() == 4 and phi(P).is_zero():
                return P
    raise AssertionError('degree-four kernel has no generator over input field')


def evaluate(model, edges2, edges3, coordinate_map):
    p = 883
    K = GF(p**2, 'u')
    E = EllipticCurve(K, model)
    two, two_maps = chain(E, edges2)
    three, _ = chain(E, edges3)
    q = EllipticCurveHom_composite.from_factors(two_maps[:2])
    psi = EllipticCurveHom_composite.from_factors(two_maps[2:])
    qdual = EllipticCurveHom_composite.from_factors([two_maps[1].dual(), two_maps[0].dual()])
    assert qdual.domain() == q.codomain() and qdual.codomain() == E
    middle = q.codomain()
    R = order_four_kernel_generator(psi)
    T0 = order_four_kernel_generator(qdual)
    i = K(-1).sqrt()
    T = T0 if R.weil_pairing(T0, 4) == i else -T0
    assert R.weil_pairing(T, 4) == i
    # A full odd-order kernel polynomial is a squarefree divisor polynomial.
    # push_subgroup preserves its 13 x-coordinates because q has coprime degree.
    C27_poly = q.push_subgroup(three.kernel_polynomial())
    assert C27_poly.degree() == 13 and C27_poly.is_squarefree()
    C27 = middle.isogeny(C27_poly)
    assert C27.degree() == 27
    C = EllipticCurve(K, coordinate_map['curve_ainvs'])
    coordinate_options = []
    j_pairs = []
    for kernel in (T + R, T - R):
        phi = middle.isogeny(kernel)
        pushed = phi.push_subgroup(C27_poly)
        assert pushed.degree() == 13 and pushed.is_squarefree()
        quotient = phi.codomain().isogeny(pushed)
        assert quotient.degree() == 27
        js, jt = phi.codomain().j_invariant(), quotient.codomain().j_invariant()
        _, points = roots_for_pair(C, coordinate_map, js, jt)
        coordinate_options.append(points); j_pairs.append([str(js), str(jt)])
    assert j_pairs[0] and j_pairs[1]
    F = GF(p)
    Ecurve = EllipticCurve(F, [0,0,0,0,432])
    B = EllipticCurve(F, [0,0,0,0,-16])
    B_points = set()
    frobenius_pairs = 0
    for Pplus in coordinate_options[0]:
        for Pminus in coordinate_options[1]:
            if Pplus[0]**p != Pminus[0] or Pplus[1]**p != Pminus[1]:
                continue
            frobenius_pairs += 1
            D = Pplus - Pminus
            if D.is_zero():
                continue
            xe, ye = -4*D[0], -8*i*(D[1]+K(1)/2)
            if xe**p != xe or ye**p != ye:
                continue
            H = Ecurve(F(xe), F(ye))
            preimages = dual_preimages(H, B, Ecurve)
            for Q in preimages:
                assert dual_image(Q, Ecurve) == H
                B_points.add((int(Q[0]),int(Q[1])))
    return {'source_j': int(E.j_invariant()), 'source_ainvs': model,
            'two_edge_roots': [e['kernel_x'] for e in edges2],
            'three_edge_roots': [e['kernel_x'] for e in edges3],
            'middle_j': int(middle.j_invariant()), 'C27_poly_degree': int(C27_poly.degree()),
            'j_pairs': j_pairs, 'coordinate_counts': [len(v) for v in coordinate_options],
            'frobenius_pair_count': frobenius_pairs,
            'B_points': [list(P) for P in sorted(B_points)]}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--all', action='store_true')
    parser.add_argument('--limit', type=int)
    args = parser.parse_args()
    paths = json.loads((ROOT/'hecke-432-stable-kernel-chains-20261025'/'chain_probe.json').read_text())['chains']
    maps = json.loads((ROOT/'hecke-27-coordinate-bridge-20261025'/'coordinate_map.json').read_text())
    rows = []
    if args.all:
        census = json.loads((ROOT/'hecke-432-stable-kernel-chains-20261025'/'full_chain_census.json').read_text())
        cases = ((r['curve_ainvs'], i, j, e2, e3)
                 for r in census['rows'] for i,e2 in enumerate(r['two_paths'])
                 for j,e3 in enumerate(r['three_paths']))
    else:
        cases = (([0,0,0,526,109], i, j, paths['2']['paths'][i], paths['3']['paths'][j])
                 for i,j in ((1,1),(1,0)))
    for model, i, j, e2, e3 in cases:
        if args.limit is not None and len(rows) >= args.limit:
            break
        row = evaluate(model, e2, e3, maps)
        row['pair'] = [i,j]
        rows.append(row)
        if len(rows) <= 2 or len(rows) % 12 == 0:
            print(json.dumps({'completed': len(rows), 'source_j': row['source_j'],
                              'pair': [i,j], 'B_points': row['B_points']},sort_keys=True),flush=True)
    output = 'full_result.json' if args.all else 'result.json'
    (HERE/output).write_text(json.dumps({'status':'PASS_KERNEL_TRANSPORT_CENSUS' if args.all else 'PASS_KERNEL_TRANSPORT_TWO_REPLAYS',
                                         'prime':883,'row_count':len(rows),'rows':rows},sort_keys=True,indent=2)+'\n')


if __name__ == '__main__':
    main()
