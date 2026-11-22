"""Search three free aligned W9 pair slots via a two-product eliminant."""
import hashlib
import json
import resource
import time
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SOURCE = ROOT / 'n41_n131_w29_rotation_alignment_20261017/aligned_states.json'
PRIOR = ROOT / 'n41_w9_two_product_eliminant_20261017/result.json'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


protocol = json.loads((HERE / 'protocol.json').read_text())
for name, path in {
    'script': Path(__file__), 'runtime': HERE / 'sage_runtime_info.json',
    'states': SOURCE, 'prior': PRIOR,
}.items():
    assert sha(path) == protocol['source_sha256'][name], name
assert not (HERE / 'result.json').exists()
source = json.loads(SOURCE.read_text())
assert source['rotations'] == [0, 0, 12, 12, 24]

K = PolynomialRing(GF(2), 'u')
u = K.gen()
F = GF(2**41, name='u', modulus=u**41+u**3+1)
E = EllipticCurve(F, [1, 0, 0, 0, 1])
PQ = PolynomialRing(F, names=('p', 'q'))
p, q = PQ.gens()
AQ = PolynomialRing(PQ, 'a')
a = AQ.gen()
Q = PolynomialRing(F, 'q')
qone = Q.gen()


def dec(word):
    return F(K([(int(word) >> i) & 1 for i in range(41)]))


def enc(value):
    return sum(int(c) << i for i, c in enumerate(value.polynomial().list()))


def halftrace(x):
    original = x
    out = F.zero()
    for _ in range(21):
        out += x
        x = x**4
    assert out**2 + out == original
    return out


def product(mask, seed):
    x = dec(mask << 1)
    return (x*(x+seed))**(1 << 12)


def eval_linearized(coefficients, x):
    out = F.zero()
    for c in coefficients:
        out += c*x
        x *= x
    return out


