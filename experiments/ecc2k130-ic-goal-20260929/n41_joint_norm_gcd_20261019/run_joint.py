"""Exact target-conditioned pair-family intersection by norm and polynomial GCD."""
import hashlib
import json
import resource
import signal
import time
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing, prod

HERE = Path(__file__).resolve().parent
protocol = json.loads((HERE / 'protocol.json').read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


for path, expected in protocol['sources'].items():
    assert sha(path) == expected, path
assert not (HERE / 'result.json').exists()
keys = json.loads(Path(protocol['keys']).read_text())
source = json.loads(Path(protocol['source_states']).read_text())
R2 = PolynomialRing(GF(2), 'u')
u = R2.gen()
F = GF(2**41, name='u', modulus=u**41 + u**3 + 1)
E = EllipticCurve(F, [1, 0, 0, 0, 1])
P = PolynomialRing(F, 'X')
X = P.gen()


def dec(word):
    return F(R2([(int(word) >> bit) & 1 for bit in range(41)]))


def enc(value):
    return sum(int(coefficient) << bit
               for bit, coefficient in enumerate(value.polynomial().list()))


def point(xy):
    return E(*map(dec, xy))


start_precompute = time.monotonic()
states = []
point_maps = []
x_lists = []
for slot in (0, 1):
    rows = source['states'][slot]
    state_points = [point(row['point']) for row in rows]
    point_map = {}
    x_map = {}
    for state_id, (row, group_point) in enumerate(zip(rows, state_points)):
        assert group_point != E(0)
        point_map.setdefault(tuple(row['point']), []).append(state_id)
        x_map.setdefault(group_point[0], set()).add(tuple(row['point']))
    assert len(rows) == 284 and len(x_map) == 142
    assert all(len(fiber) == 2 for fiber in x_map.values())
    states.append(state_points)
    point_maps.append(point_map)
    x_lists.append(sorted(x_map, key=enc))
fA = prod(X + x for x in x_lists[0])
fB = prod(X + x for x in x_lists[1])
assert fA.degree() == fB.degree() == 142
precompute_seconds = time.monotonic() - start_precompute


def pair_mul(left, right, modulus, delta):
    a, b = left
    c, d = right
    bd = (b * d) % modulus
    return ((a*c + bd*delta) % modulus,
            (a*d + b*c + bd*X) % modulus)


def query(key):
    K = point(key['point'])
    xK, yK = K[0], K[1]
    special_points = []
    modulus = fA
    if fA(xK) == 0:
        special_points = list(E.lift_x(xK, all=True))
        modulus = fA // (X + xK)
    assert modulus.degree() >= 1 and modulus(xK) != 0
    d = X + xK
    d_inv = d.inverse_mod(modulus)
    d_inv2 = (d_inv*d_inv) % modulus
    delta = X**3 + 1
    n0 = yK + X
    u_part = ((n0*n0 + delta)*d_inv2 + n0*d_inv + xK + X) % modulus
    v_part = (X*d_inv2 + d_inv) % modulus
    translated_x = (u_part, v_part)
    accum = (P.zero(), P.zero())
    for coefficient in reversed(fB.list()):
        a, b = pair_mul(accum, translated_x, modulus, delta)
        accum = ((a + coefficient) % modulus, b)
    a, b = accum
    norm = (a*a + a*b*X + b*b*delta) % modulus
    overlap = modulus.gcd(norm).monic()
    root_x = [root for root, multiplicity in overlap.roots()
              for _ in range(multiplicity)]
    assert len(root_x) == overlap.degree()
    candidates = special_points + [point for x in root_x
                                   for point in E.lift_x(x, all=True)]
    witnesses = []
    for A in candidates:
        if A == E(0):
            continue
        a_ids = point_maps[0].get((enc(A[0]), enc(A[1])), [])
        if not a_ids:
            continue
        B = K - A
        if B == E(0):
            continue
        b_ids = point_maps[1].get((enc(B[0]), enc(B[1])), [])
        for a_id in a_ids:
            for b_id in b_ids:
                ca = set(source['states'][0][a_id]['columns'])
                cb = set(source['states'][1][b_id]['columns'])
                if ca.isdisjoint(cb):
                    assert states[0][a_id] + states[1][b_id] == K
                    witnesses.append([a_id, b_id])
    return {'key_id': key['key_id'], 'exact_member': key['exact_member'],
            'oracle_member': bool(witnesses), 'witnesses': witnesses,
            'norm_gcd_degree': int(overlap.degree()),
            'special_first_x': len(special_points) // 2,
            'candidate_first_points': len(candidates),
            'first_state_group_subtractions': len(candidates)}


rows = []
for key in keys['keys']:
    started = time.monotonic()
    signal.signal(signal.SIGALRM,
                  lambda _signum, _frame: (_ for _ in ()).throw(TimeoutError()))
    signal.alarm(protocol['per_key_wall_cap_seconds'])
    try:
        result = query(key)
        result['status'] = 'PASS_EXACT_KEY_AGREEMENT'
        assert result['oracle_member'] == result['exact_member'], result
    except TimeoutError:
        result = {'key_id': key['key_id'], 'exact_member': key['exact_member'],
                  'status': 'BOUNDED_UNKNOWN', 'stop_reason': 'PER_KEY_WALL_CAP'}
    finally:
        signal.alarm(0)
    result['query_wall_seconds'] = time.monotonic() - started
    rows.append(result)
    print(json.dumps({key: result.get(key) for key in
                      ('key_id', 'status', 'norm_gcd_degree',
                       'query_wall_seconds')}, sort_keys=True), flush=True)
out = {'status': 'N41_JOINT_NORM_GCD_PANEL', 'candidate_id': None,
       'curve_id': protocol['curve_id'], 'precompute_wall_seconds': precompute_seconds,
       'first_x_count': len(x_lists[0]), 'second_x_count': len(x_lists[1]),
       'first_polynomial_sha256': hashlib.sha256(str(fA).encode()).hexdigest(),
       'second_polynomial_sha256': hashlib.sha256(str(fB).encode()).hexdigest(),
       'rows': rows, 'maxrss_raw': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
       'protocol_sha256': sha(HERE / 'protocol.json')}
(HERE / 'result.json').write_text(json.dumps(out, sort_keys=True, indent=2) + '\n')
