"""Independent Gaussian and curve-sum replay of N131 alternate-root charts."""
import hashlib
import json
import time
from pathlib import Path

D = Path(__file__).resolve().parent
ROOT = D.parent
ARCHIVE = ROOT / 'n41_n131_rr_code_family_span_20261017'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    start = time.monotonic()
    protocol = json.loads((D / 'holdout_protocol.json').read_text())
    result = json.loads((D / 'holdout_result.json').read_text())
    panel = json.loads((ARCHIVE / 'panel_n131_v2.json').read_text())
    assert result['protocol_sha256'] == sha(D / 'holdout_protocol.json')
    assert all(sha(Path(path)) == digest for path, digest in protocol['sources'].items())
    n, modulus = panel['field_degree'], panel['field_modulus']
    assert n == 131

    def mul(a, b):
        c = 0
        while b:
            c ^= a << ((b & -b).bit_length() - 1)
            b &= b - 1
        while c.bit_length() > n:
            c ^= modulus << (c.bit_length() - n - 1)
        return c

    def inv(a):
        assert a
        u, v, g, h = a, modulus, 1, 0
        while u != 1:
            shift = u.bit_length() - v.bit_length()
            if shift < 0:
                u, v, g, h = v, u, h, g
                shift = -shift
            u ^= v << shift
            g ^= h << shift
        while g.bit_length() > n:
            g ^= modulus << (g.bit_length() - n - 1)
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

    def determinant(points):
        rows = []
        for x, y in points:
            x2 = mul(x, x)
            rows.append([1, x, y, x2, mul(x, y), mul(x2, x), mul(x2, y)])
        value = 1
        for column in range(7):
            pivot = next((r for r in range(column, 7) if rows[r][column]), None)
            if pivot is None:
                return 0
            rows[column], rows[pivot] = rows[pivot], rows[column]
            p = rows[column][column]
            value = mul(value, p)
            reciprocal = inv(p)
            for r in range(column + 1, 7):
                if rows[r][column]:
                    scale = mul(rows[r][column], reciprocal)
                    for c in range(column + 1, 7):
                        rows[r][c] ^= mul(scale, rows[column][c])
                    rows[r][column] = 0
        return value

    checks = 0
    group_hits = 0
    for i, variant in enumerate(panel['variants']):
        saved = result['rows'][i]
        assert saved['status'] == 'VALID_CHART' and saved['chart_index'] == i
        base = [tuple(variant['roots'][1][0])] + [tuple(p) for p in panel['fixed_points']]
        for sign in range(64):
            points = [(x, y ^ x if sign >> slot & 1 else y)
                      for slot, (x, y) in enumerate(base)]
            value = determinant(points + [(panel['target'][0],
                                           panel['target'][1] ^ panel['target'][0])])
            assert value == saved['values'][sign]
            total = None
            for point in points:
                total = add(total, point)
            assert (value == 0) == (total == tuple(panel['target']))
            group_hits += total == tuple(panel['target'])
            checks += 1
    assert checks == 256 and group_hits == 0
    audit = {'status': 'N131_ALTERNATE_ROOT_INDEPENDENT_AUDIT_PASS',
             'holdout_result_sha256': sha(D / 'holdout_result.json'),
             'determinants_checked': checks, 'group_sums_checked': checks,
             'group_hits': group_hits, 'wall_s': time.monotonic() - start}
    (D / 'holdout_audit_result.json').write_text(json.dumps(audit, sort_keys=True, indent=2) + '\n')
    print(json.dumps(audit, sort_keys=True))


if __name__ == '__main__':
    main()
