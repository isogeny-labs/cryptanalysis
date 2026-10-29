"""Independent Sage replay of every tested C-E resolvent factorization."""
import json
from hashlib import sha256
from pathlib import Path

from sage.all import GF, PolynomialRing

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def rational(terms,x,y,F):
    total = F(0)
    for term in terms:
        raw = term['coefficient']
        a,b = (map(int,raw.split('/')) if '/' in raw else (int(raw),1))
        total += F(a)/F(b)*x**term['x_power']*y**term['y_power']
    return total


def audit_row(row,terms,coordinate):
    p = row['prime']; F = GF(p); R = PolynomialRing(F,'t'); t = R.gen()
    x,y = map(F,row['C_point'])
    assert y*y+y==x*x*x-7
    jrec = coordinate['source_j']
    den = rational(jrec['denominator'],x,y,F)
    assert den and -rational(jrec['numerator'],x,y,F)/den==F(1728)
    poly = R.zero()
    for term in terms:
        poly += F(int(term['integer_coefficient']))*x**term['x_C_exponent']*y**term['y_C_exponent']*t**term['x_E_exponent']
    assert poly.degree()==12
    degrees = sorted([int(f.degree()) for f,m in poly.factor() for _ in range(m)])
    assert degrees==row['factor_degrees']
    roots = sorted((int(z),int(m)) for z,m in poly.roots())
    stored_roots = sorted((a['x_E'],a['multiplicity']) for a in row['linear_roots'])
    assert roots==stored_roots
    pair_count = 0
    for z,_ in roots:
        rhs = F(z)**3+432
        pair_count += 1 if rhs==0 else (2 if rhs.is_square() else 0)
    assert pair_count==row['rational_CE_pairs']
    return degrees,pair_count


def main():
    cp=ROOT/'experiments/hecke-27-coordinate-bridge-20261025/coordinate_map.json'
    rp=ROOT/'experiments/hecke-432-relative-resolvent-20261025/relative_resolvent.json'
    coordinate=json.loads(cp.read_text()); terms=json.loads(rp.read_text())['terms']
    receipts={}; total=0
    for name in ('test_result','refined_test_result'):
        path=HERE/(name+'.json'); result=json.loads(path.read_text())
        patterns={}; pairs=0
        for row in result['rows']:
            degrees,n=audit_row(row,terms,coordinate)
            key=str(tuple(degrees));patterns[key]=patterns.get(key,0)+1
            pairs+=n;total+=1
        receipts[name]={'sha256':sha256(path.read_bytes()).hexdigest(),
                        'rows':len(result['rows']),'factor_patterns':patterns,'rational_CE_pairs':pairs}
    out={'status':'PASS_INDEPENDENT_SAGE_FACTOR_AUDIT','rows':total,
         'inputs':{str(q.relative_to(ROOT)):sha256(q.read_bytes()).hexdigest() for q in (cp,rp)},
         'receipts':receipts}
    (HERE/'audit_sage.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
    print(json.dumps(out,sort_keys=True))


if __name__=='__main__':main()
