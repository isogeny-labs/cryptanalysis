"""Replay q-series identities and pivot minors without Sage linear algebra."""
import json
from hashlib import sha256
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
MAX_EXPONENT = 320


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
    rows = [list(map(int, row)) for row in matrix]
    size = len(rows)
    assert all(len(row) == size for row in rows)
    determinant = 1
    for col in range(size):
        pivot = next((r for r in range(col, size) if rows[r][col] % prime), None)
        if pivot is None:
            return 0
        if pivot != col:
            rows[col], rows[pivot] = rows[pivot], rows[col]
            determinant = -determinant
        value = rows[col][col] % prime
        determinant = determinant * value % prime
        inverse = pow(value, -1, prime)
        for row in range(col + 1, size):
            factor = rows[row][col] * inverse % prime
            if factor:
                for j in range(col + 1, size):
                    rows[row][j] = (rows[row][j] - factor * rows[col][j]) % prime
                rows[row][col] = 0
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
    assert (lo, hi) == (-3, MAX_EXPONENT)
    xc, yc, xb, hx = [Laurent(p, lo, qrecord[name])
                      for name in ('xc', 'yc', 'xb', 'hx')]
    xc2, xc3 = xc*xc, xc*xc*xc
    yc2, xb2, xb3 = yc*yc, xb*xb, xb*xb*xb
    hx_xb2 = hx*xb2
    for n in range(-6, 281):
        assert (yc2.coefficient(n) + yc.coefficient(n)
                - xc3.coefficient(n) + (7 if n == 0 else 0)) % p == 0
        assert (hx_xb2.coefficient(n) - xb3.coefficient(n)
                + (64 if n == 0 else 0)) % p == 0
    max_a = max(term[0] for term in row['a_terms'] + row['b_terms'])
    max_c = max(term[2] for term in row['a_terms'] + row['b_terms'])
    xpow, hpow = powers(xc, max_a), powers(hx, max_c)
    def monomial(term):
        a, b, c = term
        value = xpow[a] * hpow[c]
        return value * yc if b else value
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
    assert result['status'] == 'COMPLETE_BOUNDED_DIRECT_LIFT_SCREEN'
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
