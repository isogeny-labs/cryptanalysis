"""Exhaustive block oracles and an independent polynomial-resultant check."""
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from flint import nmod_poly
from core import prime_order_curve
from progression_blocks import (BinomialBlocks, SymmetricBlocks,
                                 SequentialBlocks, IntervalBSGS,
                                 binomial_quadratic_resultant, semaev_factor)


def main():
    tests = poles = hits = resultant_checks = identities = 0; records = []
    for p, b, g in [(17, 2, 2), (41, 2, 4), (97, 4, 4), (257, 4, 8)]:
        E, r, P = prime_order_curve(p)
        for B in [2, 4, 8]:
            if (p-1) % B:
                continue
            for alpha in [1, 2, 3]:
                c = pow(alpha, B, p)
                xs = [x for x in range(1, p) if pow(x, B, p) == c and E.lift(x)]
                chain = BinomialBlocks(E, P, r, b, g, B, alpha)
                products = SymmetricBlocks(E, P, r, b, g); products.prepare(xs)
                bsgs = IntervalBSGS(E, P, 2*b*g, len(xs)); bsgs.prepare(xs)
                scan = SequentialBlocks(E, P, 2*b*g)
                for T in [None]+list(E.points()):
                    expected = scan.solve(T, xs)
                    # Scalar-based independent oracle, including all exceptional j.
                    oracle = {}; oo = []
                    for j in range(2*b*g):
                        point = E.add(T, E.mul(j, P))
                        if point is None:
                            oo.append(j)
                        elif pow(point[0], B, p) == c:
                            oracle[j] = point
                    assert expected['hits'] == oracle and expected['identity_indices'] == oo
                    for solver in [chain, products, bsgs]:
                        actual = solver.solve(T, xs)
                        assert actual['hits'] == oracle, (p, B, alpha, T)
                        assert actual['identity_indices'] == oo, (p, B, alpha, T, solver)
                        if solver is chain:
                            poles += actual['poles_recovered']
                    tests += 1; hits += len(oracle); identities += len(oo)
                # Check the homogeneous chain against an ordinary resultant
                # after specializing V. This is independent of block geometry.
                z = nmod_poly([0, 1], p); L = z**B-c
                for U in [P[0], 0, 1]:
                    for V in range(p):
                        # Symmetry lets the same helper form S_3(V,U,z).
                        a = nmod_poly([(V*U-E.a)**2-4*E.b*(V+U),
                                       -2*((V+U)*(V*U+E.a)+2*E.b), (V-U)**2], p)
                        expected = int(L.resultant(a))
                        residue = binomial_quadratic_resultant(E, U, B, c,
                                                              nmod_poly([-V, 1], p))
                        # Ordinary Res(L,a) checks the homogeneous formula
                        # even at specializations where a2 vanishes.
                        assert int(residue[0]) == expected, (p, B, U, V)
                        resultant_checks += 1
                records.append({'p': p, 'r': r, 'B': B, 'alpha': alpha,
                                'M': 2*b*g, 'targets': r, 'usable_coordinates': len(xs)})
        print({'p': p, 'cumulative_blocks': tests, 'hits': hits}, flush=True)
    output = {'exhaustive_blocks': tests, 'hit_indices_verified': hits,
              'identity_indices_verified': identities, 'pole_cases_recovered': poles,
              'independent_resultants': resultant_checks, 'records': records,
              'errors': 0, 'all_four_solvers_match': True}
    Path(__file__).with_name('block_validation.json').write_text(json.dumps(output, indent=2)+'\n')
    print({k: v for k, v in output.items() if k != 'records'}, flush=True)


if __name__ == '__main__':
    main()
