"""Matched complete construction and chosen-base relation experiments.

No construction uses a discrete-log table or the planted secret. That secret
is retained by the driver only to audit labels and any resulting DLP witness.
All rejected inputs, common-field embeddings, and failed bases are included.
"""
from itertools import product
from pathlib import Path
import json
import random
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT/'extensions'))
sys.path.insert(0, str(ROOT/'joint'))
from flint import nmod_poly
from core import prime_order_curve, sqrt_mod
from known_labels import WindowSampler
from zero_pairs import zero_pairs
from norm_trace_lift import Extension, lift
from cubic_trace_lift import lift_parameters, CommonCubicField, field_point_sum
from progression_blocks import CountedCurve, product_tree
from trace_solver import trace_fibers, linear_solve
from orbit_projection import OrbitProjection


def polynomial_from_roots(roots, p):
    return product_tree([nmod_poly([-x, 1], p) for x in roots])[-1][0]


def construct(E, P, Q, r, B, seed, family, common_field=True):
    start = time.process_time(); C = CountedCurve(E)
    sampler = WindowSampler(C, P, Q, r)
    sampler_setup = sampler.cpu_s
    rng = random.Random(seed)
    field = None; field_setup = 0.0
    delta = next(d for d in range(2, E.p) if sqrt_mod(d, E.p) is None)
    if family == 'cubic' and common_field:
        field = CommonCubicField(E.p); field_setup = field.cpu_s
    K = Extension(E.p, delta)
    records = {}; attempts = rejections = repeats = identities = 0
    lifting_cpu = embedding_cpu = verification_cpu = 0.0
    while len(records) < B:
        if attempts > 100*r:
            raise RuntimeError('Construction cap exhausted; no success inferred')
        T, u, v = sampler.sample(rng); attempts += 1
        if T is None:
            identities += 1; continue
        sign = 1 if T <= E.neg(T) else -1
        if sign == -1:
            T = E.neg(T); u, v = -u % r, -v % r
        if T[0] in records:
            repeats += 1; continue
        tick = time.process_time()
        if family == 'quadratic':
            candidates = lift(E, T, 1, delta)
            lifting_cpu += time.process_time()-tick
            if not candidates:
                rejections += 1; continue
            R = candidates[0]; x, y = R; auxiliary = 2*x[0] % E.p
            tick = time.process_time()
            assert K.contains(E, R)
            assert K.mul(x, K.conjugate(x)) == (1, 0)
            assert K.point_add(E, R, (K.conjugate(x), K.conjugate(y))) == ((T[0], 0), (T[1], 0))
            verification_cpu += time.process_time()-tick
            record = {'T': T, 'u': u, 'v': v, 'parameter': auxiliary, 'R': R}
        else:
            result = lift_parameters(E, T, 1, 0)
            lifting_cpu += time.process_time()-tick
            if not result['candidates']:
                rejections += 1; continue
            candidate = min(result['candidates'], key=lambda q: q['h'])
            if field is not None:
                embedded = field.embed(E, T, candidate)
                embedding_cpu += embedded['cpu_s']
            else:
                rt = time.process_time(); z = nmod_poly([0, 1], E.p)
                cu, cw = candidate['u'], candidate['w']; X, Y = T
                cv = (cw*Y-X*X-cu*X) % E.p
                gpoly = z*z+cu*z+cv
                fpoly = z**3+E.a*z+E.b
                assert gpoly*gpoly-cw*cw*fpoly == (z-X)*nmod_poly(candidate['q'], E.p)
                verification_cpu += time.process_time()-rt
                embedded = {'point': None, 'coordinates': None}
            record = {'T': T, 'u': u, 'v': v, 'parameter': candidate['h'],
                      'R': embedded['point'], 'q': candidate['q'],
                      'interpolation': [candidate['u'], candidate['w']],
                      'coordinates': embedded['coordinates']}
        assert record['parameter'] not in [v['parameter'] for v in records.values()]
        records[T[0]] = record
    construction_cpu = time.process_time()-start
    tick = time.process_time()
    V = polynomial_from_roots([v['parameter'] for v in records.values()], E.p)
    L = polynomial_from_roots(records, E.p)
    encoding_cpu = time.process_time()-tick
    result = {'family': family, 'B': B, 'seed': seed, 'attempts': attempts,
              'rejected_lifts': rejections, 'repeated_trace_coordinates': repeats,
              'identity_opportunities': identities, 'construction_cpu_s': construction_cpu,
              'sampler_setup_cpu_s': sampler_setup, 'common_field_setup_cpu_s': field_setup,
              'lift_solve_cpu_s': lifting_cpu, 'embedding_and_trace_verify_cpu_s': embedding_cpu,
              'quadratic_verify_cpu_s': verification_cpu, 'construction_group_ops': C.ops,
              'chosen_base_encoding_cpu_s': encoding_cpu,
              'auxiliary_membership_degree': int(V.degree()),
              'auxiliary_nonzero_coefficients': sum(int(x) != 0 for x in V),
              'trace_membership_degree': int(L.degree()),
              'delta': delta if family == 'quadratic' else None,
              'common_field_coefficients': list(map(int, field.K.modulus())) if field else None,
              'common_field_modulus': str(field.K.modulus()) if field else None}
    return records, result, field


