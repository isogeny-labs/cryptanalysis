"""Factor the frozen C-E resolvent at designated j=1728 C points."""
import json
from collections import Counter, defaultdict
from hashlib import sha256
from pathlib import Path

from sympy import Poly, Symbol, factor_list

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
X = Symbol('x_E')
PRIMES = (1319, 1367, 1439, 1753, 2917, 3037)


def rational(terms, x, y, p):
    out = 0
    for t in terms:
        raw = t['coefficient']
        a, b = (map(int, raw.split('/')) if '/' in raw else (int(raw), 1))
        out += a * pow(b, -1, p) * pow(x, t['x_power'], p) * pow(y, t['y_power'], p)
    return out % p


def curve_points(p):
    squares = defaultdict(list)
    for y in range(p):
        squares[y*y % p].append(y)
    half = pow(2, -1, p)
    return sorted((x,(z-1)*half % p) for x in range(p)
                  for z in squares[(4*(x*x*x-7)+1) % p])


def coefficients(terms, c, p):
    x,y = c
    out = [0]*13
    for t in terms:
        e = t['x_E_exponent']
        out[e] = (out[e] + int(t['integer_coefficient'])
                  * pow(x, t['x_C_exponent'], p)
                  * pow(y, t['y_C_exponent'], p)) % p
    return out


def main():
    cp = ROOT/'experiments/hecke-27-coordinate-bridge-20261025/coordinate_map.json'
    rp = ROOT/'experiments/hecke-432-relative-resolvent-20261025/relative_resolvent.json'
    coord = json.loads(cp.read_text())
    resolvent = json.loads(rp.read_text())
    rows = []
    for p in PRIMES:
        cs = []
        for x,y in curve_points(p):
            den = rational(coord['source_j']['denominator'],x,y,p)
            if den and (-rational(coord['source_j']['numerator'],x,y,p)*pow(den,-1,p)) % p == 1728 % p:
                cs.append((x,y))
        for c in cs:
            a = coefficients(resolvent['terms'],c,p)
            f = Poly.from_list(list(reversed(a)), X, modulus=p)
            _, factors = factor_list(f)
            degrees = sorted([q.degree() for q,m in factors for _ in range(m)])
            linear_roots = []
            for q,m in factors:
                if q.degree() != 1:continue
                b0,b1 = [int(q.nth(i)) % p for i in (0,1)]
                xe = -b0*pow(b1,-1,p) % p
                rhs = (xe**3+432) % p
                linear_roots.append({'x_E':xe,'multiplicity':m,
                                     'E_y_count':1 if rhs==0 else (2 if pow(rhs,(p-1)//2,p)==1 else 0)})
            rows.append({'prime':p,'C_point':list(c),'resolvent_degree':f.degree(),
                         'factor_degrees':degrees,'linear_roots':linear_roots})
        print(json.dumps({'prime':p,'C_points':len(cs),
                          'factor_patterns':{str(k):v for k,v in Counter(tuple(r['factor_degrees']) for r in rows if r['prime']==p).items()}}),flush=True)
    out={'status':'EXPLORATORY_CE_FACTORIZATION','primes':list(PRIMES),
         'inputs':{str(q.relative_to(ROOT)):sha256(q.read_bytes()).hexdigest() for q in (cp,rp)},
         'source_sha256':sha256(Path(__file__).read_bytes()).hexdigest(),'rows':rows}
    (HERE/'factor_sample.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')


if __name__ == '__main__':main()
