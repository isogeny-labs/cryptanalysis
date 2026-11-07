"""Independent replay of labels, extension divisors, and every block index.

Extension arithmetic here is pure Python polynomial arithmetic. It shares
neither FLINT extension fields nor the lift formulas. Block replay uses a
sequential group walk, not resultants, powering certificates, or BSGS.
No planted secret is needed for the full-construction replay or label audit.
"""
from hashlib import sha256
from pathlib import Path
import json
import random
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from core import Curve, prime_order_curve


class Field:
    def __init__(self, p, modulus):
        self.p, self.n, self.modulus = p, len(modulus)-1, modulus
        assert modulus[-1] == 1

    def value(self, x):
        if isinstance(x, int):
            return (x % self.p,)+(0,)*(self.n-1)
        return tuple(x)+(0,)*(self.n-len(x))

    def add(self, a, b):
        return tuple((x+y) % self.p for x, y in zip(a, b))

    def neg(self, a):
        return tuple(-x % self.p for x in a)

    def sub(self, a, b):
        return self.add(a, self.neg(b))

    def mul(self, a, b):
        c = [0]*(2*self.n-1)
        for i, x in enumerate(a):
            for j, y in enumerate(b):
                c[i+j] += x*y
        for k in range(2*self.n-2, self.n-1, -1):
            for j in range(self.n):
                c[k-self.n+j] -= c[k]*self.modulus[j]
        return tuple(x % self.p for x in c[:self.n])

    def power(self, a, exponent):
        result = self.value(1)
        while exponent:
            if exponent & 1:
                result = self.mul(result, a)
            a = self.mul(a, a); exponent >>= 1
        return result

    def divide(self, a, b):
        assert b != self.value(0)
        return self.mul(a, self.power(b, self.p**self.n-2))

    def evaluate(self, coefficients, a):
        result = self.value(0)
        for c in reversed(coefficients):
            result = self.add(self.mul(result, a), self.value(c))
        return result

    def point_add(self, E, P, Q):
        if P is None:
            return Q
        if Q is None:
            return P
        x, y = P; xx, yy = Q
        if x == xx:
            if self.add(y, yy) == self.value(0):
                return None
            numerator = self.add(self.mul(self.value(3), self.mul(x, x)), self.value(E.a))
            slope = self.divide(numerator, self.mul(self.value(2), y))
        else:
            slope = self.divide(self.sub(yy, y), self.sub(xx, x))
        rx = self.sub(self.sub(self.mul(slope, slope), x), xx)
        return rx, self.sub(self.mul(slope, self.sub(x, rx)), y)

    def orbit(self, R):
        points = [R]
        for _ in range(1, self.n):
            points.append(tuple(self.power(z, self.p) for z in points[-1]))
        assert tuple(self.power(z, self.p) for z in points[-1]) == R
        return points

    def check(self, E, R, T):
        x, y = R
        assert self.mul(y, y) == self.evaluate([E.b, E.a, 0, 1], x)
        total = None
        for point in self.orbit(R):
            total = self.point_add(E, total, point)
        assert total == (self.value(T[0]), self.value(T[1]))


def poly_mul(a, b, p):
    c = [0]*(len(a)+len(b)-1)
    for i, x in enumerate(a):
        for j, y in enumerate(b):
            c[i+j] = (c[i+j]+x*y) % p
    return c


def poly_sub(a, b, p):
    return [((a[i] if i < len(a) else 0)-(b[i] if i < len(b) else 0)) % p
            for i in range(max(len(a), len(b)))]


