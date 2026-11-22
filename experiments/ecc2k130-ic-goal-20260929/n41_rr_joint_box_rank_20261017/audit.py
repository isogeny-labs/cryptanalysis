"""Independent Gaussian determinant and low-pivot replay of every box."""
import hashlib
import itertools
import json
import resource
import time
from pathlib import Path

D = Path(__file__).resolve().parent
S = D.parent / 'n41_sixpair_shared_target_20261017' / 'join_input.tsv'
MOD = (1 << 41) | (1 << 3) | 1
MASK = (1 << 41)-1

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def reduce(x):
    while x.bit_length() > 41:
        x ^= MOD << (x.bit_length()-42)
    return x

def mul(a, b):
    raw = 0
    while b:
        bit = b & -b
        raw ^= a << (bit.bit_length()-1)
        b ^= bit
    return reduce(raw)

def inv(a):
    assert a
    u, v, g, h = a, MOD, 1, 0
    while u != 1:
        j = u.bit_length()-v.bit_length()
        if j < 0:
            u, v, g, h = v, u, h, g
            j = -j
        u ^= v << j
        g ^= h << j
    return reduce(g)

def determinant(points):
    matrix = []
    for x, y in points:
        x2 = mul(x, x)
        matrix.append([1, x, y, x2, mul(x, y), mul(x2, x), mul(x2, y)])
    result = 1
    for col in range(7):
        pivot = next((r for r in range(col, 7) if matrix[r][col]), None)
        if pivot is None:
            return 0
        matrix[col], matrix[pivot] = matrix[pivot], matrix[col]
        value = matrix[col][col]
        result = mul(result, value)
        inverse = inv(value)
        assert mul(value, inverse) == 1
        for row in range(col+1, 7):
            if matrix[row][col] == 0:
                continue
            factor = mul(matrix[row][col], inverse)
            for c in range(col+1, 7):
                matrix[row][c] ^= mul(factor, matrix[col][c])
            matrix[row][col] = 0
    return result

def insert_low(basis, value):
    while value:
        bit = value & -value
        k = bit.bit_length()-1
        if k in basis:
            value ^= basis[k]
        else:
            basis[k] = value
            return True
    return False

def separation_mask(values):
    """Solve parity(mask & value)=1 for every recorded determinant."""
    basis = {}
    for value in values:
        row = value | (1 << 41)
        while row & MASK:
            k = (row & MASK).bit_length()-1
            if k in basis:
                row ^= basis[k]
            else:
                basis[k] = row
                break
        else:
            assert row == 0
    mask = 0
    for k in sorted(basis):
        row = basis[k]
        rhs = (row >> 41) & 1
        lower = row & ((1 << k)-1)
        bit = rhs ^ ((lower & mask).bit_count() & 1)
        mask |= bit << k
    assert all((mask & value).bit_count() & 1 for value in values)
    return mask

def add(p, q):
    if p is None:
        return q
    if q is None:
        return p
    x, y = p
    u, v = q
    if x == u:
        if y != v or x == 0:
            return None
        slope = x ^ mul(y, inv(x))
        xx = mul(slope, slope) ^ slope
        yy = mul(x, x) ^ mul(slope ^ 1, xx)
    else:
        slope = mul(y ^ v, inv(x ^ u))
        xx = mul(slope, slope) ^ slope ^ x ^ u
        yy = mul(slope, x ^ xx) ^ xx ^ y
    return xx, yy

started = time.monotonic()
panel = json.loads((D/'panel.json').read_text())
producer = json.loads((D/'result.json').read_text())
assert panel['source_sha256'] == sha(S)
assert producer['protocol_sha256'] == sha(D/'protocol.json')
lines = S.read_text().splitlines()
rows = {}
for line in lines[1:]:
    v = line.split()
    j, i = map(int, v[1:3])
    rows[j, i] = (int(v[9]), int(v[10]), int(v[7]), int(v[8]))
assert len(rows) == 960
target = tuple(panel['target'])
assert target == tuple(map(int, lines[0].split()[3:]))
negative_target = (target[0], target[0] ^ target[1])
checks = 0
certificates = []
group_matches = 0
for box, expected in zip(panel['panels'], producer['rows']):
    assert box['kind'] == expected['kind']
    basis = {}
    first = None
    zeros = 0
    count = 0
    values = []
    for ids in itertools.product(*box['slots']):
        selected = [rows[j, ids[j]] for j in range(6)]
        columns = [c for point in selected for c in point[2:]]
        assert len(set(columns)) == 12
        points = [(x, y) for x, y, _, _ in selected] + [negative_target]
        assert len({x for x, _ in points}) == 7
        value = determinant(points)
        group_sum = None
        for point in points[:6]:
            group_sum = add(group_sum, point)
        assert (value == 0) == (group_sum == target)
        group_matches += group_sum == target
        values.append(value)
        count += 1
        zeros += value == 0
        if first is None:
            first = value
        else:
            insert_low(basis, value ^ first)
        if len(basis) == 41:
            classification = 'NO_LINEAR_SEPARATOR'
            break
    else:
        residue = first
        for k in sorted(basis):
            if residue >> k & 1:
                residue ^= basis[k]
        classification = 'CERTIFIED_NO_ZERO' if residue else 'AFFINE_HULL_CONTAINS_ZERO'
    assert (count, len(basis), zeros, first, classification) == (
        expected['evaluated'], expected['difference_rank'],
        expected['zero_determinants_seen'], expected['first_determinant'],
        expected['classification'])
    if box['kind'] == 'sign':
        assert classification == 'CERTIFIED_NO_ZERO'
        certificates.append({'box': expected['box'],
                             'functional_mask': separation_mask(values),
                             'checked_values': len(values)})
    checks += count
witness = panel['witness_states']
points = [(rows[j, witness[j]][0], rows[j, witness[j]][1]) for j in range(6)]
sum_point = None
for point in points:
    sum_point = add(sum_point, point)
assert sum_point == target
assert determinant(points+[negative_target]) == 0
out = {'status': 'PASS', 'boxes': len(panel['panels']),
       'independent_determinants': checks, 'witness_states': witness,
       'independent_group_checks': checks, 'group_matches': group_matches,
       'sign_certificates': certificates,
       'witness_sum': sum_point, 'producer_result_sha256': sha(D/'result.json'),
       'panel_sha256': sha(D/'panel.json'), 'audit_source_sha256': sha(Path(__file__)),
       'wall_s': time.monotonic()-started,
       'peak_self_rss_bytes': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
(D/'audit_result.json').write_text(json.dumps(out, indent=2, sort_keys=True)+'\n')
print(json.dumps(out))
