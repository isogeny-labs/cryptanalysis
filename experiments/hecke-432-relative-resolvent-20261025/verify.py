"""Independent NumPy replay of relative-resolvent pivot minors."""
import json
from hashlib import sha256
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
MAX_EXPONENT = 1050


class Laurent:
    def __init__(self, p, lo, coefficients):
        self.p = p
        self.lo = lo
        self.a = np.asarray(coefficients,dtype=np.int64) % p

    @classmethod
    def one(cls,p):
        return cls(p,0,[1])

    def coefficient(self,n):
        index = n-self.lo
        return int(self.a[index]) if 0 <= index < len(self.a) else 0

    def __mul__(self,other):
        assert self.p == other.p
        lo = self.lo+other.lo
        values = np.convolve(self.a,other.a) % self.p
        return Laurent(self.p,lo,values[:max(0,MAX_EXPONENT-lo+1)])


def powers(value,limit):
    out = [Laurent.one(value.p)]
    for _ in range(limit):
        out.append(out[-1]*value)
    return out


def determinant_mod(square,p):
    rows = np.asarray(square,dtype=np.int64) % p
    n = len(rows)
    assert rows.shape == (n,n)
    det = 1
    for col in range(n):
        offsets = np.flatnonzero(rows[col:,col])
        assert len(offsets),(col,n)
        pivot = col+int(offsets[0])
        if pivot != col:
            rows[[col,pivot]] = rows[[pivot,col]]
            det = -det
        value = int(rows[col,col])
        det = det*value % p
        factors = rows[col+1:,col]*pow(value,-1,p) % p
        rows[col+1:,col+1:] = (rows[col+1:,col+1:]
                              - factors[:,None]*rows[col,col+1:]) % p
        rows[col+1:,col] = 0
    return det % p


def replay_cell(row,record):
    p = row['prime']
    lo,hi = record['coefficient_exponents']
    assert (lo,hi) == (-3,1050)
    xc,yc,xe = (Laurent(p,lo,record[name]) for name in ('xc','yc','hx'))
    xcp = powers(xc,max(t[0] for t in row['terms']))
    xep = powers(xe,12)
    columns = [xcp[a]*xep[c]*(yc if b else Laurent.one(p))
               for a,b,c in row['terms']]
    assert len(columns) == row['columns'] == len(row['pivot_rows'])
    square = [[col.coefficient(-row['weighted_degree']+r)
               for col in columns] for r in row['pivot_rows']]
    det = determinant_mod(square,p)
    assert det == row['pivot_minor_determinant_mod_p'] != 0
    assert row['training_rank'] == row['columns']
    assert row['training_nullity'] == 0 and not row['kernel_basis']
    return {'prime':p,'weighted_degree':row['weighted_degree'],
            'columns':row['columns'],'pivot_minor_determinant_mod_p':det}


def main():
    protocol_path = HERE/'protocol.json'
    result_path = HERE/'screen_result.json'
    source_path = ROOT/'hecke-432-full-e-lift-20261025'/'qseries_modp.json'
    verified_path = ROOT/'hecke-432-full-e-lift-20261025'/'verification.json'
    protocol = json.loads(protocol_path.read_text())
    result = json.loads(result_path.read_text())
    source = json.loads(source_path.read_text())
    assert result['status'] == 'COMPLETE_RELATIVE_RESOLVENT_SCREEN'
    assert result['protocol_sha256'] == sha256(protocol_path.read_bytes()).hexdigest()
    assert result['source_sha256'] == sha256(source_path.read_bytes()).hexdigest()
    assert result['source_verification_sha256'] == sha256(verified_path.read_bytes()).hexdigest()
    assert len(result['rows']) == len(protocol['weighted_degrees'])*len(source)
    by_prime = {r['prime']:r for r in source}
    rows = [replay_cell(row,by_prime[row['prime']]) for row in result['rows']]
    out = {'status':'PASS_INDEPENDENT_RELATIVE_RESOLVENT_PIVOTS',
           'numpy_version':np.__version__,'cells':rows,
           'screen_result_sha256':sha256(result_path.read_bytes()).hexdigest()}
    (HERE/'verification.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'status':out['status'],'cells':len(rows)},sort_keys=True))


if __name__=='__main__':
    main()