def audit_lifts(directory):
    benchmark = json.loads((directory/'lift_benchmark.json').read_text())
    witnesses = json.loads((directory/'lift_witnesses.json').read_text())
    lookup = {(r['p'], r['family'], r['trial']): r for r in benchmark['records']}
    labels = lifts = divisors = zeros = 0
    for witness in witnesses:
        b = lookup[witness['p'], witness['family'], witness['trial']]
        E = Curve(b['p'], *b['curve']); p, r = E.p, b['r']
        P, Q = tuple(b['P']), tuple(b['Q'])
        records = {v['T'][0]: v for v in witness['records']}
        fields = {}; extension_points = {}
        for x0, record in records.items():
            T = tuple(record['T'])
            assert E.add(E.mul(record['u'], P), E.mul(record['v'], Q)) == T
            labels += 1
            if witness['family'] == 'quadratic':
                F = Field(p, [-b['delta'], 0, 1])
                R = tuple(F.value(z) for z in record['R'])
                assert F.mul(R[0], F.power(R[0], p)) == F.value(1)
                assert 2*R[0][0] % p == record['parameter']
            else:
                F = Field(p, record['q']); x = F.value([0, 1, 0])
                assert F.power(x, p) != x
                assert F.power(x, p**3) == x
                u, w = record['interpolation']; X, Y = T
                v = (w*Y-X*X-u*X) % p
                y = F.neg(F.divide(F.evaluate([v, u, 1], x), F.value(w)))
                R = (x, y)
                common = Field(p, b['common_field_coefficients'])
                common.check(E, tuple(common.value(z) for z in record['coordinates']), T)
                lifts += 1
            F.check(E, R, T); lifts += 1
            fields[x0], extension_points[x0] = F, R
        for divisor in witness['divisors']:
            relation = list(map(tuple, divisor['trace_relation']))
            assert len({T[0] for T in relation}) == 3 and E.sum(relation) is None
            su = sv = 0; expected = [1]
            coeff = divisor['divisor_coefficients']
            if witness['family'] == 'quadratic':
                g, k = coeff[:3]+[1], coeff[3:]
                H = poly_sub(poly_mul(g, g, p), poly_mul(poly_mul(k, k, p), [E.b, E.a, 0, 1], p), p)
            else:
                g, k = coeff[:5], coeff[5:]+[1]
                H = poly_sub(poly_mul(poly_mul(k, k, p), [E.b, E.a, 0, 1], p), poly_mul(g, g, p), p)
            for T in relation:
                record = records[T[0]]; F = fields[T[0]]
                x, y = extension_points[T[0]]
                sign = 1 if T == tuple(record['T']) else -1
                if sign == -1:
                    y = F.neg(y)
                su += sign*record['u']; sv += sign*record['v']
                factor = [1, -record['parameter'], 1] if witness['family'] == 'quadratic' else record['q']
                expected = poly_mul(expected, factor, p)
                for xx, yy in F.orbit((x, y)):
                    assert F.add(F.evaluate(g, xx), F.mul(F.evaluate(k, xx), yy)) == F.value(0)
                    zeros += 1
            assert H == expected
            assert [su % r, sv % r] == divisor['label_sum']
            assert sv % r
            d = -su*pow(sv % r, -1, r) % r
            assert E.mul(d, P) == Q
            divisors += 1
    return {'known_labels_verified': labels, 'extension_lifts_verified': lifts,
            'principal_divisors_verified': divisors, 'extension_divisor_zeros_verified': zeros}


def replay_block(E, P, Q, u, M, B):
    R = E.add(Q, E.mul(u, P)); hits = []; identities = []; points = {}
    for j in range(M):
        if R is None:
            identities.append(j)
        elif pow(R[0], B, E.p) == 1:
            hits.append(j); points[j] = R
        if j+1 < M:
            R = E.add(R, P)
    return hits, identities, points


def audit_blocks(directory):
    benchmark = json.loads((directory/'block_benchmark.json').read_text())
    transcripts = json.loads((directory/'block_transcripts.json').read_text())
    unique = {}; walks = hits_seen = indices = 0
    for record in benchmark['block_records']:
        key = record['p'], record['B'], record['trial']
        if key not in unique:
            E, r, P = prime_order_curve(record['p'])
            secret = random.Random(20261027+E.p+record['B']).randrange(1, r)
            Q = E.mul(secret, P)
            hits, identities, _ = replay_block(E, P, Q, record['input_u'], record['M'], record['B'])
            unique[key] = hits, identities; walks += 1; indices += record['M']
        assert unique[key] == (record['hit_indices'], record['identity_indices'])
        assert len(record['hit_indices']) == record['hits']
        hits_seen += record['hits']
    E, r, _ = prime_order_curve(65537)
    for transcript in transcripts:
        P, Q = tuple(transcript['P']), tuple(transcript['Q']); known = {}
        trial = transcript['trial']; trace = transcript['blocks']
        hashed = sha256(json.dumps(trace, separators=(',', ':')).encode()).hexdigest()
        for record in benchmark['complete_constructions']:
            if record['trial'] == trial:
                assert record['transcript_sha256'] == hashed
        for u, jj, oo in trace:
            hits, identities, points = replay_block(E, P, Q, u, 2048, 64)
            assert hits == jj and identities == oo
            assert len(known) < 33
            for j, point in sorted(points.items()):
                known.setdefault(point[0], (point, (u+j) % r))
            walks += 1; indices += 2048; hits_seen += len(jj)
        assert len(known) == 33
        assert [[x, list(point), label] for x, (point, label) in sorted(known.items())] == transcript['known']
        for point, label in known.values():
            assert E.add(E.mul(label, P), Q) == point
    return {'independent_progression_blocks_replayed': walks,
            'progression_indices_replayed': indices,
            'hit_indices_checked_in_records': hits_seen,
            'complete_construction_transcripts_verified': len(transcripts)}


def main():
    directory = Path(__file__).resolve().parent
    result = dict(audit_lifts(directory), **audit_blocks(directory), errors=0)
    (directory/'audit.json').write_text(json.dumps(result, indent=2)+'\n')
    print(result)


if __name__ == '__main__':
    main()
