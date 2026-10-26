"""Replay q-series identities and pivot minors without Sage linear algebra."""
import json
from hashlib import sha256
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
MAX_EXPONENT = 1050


class Laurent:
    def __init__(self, prime, lo, coefficients):
        self.prime = prime
        self.lo = lo
        self.a = np.asarray(coefficients, dtype=np.int64) % prime

    @classmethod
    def one(cls, prime):
        return cls(prime, 0, [1])

    def coefficient(self, exponent):
        index = exponent - self.lo
        return int(self.a[index]) if 0 <= index < len(self.a) else 0

    def __mul__(self, other):
        assert self.prime == other.prime
        lo = self.lo + other.lo
        product = np.convolve(self.a, other.a) % self.prime
        product = product[:max(0, MAX_EXPONENT - lo + 1)]
        return Laurent(self.prime, lo, product)


def determinant_mod(matrix, prime):
    rows = np.asarray(matrix, dtype=np.int64) % prime
    size = len(rows)
    assert all(len(row) == size for row in rows)
    determinant = 1
    for col in range(size):
        offsets = np.flatnonzero(rows[col:, col])
        if not len(offsets):
            return 0
        pivot = col + int(offsets[0])
        if pivot != col:
            rows[[col, pivot]] = rows[[pivot, col]]
            determinant = -determinant
        value = int(rows[col, col])
        determinant = determinant * value % prime
        inverse = pow(value, -1, prime)
        factors = rows[col + 1:, col] * inverse % prime
        rows[col + 1:, col + 1:] = (
            rows[col + 1:, col + 1:] - factors[:, None] * rows[col, col + 1:]
        ) % prime
        rows[col + 1:, col] = 0
    return determinant % prime


def powers(value, limit):
    out = [Laurent.one(value.prime)]
    for _ in range(limit):
        out.append(out[-1] * value)
    return out


def replay_cell(row, qrecord):
    p = row['prime']
    degree = row['weighted_degree']
    lo, hi = qrecord['coefficient_exponents']
    assert (lo, hi) == tuple(json.loads((HERE/'protocol.json').read_text())['stored_coefficients'])
    xc, yc, xb, yb, hx, hy = [Laurent(p, lo, qrecord[name])
                              for name in ('xc', 'yc', 'xb', 'yb', 'hx', 'hy')]
    xc2, xc3 = xc*xc, xc*xc*xc
    yc2, xb2, xb3 = yc*yc, xb*xb, xb*xb*xb
    yb2, hx3, hy2 = yb*yb, hx*hx*hx, hy*hy
    hx_xb2 = hx*xb2
    hy_xb3, yb_xb3 = hy*xb3, yb*xb3
    for n in range(-9, 981):
        assert (yc2.coefficient(n) + yc.coefficient(n)
                - xc3.coefficient(n) + (7 if n == 0 else 0)) % p == 0
        assert (yb2.coefficient(n) - xb3.coefficient(n)
                + (16 if n == 0 else 0)) % p == 0
        assert (hy2.coefficient(n) - hx3.coefficient(n)
                - (432 if n == 0 else 0)) % p == 0
        assert (hx_xb2.coefficient(n) - xb3.coefficient(n)
                + (64 if n == 0 else 0)) % p == 0
        assert (hy_xb3.coefficient(n) - yb_xb3.coefficient(n)
                - 128 * yb.coefficient(n)) % p == 0
    max_a = max(term[0] for term in row['a_terms'] + row['b_terms'])
    max_c = max(term[2] for term in row['a_terms'] + row['b_terms'])
    xpow, hpow = powers(xc, max_a), powers(hx, max_c)
    def monomial(term):
        a, b, c, d = term
        value = xpow[a] * hpow[c]
        if b:
            value = value * yc
        if d:
            value = value * hy
        return value
    columns = [monomial(term)*xb for term in row['a_terms']]
    columns += [monomial(term) for term in row['b_terms']]
    assert len(columns) == row['columns'] == len(row['pivot_rows'])
    train_lo = -(degree + 2)
    square = [[column.coefficient(train_lo + index)
               for column in columns] for index in row['pivot_rows']]
    determinant = determinant_mod(square, p)
    assert determinant == row['pivot_minor_determinant_mod_p'] != 0
    assert row['training_rank'] == row['extended_rank'] == row['columns']
    assert row['training_nullity'] == row['extended_nullity'] == 0
    return {'prime':p,'weighted_degree':degree,
            'columns':row['columns'],'pivot_minor_determinant_mod_p':determinant}


def main():
    protocol = json.loads((HERE/'protocol.json').read_text())
    result = json.loads((HERE/'screen_result.json').read_text())
    qrecords = json.loads((HERE/'qseries_modp.json').read_text())
    assert result['protocol_sha256'] == sha256((HERE/'protocol.json').read_bytes()).hexdigest()
    assert result['status'] == 'COMPLETE_FULL_E_DIRECT_LIFT_SCREEN'
    assert [r['prime'] for r in qrecords] == protocol['auxiliary_fields']
    assert len(result['rows']) == len(protocol['auxiliary_fields']) * len(protocol['weighted_degrees'])
    by_prime = {r['prime']:r for r in qrecords}
    checked = [replay_cell(row, by_prime[row['prime']]) for row in result['rows']]
    out = {'status':'PASS_INDEPENDENT_PIVOT_REPLAY',
           'numpy_version':np.__version__,'cells':checked}
    (HERE/'verification.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'status':out['status'],'cells':len(checked)},sort_keys=True))


if __name__ == '__main__':
    main()
