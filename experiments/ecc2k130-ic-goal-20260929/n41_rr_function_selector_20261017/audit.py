"""Independent source/group and serialized-formula receipt audit."""
import hashlib
import json
from math import comb
from pathlib import Path

D = Path(__file__).resolve().parent
S = D.parent / 'n41_sixpair_shared_target_20261017' / 'join_input.tsv'
MOD = (1 << 41) | (1 << 3) | 1
WITNESS = (12, 122, 116, 47, 128, 34)
COEFF = (1, 1200046331721, 51193325258, 197579618746,
         1789122703940, 761080510426, 107927970499)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def mul(a, b):
    c = 0
    while b:
        c ^= a << ((b & -b).bit_length() - 1)
        b &= b - 1
    while c.bit_length() > 41:
        c ^= MOD << (c.bit_length() - 42)
    return c


def inv(a):
    assert a
    u, v, g, h = a, MOD, 1, 0
    while u != 1:
        shift = u.bit_length() - v.bit_length()
        if shift < 0:
            u, v, g, h = v, u, h, g
            shift = -shift
        u ^= v << shift
        g ^= h << shift
    while g.bit_length() > 41:
        g ^= MOD << (g.bit_length() - 42)
    return g


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


def row(point):
    x, y = point
    x2 = mul(x, x)
    return (mul(x2, y), mul(x2, x), x2, x, mul(x, y), y, 1)


def audit_formula(suffix):
    formula = D / ('formula' + suffix + '.xcnf')
    build = json.loads((D / ('build_result' + suffix + '.json')).read_text())
    query = json.loads((D / ('query_result' + suffix + '.json')).read_text())
    stdout = D / ('solver' + suffix + '.stdout')
    stderr = D / ('solver' + suffix + '.stderr')
    assert sha(formula) == build['formula_sha256']
    assert formula.stat().st_size == build['formula_bytes']
    assert sha(stdout) == query['stdout_sha256']
    assert sha(stderr) == query['stderr_sha256']
    assert query['status'] == 'BOUNDED_UNKNOWN' and query['parent_cap']
    assert not [line for line in stdout.read_text().splitlines()
                if line.startswith('s SATISFIABLE') or line.startswith('s UNSATISFIABLE')]
    with formula.open() as stream:
        header = stream.readline().split()
        assert header[:2] == ['p', 'cnf']
        assert int(header[2]) == build['variables']
        clauses = xors = 0
        for line in stream:
            if line.startswith('x '):
                xors += 1
            elif line and line[0] not in 'cp':
                clauses += 1
        assert clauses == build['cnf_clauses']
        assert xors == build['native_xor_rows']
        assert int(header[3]) == clauses + xors
    return {'formula_sha256': sha(formula), 'bytes': formula.stat().st_size,
            'variables': build['variables'], 'cnf_clauses': clauses,
            'native_xor_rows': xors, 'query_status': query['status'],
            'solver_wall_s': query['wall_s'],
            'peak_child_rss_bytes': query['peak_child_rss_bytes']}


def main():
    protocol = json.loads((D / 'protocol.json').read_text())
    assert sha(S) == protocol['source_sha256']
    lines = S.read_text().splitlines()
    head = lines[0].split()
    assert head[:3] == ['ECC2K41', '6', '160']
    target = tuple(map(int, head[3:5]))
    assert list(target) == protocol['target']
    points = {}
    codes = {}
    for line in lines[1:]:
        fields = line.split()
        assert fields[0] == 'S'
        slot, state = map(int, fields[1:3])
        key = slot, state
        assert key not in points
        points[key] = tuple(map(int, fields[9:11]))
        codes[key] = tuple(map(int, fields[7:9]))
    assert len(points) == 960
    selected = [points[slot, state] for slot, state in enumerate(WITNESS)]
    selected_codes = [c for slot, state in enumerate(WITNESS)
                      for c in codes[slot, state]]
    assert len(set(selected_codes)) == 12
    assert len({p[0] for p in selected + [(target[0], target[1] ^ target[0])]}) == 7
    assert all(mul(y, y) ^ mul(x, y) == mul(mul(x, x), x) ^ 1
               for x, y in selected)
    total = None
    for point in selected:
        total = add(total, point)
    assert total == target
    for point in selected + [(target[0], target[1] ^ target[0])]:
        value = 0
        for c, a in zip(COEFF, row(point)):
            value ^= mul(c, a)
        assert value == 0
    size = 4_196_872
    result = {'status': 'AUDIT_PASS', 'source_sha256': sha(S),
              'witness_group_sum': list(total), 'selected_states': list(WITNESS),
              'distinct_columns': len(set(selected_codes)),
              'distinct_x': len({p[0] for p in selected + [target]}),
              'v1': audit_formula(''), 'v2': audit_formula('_v2'),
              'v3': audit_formula('_v3'),
              'n131_direct_pairwise_amo_clauses': 6 * comb(size, 2),
              'n131_sequential_amo_clauses': 6 * (3 * size - 4),
              'n131_direct_selector_variables': 6 * size,
              'n131_states_per_slot': size}
    (D / 'audit_result.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
