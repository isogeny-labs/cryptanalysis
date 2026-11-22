"""Exact implicit second-pair membership via the source-product inverse."""
import hashlib
import json
import resource
import signal
import time
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
protocol = json.loads((HERE / 'inverse_protocol.json').read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


for path, expected in protocol['sources'].items():
    assert sha(path) == expected, path
out = HERE / 'inverse_result.json'
assert not out.exists()
signal.signal(signal.SIGALRM, lambda _s, _f: (_ for _ in ()).throw(TimeoutError('implicit pair oracle cap')))
signal.alarm(protocol['wall_cap_seconds'])
started = time.monotonic()
P = PolynomialRing(GF(2), 'u')
u = P.gen()
K = GF(2**41, name='u', modulus=u**41+u**3+1)
E = EllipticCurve(K, [1, 0, 0, 0, 1])
fixture = json.loads((HERE / 'fixture.json').read_text())
count = json.loads((ROOT / 'n41_w11_n131_w33_density_20261018' /
                    'n41_count_result.json').read_text())
audit = json.loads((ROOT / 'n41_w11_fivepair_native_join_20261018' /
                    'audit_result.json').read_text())
valid = set(count['valid_codes'])
assert len(valid) == 281
BITS = [0, 1, 2, 3, 4, 6, 7, 8, 9, 10]
seed = K(P([(112 >> i) & 1 for i in range(41)]))


def dec(number):
    return K(P([(number >> i) & 1 for i in range(41)]))


def enc(value):
    return sum(int(coefficient) << i
               for i, coefficient in enumerate(value.polynomial().list()))


def halftrace(value):
    out, power = K.zero(), value
    for _ in range(21):
        out += power
        power = power**4
    assert out*out + out == value
    return out


def parameter(code):
    return sum((dec(1 << (bit+1)) for index, bit in enumerate(BITS)
                if code >> index & 1), K.zero())


def source_points(a):
    h = halftrace(a)
    assert h
    return E.lift_x(K.one() + ~h, all=True)


H = halftrace(seed)**2
C = K.one() + H
assert H and C
products = {}
for code in range(1024):
    a = parameter(code)
    product = a*(a+seed)
    products[enc(product**(1 << 24))] = code
assert len(products) == 1024
first_states = []
second_by_code = {}
pair_law_checks = 0
for code in sorted(valid):
    a = parameter(code)
    b = a+seed
    assert a and b and not a.trace() and not (~a).trace() and not (~b).trace()
    options = [p+q for p in source_points(a) for q in source_points(b)]
    assert len(options) == 4 and all(point != E(0) and point[0] for point in options)
    product = a*b
    for point in options:
        u0 = ~point[0]
        assert C*u0 + H*point[0] == product
        pair_law_checks += 1
    first_states.extend((code, branch,
                         E(point[0]**(1 << 12), point[1]**(1 << 12)))
                        for branch, point in enumerate(options))
    second_by_code[code] = [E(point[0]**(1 << 24), point[1]**(1 << 24))
                            for point in options]
assert len(first_states) == 1124 and pair_law_checks == 1124
collisions = {tuple(pair) for pair in
              fixture['distinct_code_folded_column_collision_pairs']}
C_rot = C**(1 << 24)
H_rot = H**(1 << 24)
setup_seconds = time.monotonic()-started


def query(name, target):
    query_start = time.monotonic()
    source_span_hits = 0
    valid_code_hits = 0
    candidates = 0
    for state_id, (first_code, first_branch, first) in enumerate(first_states):
        second = target - first
        candidates += 1
        if second == E(0) or not second[0]:
            continue
        x = second[0]
        p_rot = C_rot * ~x + H_rot * x
        second_code = products.get(enc(p_rot))
        if second_code is None:
            continue
        source_span_hits += 1
        if second_code not in valid or second_code == first_code or \
           tuple(sorted((first_code, second_code))) in collisions:
            continue
        valid_code_hits += 1
        for second_branch, expected in enumerate(second_by_code[second_code]):
            if expected == second:
                assert first + expected == target
                return {'name': name, 'status': 'EXACT_TWO_PAIR_HIT',
                        'states_examined': candidates,
                        'source_span_hits': source_span_hits,
                        'valid_code_hits': valid_code_hits,
                        'source_codes': [first_code, second_code],
                        'branch_indices': [first_branch, second_branch],
                        'first_state_id': state_id,
                        'target_point': [enc(target[0]), enc(target[1])],
                        'query_seconds': time.monotonic()-query_start}
    return {'name': name, 'status': 'EXACT_TWO_PAIR_MISS',
            'states_examined': candidates,
            'source_span_hits': source_span_hits,
            'valid_code_hits': valid_code_hits,
            'target_point': [enc(target[0]), enc(target[1])],
            'query_seconds': time.monotonic()-query_start}


positive = E(*map(dec, fixture['target_residual_point']))
public = E(*map(dec, audit['target_point']))
rows = [query('verified_relation_residual', positive),
        query('frozen_public_raw_point', public)]
assert rows[0]['status'] == 'EXACT_TWO_PAIR_HIT'
signal.alarm(0)
result = {'status': 'COMPLETE_N41_W11_IMPLICIT_TWO_PAIR_ORACLE',
          'candidate_id': None, 'curve_id': protocol['curve_id'],
          'source_codes': len(valid), 'first_pair_states': len(first_states),
          'product_code_map_entries': len(products),
          'pair_law_checks': pair_law_checks,
          'setup_seconds': setup_seconds,
          'query_rows': rows,
          'total_wall_seconds': time.monotonic()-started,
          'self_maxrss_raw': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
          'protocol_sha256': sha(HERE / 'inverse_protocol.json')}
out.write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
print(json.dumps({k: result[k] for k in
                  ('status', 'setup_seconds', 'query_rows', 'total_wall_seconds')},
                 sort_keys=True))