def unfiltered_control(E, P, Q, r, B, seed):
    tick = time.process_time(); C = CountedCurve(E)
    sampler = WindowSampler(C, P, Q, r); rng = random.Random(seed)
    xs = set(); attempts = 0
    while len(xs) < B:
        T, u, v = sampler.sample(rng); attempts += 1
        if T is not None:
            xs.add(T[0])
    return {'unfiltered_construction_cpu_s': time.process_time()-tick,
            'unfiltered_group_ops': C.ops, 'unfiltered_attempts': attempts}


def reciprocal_divisor(E, relation, records, delta):
    K = Extension(E.p, delta); p = E.p
    rows = []; rhs = []; Rs = []; ts = []
    for T in relation:
        record = records[T[0]]; x, y = record['R']
        if T != record['T']:
            y = K.neg(y)
        R = x, y; Rs.append(R); ts.append(record['parameter'])
        columns = [(1, 0), x, K.mul(x, x), y, K.mul(x, y)]
        target = K.neg(K.mul(K.mul(x, x), x))
        for component in range(2):
            rows.append([c[component] for c in columns]); rhs.append(target[component])
    coeff = linear_solve(rows, rhs, p)
    assert coeff is not None
    g = nmod_poly(coeff[:3]+[1], p); k = nmod_poly(coeff[3:], p)
    f = nmod_poly([E.b, E.a, 0, 1], p); H = g*g-k*k*f
    expected = nmod_poly([1], p)
    for t in ts:
        expected *= nmod_poly([1, -t, 1], p)
    assert H == expected
    assert int(H[0]) == 1 and int(H[1]) == int(H[5]) and int(H[2]) == int(H[4])
    compressed = polynomial_from_roots(ts, p)
    k0, k1, k2 = map(int, list(compressed)[:3])
    assert H == nmod_poly([1, k2, k1+3, k0+2*k2, k1+3, k2, 1], p)
    zero_sums = 0; nonzero_kernel_sums = 0
    for choices in product([0, 1], repeat=3):
        total = None
        for R, choice in zip(Rs, choices):
            chosen = tuple(K.conjugate(z) for z in R) if choice else R
            total = K.point_add(E, total, chosen)
        conjugate = None if total is None else tuple(K.conjugate(z) for z in total)
        assert K.point_add(E, total, conjugate) is None
        zero_sums += total is None; nonzero_kernel_sums += total is not None
    return {'divisor_coefficients': coeff, 'compressed_cubic': list(map(int, compressed)),
            'zero_extension_sums': zero_sums,
            'nonzero_trace_kernel_sums': nonzero_kernel_sums}


def cubic_divisor(E, relation, records, field):
    rows = []; rhs = []; Rs = []; hs = []
    for T in relation:
        record = records[T[0]]; x, y = record['R']
        if T != record['T']:
            y = -y
        Rs.append((x, y)); hs.append(record['parameter'])
        columns = [field.K(1), x, x*x, x**3, x**4, y, x*y, x*x*y]
        target = -x**3*y
        columns = [list(map(int, value.to_list())) for value in columns]
        target = list(map(int, target.to_list()))
        for component in range(3):
            rows.append([c[component] for c in columns]); rhs.append(target[component])
    coeff = linear_solve(rows, rhs, E.p)
    assert coeff is not None
    g = nmod_poly(coeff[:5], E.p); k = nmod_poly(coeff[5:]+[1], E.p)
    f = nmod_poly([E.b, E.a, 0, 1], E.p); H = k*k*f-g*g
    expected = nmod_poly([1], E.p)
    for h in hs:
        expected *= nmod_poly([-1, 0, h, 1], E.p)
    assert H == expected
    z = nmod_poly([0, 1], E.p); D = z**3-1
    s1 = sum(hs) % E.p; s2 = sum(hs[i]*hs[j] for i in range(3) for j in range(i+1, 3)) % E.p
    s3 = hs[0]*hs[1]*hs[2] % E.p
    assert H == D**3+s1*D*D*z*z+s2*D*z**4+s3*z**6
    total = field_point_sum(E, Rs)
    orbit = []
    if total is not None:
        orbit = [total, tuple(z.frobenius() for z in total)]
        orbit.append(tuple(z.frobenius() for z in orbit[-1]))
    assert field_point_sum(E, orbit) is None
    return {'divisor_coefficients': coeff, 'symmetric_h': [s1, s2, s3],
            'extension_sum_is_identity': total is None,
            'trace_of_extension_sum_is_identity': True}


