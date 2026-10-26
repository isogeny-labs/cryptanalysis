"""Replay the y-only q-series minors using NumPy, without Sage matrices."""
import json
from hashlib import sha256
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
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
        index = exponent-self.lo
        return int(self.a[index]) if 0 <= index < len(self.a) else 0

    def __mul__(self, other):
        assert self.prime == other.prime
        lo = self.lo+other.lo
        product = np.convolve(self.a,other.a) % self.prime
        product = product[:max(0,MAX_EXPONENT-lo+1)]
        return Laurent(self.prime,lo,product)


def powers(value, limit):
    out = [Laurent.one(value.prime)]
    for _ in range(limit):
        out.append(out[-1]*value)
    return out


def determinant_mod(square, prime):
    rows = np.asarray(square,dtype=np.int64) % prime
    size = len(rows)
    assert rows.shape == (size,size)
    determinant = 1
    for col in range(size):
        offsets = np.flatnonzero(rows[col:,col])
        assert len(offsets),(col,size)
        pivot = col+int(offsets[0])
        if pivot != col:
            rows[[col,pivot]] = rows[[pivot,col]]
            determinant = -determinant
        value = int(rows[col,col])
        determinant = determinant*value % prime
        factors = rows[col+1:,col]*pow(value,-1,prime) % prime
        rows[col+1:,col+1:] = (rows[col+1:,col+1:]
                              - factors[:,None]*rows[col,col+1:]) % prime
        rows[col+1:,col] = 0
    return determinant % prime


def replay_cell(row, qrecord):
    p = row['prime']
    lo,hi = qrecord['coefficient_exponents']
    assert (lo,hi) == (-3,1050)
    xc,yc,xb,ye = (Laurent(p,lo,qrecord[name])
                   for name in ('xc','yc','xb','hy'))
    terms = row['a_terms']+row['b_terms']
    xc_powers = powers(xc,max(t[0] for t in terms))
    ye_powers = powers(ye,max(t[2] for t in terms))
    def monomial(term):
        a,b,k = term
        value = xc_powers[a]*ye_powers[k]
        return value*yc if b else value
    columns = [monomial(term)*xb for term in row['a_terms']]
    columns += [monomial(term) for term in row['b_terms']]
    assert len(columns) == row['columns'] == len(row['pivot_rows'])
    train_lo = -(row['weighted_degree']+2)
    square = [[column.coefficient(train_lo+index)
               for column in columns] for index in row['pivot_rows']]
    determinant = determinant_mod(square,p)
    assert determinant == row['pivot_minor_determinant_mod_p'] != 0
    assert row['training_rank'] == row['columns']
    assert row['training_nullity'] == 0
    assert not row['kernel_basis_holdout']
    return {'prime':p,'weighted_degree':row['weighted_degree'],
            'columns':row['columns'],'pivot_minor_determinant_mod_p':determinant}


def main():
    protocol_path = HERE/'protocol.json'
    result_path = HERE/'screen_result.json'
    source_path = ROOT/'hecke-432-full-e-lift-20261025'/'qseries_modp.json'
    prior_path = ROOT/'hecke-432-full-e-lift-20261025'/'verification.json'
    protocol = json.loads(protocol_path.read_text())
    result = json.loads(result_path.read_text())
    source = json.loads(source_path.read_text())
    prior = json.loads(prior_path.read_text())
    assert result['status'] == 'COMPLETE_Y_ONLY_RATIONAL_LIFT_SCREEN'
    assert result['protocol_sha256'] == sha256(protocol_path.read_bytes()).hexdigest()
    assert result['qseries_source_sha256'] == sha256(source_path.read_bytes()).hexdigest()
    assert result['qseries_independent_verification_sha256'] == sha256(prior_path.read_bytes()).hexdigest()
    assert prior['status'] == 'PASS_INDEPENDENT_PIVOT_REPLAY'
    assert [r['prime'] for r in source] == protocol['auxiliary_fields']
    assert len(result['rows']) == len(source)*len(protocol['weighted_degrees'])
    by_prime = {r['prime']:r for r in source}
    cells = [replay_cell(row,by_prime[row['prime']]) for row in result['rows']]
    out = {'status':'PASS_INDEPENDENT_Y_ONLY_PIVOT_REPLAY',
           'numpy_version':np.__version__,'cells':cells,
           'screen_result_sha256':sha256(result_path.read_bytes()).hexdigest()}
    (HERE/'verification.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'status':out['status'],'cells':len(cells)},sort_keys=True))


if __name__ == '__main__':
    main()
