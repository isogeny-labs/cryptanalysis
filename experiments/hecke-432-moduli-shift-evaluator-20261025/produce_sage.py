"""Evaluate quarter-shift modular points from a cyclic 432-subgroup."""
from hashlib import sha256
import json
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent


def torsion_four(curve):
    seen = set()
    out = []
    for x, multiplicity in curve.division_polynomial(4).roots():
        for point in curve.lift_x(x, all=True):
            if point.order() != 4:
                continue
            subgroup = frozenset(k*point for k in range(4))
            if subgroup not in seen:
                seen.add(subgroup)
                out.append(point)
    return out


def dual_kernel_generator(quotient, source, input_generator):
    middle = quotient.codomain()
    matches = []
    for candidate in torsion_four(middle):
        try:
            reverse = middle.isogeny(candidate, codomain=source)
        except ValueError:
            continue
        if reverse(quotient(input_generator)) in (4*input_generator, -4*input_generator):
            matches.append(candidate)
    assert len(matches) == 1, len(matches)
    return matches[0]


def subgroup_points(point, order):
    return frozenset(k*point for k in range(order))


def shifted_pair(middle, S, T):
    R = 27*S
    plus = middle.isogeny(T+R)
    minus = middle.isogeny(T-R)
    Cplus, Cminus = plus(4*S), minus(4*S)
    assert int(plus.degree()) == int(minus.degree()) == 4
    assert Cplus.order() == Cminus.order() == 27
    return (plus, Cplus), (minus, Cminus)


def same_moduli_point(left, right):
    left_map, left_C = left
    right_map, right_C = right
    L, R = left_map.codomain(), right_map.codomain()
    if L == R:
        return subgroup_points(left_C, 27) == subgroup_points(right_C, 27)
    if not L.is_isomorphic(R):
        return False
    return any(subgroup_points(iso(left_C), 27) == subgroup_points(right_C, 27)
               for iso in L.isomorphisms(R))


def point_text(point):
    return 'O' if point.is_zero() else f'({point[0]},{point[1]})'


def case(record, units):
    p, degree = record['prime'], record['field_degree']
    base_curve = EllipticCurve(GF(p), record['curve_ainvs'])
    assert base_curve.cardinality() == record['curve_order']
    field = GF(p**degree, 'u')
    curve = EllipticCurve(field, record['curve_ainvs'])
    P = curve(field(record['generator'][0]), field(record['generator'][1]))
    assert P.order() == 432
    q = curve.isogeny(108*P)
    assert int(q.degree()) == 4
    middle = q.codomain()
    S = q(P)
    R = 27*S
    assert S.order() == 108 and R.order() == 4
    T0 = dual_kernel_generator(q, curve, P)
    assert T0.order() == 4
    i = field(-1).sqrt()
    assert i**2 == -1
    T = T0 if R.weil_pairing(T0, 4) == i else -T0
    assert R.weil_pairing(T, 4) == i
    plus, minus = shifted_pair(middle, S, T)

    invariance = []
    for u in units:
        Pu = u*P
        assert Pu.order() == 432
        qu = curve.isogeny(108*Pu)
        assert qu.codomain() == middle and qu(P) == q(P)
        Su = qu(Pu)
        Ru = 27*Su
        Tu = T if Ru.weil_pairing(T, 4) == i else -T
        assert Ru.weil_pairing(Tu, 4) == i
        plus_u, minus_u = shifted_pair(middle, Su, Tu)
        assert same_moduli_point(plus_u, plus)
        assert same_moduli_point(minus_u, minus)
        invariance.append({'unit': u, 'plus_same': True, 'minus_same': True})

    plus_map, plus_C = plus
    minus_map, minus_C = minus
    frobenius_swap = None
    if degree == 2:
        assert i**p == -i
        assert T[0]**p == (-T)[0] and T[1]**p == (-T)[1]
        assert R[0]**p == R[0] and R[1]**p == R[1]
        assert subgroup_points((T+R), 4) != subgroup_points((T-R), 4)
        frobenius_swap = True
    else:
        assert i**p == i

    outputs = []
    quotient_js = []
    for label, phi, C27 in (('plus', plus_map, plus_C), ('minus', minus_map, minus_C)):
        target_quotient = phi.codomain().isogeny(C27)
        quotient_js.append(target_quotient.codomain().j_invariant())
        outputs.append({'shift': label, 'curve_ainvs': [str(c) for c in phi.codomain().ainvs()],
                        'curve_j': str(phi.codomain().j_invariant()),
                        'level27_quotient_j': str(target_quotient.codomain().j_invariant()),
                        'subgroup_generator': point_text(C27),
                        'subgroup_order': int(C27.order())})
    if degree == 2:
        assert plus_map.codomain().j_invariant()**p == minus_map.codomain().j_invariant()
        assert quotient_js[0]**p == quotient_js[1]
    return {'prime': p, 'field_degree': degree, 'input_curve_order': record['curve_order'],
            'input_generator': point_text(P), 'input_generator_order': int(P.order()),
            'middle_curve_ainvs': [str(c) for c in middle.ainvs()],
            'S_order': int(S.order()), 'R': point_text(R), 'T': point_text(T),
            'weil_pairing_R_T': str(R.weil_pairing(T,4)), 'chosen_i': str(i),
            'dual_kernel_candidates': 1, 'alternate_generator_checks': invariance,
            'frobenius_swaps_shift_kernels': frobenius_swap,
            'outputs': outputs}


def main():
    path = HERE/'protocol.json'
    protocol = json.loads(path.read_text())
    assert protocol['status'] == 'FROZEN_BEFORE_PERSISTED_MODULI_SHIFT_RUN_AFTER_EXPLORATORY_CURVE_SEARCH'
    assert (protocol['level'], protocol['target_level'], protocol['quarter_order']) == (432,27,4)
    cases = [case(r, protocol['alternate_generator_units']) for r in protocol['cases']]
    out = {'status': 'PASS_MODULI_QUARTER_SHIFT_EVALUATOR',
           'protocol_sha256': sha256(path.read_bytes()).hexdigest(),
           'cases': cases, 'X0_27_coordinate_evaluator': None,
           'candidate_id': None, 'timing_claim': None}
    (HERE/'result.json').write_text(json.dumps(out, sort_keys=True, indent=2)+'\n')
    print(json.dumps({'status': out['status'], 'primes': [r['prime'] for r in cases],
                      'alternate_generators_checked': sum(len(r['alternate_generator_checks']) for r in cases)},
                     sort_keys=True))


if __name__ == '__main__':
    main()