def main():
    results = []; witnesses = []; successful = verified_divisors = 0
    for p, B in [(257, 8), (1153, 16), (12289, 32), (65537, 48)]:
        E, r, P = prime_order_curve(p)
        for trial in range(8):
            rng = random.Random(20261027+p+trial); secret = rng.randrange(1, r)
            Q = E.mul(secret, P)
            for family in ['quadratic', 'cubic']:
                records, result, field = construct(E, P, Q, r, B, 20270000+trial+p, family)
                result.update({'p': p, 'curve': [E.a, E.b], 'r': r, 'P': P, 'Q': Q,
                               'trial': trial})
                result.update(unfiltered_control(E, P, Q, r, B, 20270000+trial+p))
                if family == 'cubic':
                    formal_records, formal, _ = construct(E, P, Q, r, B, 20270000+trial+p,
                                                          family, common_field=False)
                    for x, record in records.items():
                        assert all(record[k] == formal_records[x][k]
                                   for k in ['T', 'u', 'v', 'q', 'parameter', 'interpolation'])
                    result['formal_construction_cpu_s'] = formal['construction_cpu_s']
                    result['formal_construction_group_ops'] = formal['construction_group_ops']
                # The driver checks labels with the secret after construction.
                for record in records.values():
                    assert E.mul((record['u']+record['v']*secret) % r, P) == record['T']
                tick = time.process_time(); pairs = zero_pairs(E, records)
                result['direct_pairs_cpu_s'] = time.process_time()-tick
                solved = trace_fibers(E, records)
                assert solved['relations'] == pairs
                result.update({k: v for k, v in solved.items() if k != 'relations'})
                result['trace_fibers_cpu_s'] = result.pop('cpu_s')
                projector = OrbitProjection(E, family, result['delta'])
                projected = projector.solve(records)
                assert projected['relations'] == pairs
                result.update({k: v for k, v in projected.items()
                               if k.startswith('orbit_projection') or k.startswith('projected_')
                               or k == 'projection_and_fibers_cpu_s'})
                result['relations'] = len(pairs); successful += bool(pairs)
                useful = 0; divisors = []
                for relation in sorted(pairs):
                    su = sv = 0
                    for T in relation:
                        record = records[T[0]]
                        sign = 1 if T == record['T'] else -1
                        su += sign*record['u']; sv += sign*record['v']
                    su %= r; sv %= r
                    if sv:
                        recovered = -su*pow(sv, -1, r) % r
                        assert E.mul(recovered, P) == Q; useful += 1
                    if family == 'quadratic':
                        divisor = reciprocal_divisor(E, relation, records, result['delta'])
                    else:
                        divisor = cubic_divisor(E, relation, records, field)
                    divisor.update({'trace_relation': relation, 'label_sum': [su, sv]})
                    divisors.append(divisor); verified_divisors += 1
                result['useful_labeled_relations'] = useful
                witnesses.append({'p': p, 'family': family, 'trial': trial,
                                  'records': [dict(v, R=v['R'] if family == 'quadratic' else None)
                                              for v in records.values()],
                                  'divisors': divisors})
                results.append(result)
                # Keep completed cases reviewable even if the host interrupts.
                Path(__file__).with_name('lift_benchmark.partial.json').write_text(
                    json.dumps(results, indent=2)+'\n')
                print({k: result[k] for k in ['p', 'family', 'trial', 'attempts',
                       'relations', 'construction_cpu_s', 'direct_pairs_cpu_s',
                       'trace_fibers_cpu_s']}, flush=True)
    output = {'records': results, 'bases': len(results), 'successful_bases': successful,
              'failed_bases': len(results)-successful, 'divisors_verified': verified_divisors,
              'all_relation_sets_match': True, 'errors': 0,
              'efficient_combined_attack_demonstrated': False}
    Path(__file__).with_name('lift_benchmark.json').write_text(json.dumps(output, indent=2)+'\n')
    Path(__file__).with_name('lift_witnesses.json').write_text(json.dumps(witnesses, indent=2)+'\n')
    print({k: v for k, v in output.items() if k != 'records'}, flush=True)


if __name__ == '__main__':
    main()
