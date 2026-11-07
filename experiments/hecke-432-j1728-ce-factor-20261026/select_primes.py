"""Source-free prospective prime selection for resolvent factor parity."""
import json
from collections import defaultdict
from hashlib import sha256
from pathlib import Path

from sympy import Poly, Symbol, factor_list, primerange

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
X = Symbol('x_C')


def eval_poly(a, x, p):
    z = 0
    for c in reversed(a):z = (z*x+c) % p
    return z


def rational(terms,x,y,p):
    out = 0
    for t in terms:
        raw = t['coefficient']
        a,b = (map(int,raw.split('/')) if '/' in raw else (int(raw),1))
        out += a*pow(b,-1,p)*pow(x,t['x_power'],p)*pow(y,t['y_power'],p)
    return out % p


def main():
    pp = HERE/'protocol.json'
    protocol = json.loads(pp.read_text())
    assert protocol['status']=='FROZEN_BEFORE_PROSPECTIVE_SOURCE_SELECTION'
    for rec in protocol['inputs'].values():
        assert sha256(Path(rec['path']).read_bytes()).hexdigest()==rec['sha256']
    cp = Path(protocol['inputs']['coordinate']['path'])
    ep = Path(protocol['inputs']['eliminant']['path'])
    coord = json.loads(cp.read_text())
    a = list(map(int,json.loads(ep.read_text())['factors'][0]['coefficients_low_to_high']))
    cells = []; selected = defaultdict(list)
    for p in primerange(protocol['lower_bound_inclusive'],protocol['upper_bound_exclusive']):
        residue = int(p)%12
        if residue not in (1,5,11) or len(selected[residue])>=3:continue
        f = Poly.from_list(list(reversed(a)),X,modulus=int(p))
        _, factors = factor_list(f)
        roots = []
        for q,_ in factors:
            if q.degree()!=1:continue
            b0,b1 = [int(q.nth(i))%p for i in (0,1)]
            roots.append(-b0*pow(b1,-1,p)%p)
        assert all(eval_poly(a,x,int(p))==0 for x in roots)
        squares = defaultdict(list)
        for y in range(int(p)):squares[y*y%p].append(y)
        half = pow(2,-1,int(p)); cs = []
        for x in roots:
            for z in squares[(4*(x*x*x-7)+1)%p]:
                y = (z-1)*half%p
                den = rational(coord['source_j']['denominator'],x,y,int(p))
                if den and -rational(coord['source_j']['numerator'],x,y,int(p))*pow(den,-1,int(p))%p==1728%p:
                    cs.append([x,y])
        cs.sort()
        cell = {'prime':int(p),'class_mod_12':residue,'eliminant_x_roots':len(roots),'C_points':cs}
        cells.append(cell)
        if residue==5 or (residue==1 and len(cs)>=18) or (residue==11 and len(cs)>=2):
            selected[residue].append(cell)
            print(json.dumps({'selected_prime':int(p),'class_mod_12':residue,'C_points':len(cs)}),flush=True)
        if all(len(selected[r])>=3 for r in (1,5,11)):break
    out = {'status':'PROSPECTIVE_SOURCE_SELECTION_COMPLETE' if all(len(selected[r])>=3 for r in (1,5,11)) else 'BOUNDED_SOURCE_SELECTION_INCOMPLETE',
           'protocol_sha256':sha256(pp.read_bytes()).hexdigest(),
           'source_sha256':sha256(Path(__file__).read_bytes()).hexdigest(),
           'cells':cells,'selected':{str(k):v for k,v in selected.items()}}
    (HERE/'selection.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'status':out['status'],'cells':len(cells),'selected':{k:len(v) for k,v in selected.items()}}))


if __name__=='__main__':main()