def trace_roots(poly):
    poly = poly.monic()
    if poly.degree() == 0:
        return []
    if poly.degree() == 1:
        return [enc(poly[0]/poly[1])]
    for k in range(41):
        x = (F.gen()**k*qone) % poly
        tr = Q.zero()
        for _ in range(41):
            tr = (tr+x) % poly
            x = (x*x) % poly
        factor = poly.gcd(tr)
        if 0 < factor.degree() < poly.degree():
            return trace_roots(factor) + trace_roots(poly//factor)
    raise AssertionError('trace splitting failed')


def subspace_roots(poly, coefficients):
    x = qone % poly
    remainder = Q.zero()
    for c in coefficients:
        remainder = (remainder+c*x) % poly
        x = (x*x) % poly
    divisor = poly.gcd(remainder)
    return sorted(trace_roots(divisor)), int(divisor.degree())


states = [[E(dec(row['point'][0]), dec(row['point'][1])) for row in slot]
          for slot in source['states']]
raw = E(dec(source['target_raw_point'][0]),
        dec(source['target_raw_point'][1]))
public = E(raw[0]**(1 << 6), raw[1]**(1 << 6))
fixed0 = states[0][105]
fixed4 = states[4][111]
fixed_columns = set(source['states'][0][105]['columns'] +
                    source['states'][4][111]['columns'])
seed = dec(source['seed'] << 1)
h = halftrace(seed)
H = (h*h)**(1 << 12)
C = (1+h*h)**(1 << 12)
assert C and H

products = [product(source['states'][2][4*i]['masks'][0], seed)
            for i in range(71)]
assert len(set(products)) == 71
assert all(product(source['states'][3][4*i]['masks'][0], seed) == products[i]
           for i in range(71))
lookup = {enc(x): i for i, x in enumerate(products)}

basis = [product(1 << bit, seed) for bit in range(9) if bit != 5]
coefficients = [F.one()]
span = {F.zero()}
for v in basis:
    w = eval_linearized(coefficients, v)
    assert w
    new = [w*coefficients[0]]
    for i in range(1, len(coefficients)):
        new.append(coefficients[i-1]**2+w*coefficients[i])
    new.append(coefficients[-1]**2)
    coefficients = new
    span |= {x+v for x in tuple(span)}
assert len(span) == 256 and len(coefficients) == 9
assert all(eval_linearized(coefficients, x) == 0 for x in span)
assert all(x in span for x in products)

f1 = C*a*a+p*a+H
start = time.monotonic()
build_seconds = 0.0
root_seconds = 0.0
replay_seconds = 0.0
exceptional_outer_states = []
algebraic_code_hits = []
exact_witnesses = []
queries = 0
gcd_degree_total = 0
for outer_id, outer in enumerate(states[1]):
    target = public-fixed0-fixed4-outer
    if target == E(0) or target[0] == 0:
        exceptional_outer_states.append(outer_id)
        continue
    t = 1/target[0]
    build_start = time.monotonic()
    A = 1+(a*t)*(a*t)
    B = a*t
    D = a*a+t*t
    M = A*H+C*D
    L = A*q+C*B
    N = B*H+q*D
    remainder = (M*M+L*N) % f1
    assert remainder.degree() <= 1
    r0, r1 = remainder[0], remainder[1]
    eliminant = C*r0*r0+p*r0*r1+H*r1*r1
    assert eliminant and eliminant.degree(p) <= 4 and eliminant.degree(q) <= 4
    terms = [(i, j, c) for (i, j), c in eliminant.dict().items()]
    build_seconds += time.monotonic()-build_start

    for left_code, pp in enumerate(products):
        query_start = time.monotonic()
        poly = Q.zero()
        for i, j, c in terms:
            poly += c*(pp**i)*(qone**j)
        if not poly:
            # A zero specialization requires a complete right-code scan.
            roots = [enc(x) for x in products]
            gcd_degree = None
        else:
            roots, gcd_degree = subspace_roots(poly, coefficients)
        root_seconds += time.monotonic()-query_start
        queries += 1
        if gcd_degree is not None:
            gcd_degree_total += gcd_degree
        for word in roots:
            right_code = lookup.get(word)
            if right_code is None:
                continue
            algebraic_code_hits.append([outer_id, left_code, right_code])
            replay_start = time.monotonic()
            for left_id in range(4*left_code, 4*left_code+4):
                for right_id in range(4*right_code, 4*right_code+4):
                    cols = (fixed_columns |
                            set(source['states'][1][outer_id]['columns']) |
                            set(source['states'][2][left_id]['columns']) |
                            set(source['states'][3][right_id]['columns']))
                    if len(cols) != 10:
                        continue
                    if fixed0+outer+states[2][left_id]+states[3][right_id]+fixed4 == public:
                        exact_witnesses.append([105, outer_id, left_id, right_id, 111])
            replay_seconds += time.monotonic()-replay_start

elapsed = time.monotonic()-start
assert [105, 244, 66, 47, 111] in exact_witnesses
assert not exceptional_outer_states
result = {
    'status': 'PASS_N41_THREE_FREE_PAIR_QUARTIC_SEARCH',
    'candidate_id': None,
    'curve_id': 'EC1N41Ckb1h7d5e80d3c4d0',
    'fixed_slot_state_ids': {'0': 105, '4': 111},
    'free_slot_ids': [1, 2, 3],
    'outer_signed_states': len(states[1]),
    'specialized_quartic_queries': queries,
    'algebraic_code_hit_count': len(algebraic_code_hits),
    'algebraic_code_hits': algebraic_code_hits,
    'exact_witnesses': exact_witnesses,
    'exceptional_outer_states': exceptional_outer_states,
    'gcd_degree_total': gcd_degree_total,
    'linearized_coefficient_count': len(coefficients),
    'linearized_coefficients': [enc(c) for c in coefficients],
    'subspace_rank': len(basis),
    'subspace_size': len(span),
    'target_eliminant_build_seconds': build_seconds,
    'target_quartic_root_seconds': root_seconds,
    'target_exact_replay_seconds': replay_seconds,
    'target_total_seconds': elapsed,
    'self_maxrss_bytes': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    'protocol_sha256': sha(HERE / 'protocol.json'),
    'source_sha256': {'script': sha(Path(__file__)),
                      'runtime': sha(HERE / 'sage_runtime_info.json'),
                      'states': sha(SOURCE), 'prior': sha(PRIOR)},
}
(HERE / 'result.json').write_text(json.dumps(result, sort_keys=True, indent=2)+'\n')
print(json.dumps({'status': result['status'], 'queries': queries,
                  'hits': len(algebraic_code_hits),
                  'witnesses': exact_witnesses,
                  'seconds': elapsed}))
