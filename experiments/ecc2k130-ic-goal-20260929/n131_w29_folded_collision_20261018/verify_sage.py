"""Independent Sage-field replay of all orbit ranks and valid collision pairs."""
import hashlib
import json
import signal
import time
from pathlib import Path

from sage.all import GF, PolynomialRing

HERE = Path(__file__).resolve().parent
protocol = json.loads((HERE / 'verify_protocol.json').read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


for path, digest in protocol['sources'].items():
    assert sha(path) == digest, path
assert not (HERE / 'verification_result.json').exists()
signal.signal(signal.SIGALRM, lambda _s, _f: (_ for _ in ()).throw(TimeoutError('independent replay wall cap')))
signal.alarm(protocol['wall_cap_seconds'])
started = time.monotonic()
audit = json.loads((HERE / 'audit_result.json').read_text())
filtered = json.loads((HERE / 'filter_result.json').read_text())
assert len(audit['cases']) == 524
P = PolynomialRing(GF(2), 'u')
u = P.gen()
K = GF(2**131, name='u', modulus=u**131 + u**13 + u**2 + u + 1)


def field(word):
    return K(P([(int(word) >> i) & 1 for i in range(131)]))


def packed(value):
    return sum(int(bit) << i for i, bit in enumerate(value.polynomial().list()))


def rank_basis(vectors):
    pivots = {}
    for value in vectors:
        word = packed(value)
        while word:
            pivot = word.bit_length() - 1
            if pivot not in pivots:
                pivots[pivot] = word
                break
            word ^= pivots[pivot]
    return pivots


def in_span(value, pivots):
    word = packed(value)
    while word:
        pivot = word.bit_length() - 1
        if pivot not in pivots:
            return False
        word ^= pivots[pivot]
    return True


base = [field(value) for value in audit['source_basis']]
seed = field(audit['seed'])
rotated = list(base)
rotated_seed = seed
for k in range(131):
    pivots = rank_basis(rotated + base)
    for e in (0, 1):
        for f in (0, 1):
            row = audit['cases'][4*k + 2*e + f]
            assert (row['frobenius_power'], row['source_endpoint_e'],
                    row['other_endpoint_f']) == (k, e, f)
            offset = (rotated_seed if e else K.zero()) + (seed if f else K.zero())
            assert row['rank'] == len(pivots)
            assert row['feasible'] == in_span(offset, pivots)
            if row['feasible']:
                columns = rotated + base
                code = row['solution_code']
                actual = K.zero()
                for i, value in enumerate(columns):
                    if code >> i & 1:
                        actual += value
                assert actual == offset
                for code in row['kernel_codes']:
                    actual = K.zero()
                    for i, value in enumerate(columns):
                        if code >> i & 1:
                            actual += value
                    assert actual == 0
    rotated = [value*value for value in rotated]
    rotated_seed *= rotated_seed

mask28 = (1 << 28) - 1
source_cache = {}


def source(code):
    if code not in source_cache:
        a = K.zero()
        for i, value in enumerate(base):
            if code >> i & 1:
                a += value
        b = a + seed
        valid = bool(a) and bool(b) and int(a.trace()) == 0
        if valid:
            valid = (int((a + ~a).trace()) == 0 and
                     int((b + ~b).trace()) == 0)
        source_cache[code] = (a, b, valid)
    return source_cache[code]


replayed = set()
occurrences = 0
for row in audit['cases']:
    if not row['has_nontrivial_pair'] or row['frobenius_power'] == 0:
        continue
    k, e, f = (row['frobenius_power'], row['source_endpoint_e'],
               row['other_endpoint_f'])
    for choice in range(1 << row['kernel_dimension']):
        code = row['solution_code']
        for i, basis in enumerate(row['kernel_codes']):
            if choice >> i & 1:
                code ^= basis
        ac, bc = code & mask28, code >> 28
        if not ac or not bc or ac == bc:
            continue
        aa, ab, av = source(ac)
        ba, bb, bv = source(bc)
        assert (aa if e == 0 else ab)**(1 << k) == (ba if f == 0 else bb)
        if av and bv:
            occurrences += 1
            replayed.add(tuple(sorted((ac, bc))))

listed = {tuple(row['codes']) for row in filtered['collision_pairs']}
assert replayed == listed
assert len(replayed) == filtered['distinct_valid_collision_pairs'] == 2093
assert occurrences == filtered['counts']['both_sources_valid_occurrences'] == 4186
finished = time.monotonic()
signal.alarm(0)
out = {
    'status': 'PASS_INDEPENDENT_SAGE_ORBIT_AND_CURVE_VALIDITY_REPLAY',
    'curve_id': protocol['curve_id'],
    'linear_cases_replayed': 524,
    'source_codes_tested': len(source_cache),
    'valid_collision_occurrences': occurrences,
    'distinct_valid_collision_pairs': len(replayed),
    'wall_seconds': finished - started,
    'protocol_sha256': sha(HERE / 'verify_protocol.json'),
}
(HERE / 'verification_result.json').write_text(json.dumps(out, sort_keys=True, indent=2) + '\n')
print(json.dumps(out, sort_keys=True))
