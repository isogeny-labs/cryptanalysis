"""Source-only selection for the fresh 11 mod 24 sqrt2 holdout."""
import json
from hashlib import sha256
from pathlib import Path

from sage.all import GF, PolynomialRing, prime_range

HERE=Path(__file__).resolve().parent


def rational(terms,x,y,F):
    value=F(0)
    for t in terms:
        raw=t['coefficient'];a,b=(map(int,raw.split('/')) if '/' in raw else (int(raw),1))
        value+=F(a)/F(b)*x**t['x_power']*y**t['y_power']
    return value


def main():
    pp=HERE/'holdout_protocol.json';protocol=json.loads(pp.read_text())
    assert protocol['status']=='FROZEN_BEFORE_SQRT2_FROBENIUS_HOLDOUT'
    for rec in protocol['inputs'].values():
        assert sha256(Path(rec['path']).read_bytes()).hexdigest()==rec['sha256']
    coord=json.loads(Path(protocol['inputs']['coordinate']['path']).read_text())['source_j']
    factor=json.loads(Path(protocol['inputs']['eliminant']['path']).read_text())['factors'][0]
    cells=[];selected=[]
    for p in prime_range(protocol['lower_bound_inclusive'],protocol['upper_bound_exclusive']):
        p=int(p)
        if p%24!=11:continue
        F=GF(p);R=PolynomialRing(F,'x')
        f=R([F(int(c)) for c in factor['coefficients_low_to_high']])
        roots=f.roots()
        cs=[]
        for x,m in roots:
            discriminant=4*(x**3-7)+1
            if not discriminant.is_square():continue
            z=discriminant.sqrt()
            for w in set((z,-z)):
                y=(w-1)/2
                den=rational(coord['denominator'],x,y,F)
                if den and -rational(coord['numerator'],x,y,F)/den==F(1728):
                    cs.append([int(x),int(y)])
        cell={'prime':p,'eliminant_x_roots':len(roots),'C_points':sorted(cs)}
        cells.append(cell)
        if len(cs)==2:
            selected.append(cell)
            print(json.dumps({'selected_prime':p,'C_points':len(cs)}),flush=True)
        if len(selected)==3:break
    out={'status':'SELECTED_THREE_SQRT2_FROBENIUS_PRIMES' if len(selected)==3 else 'BOUNDED_SELECTION_INCOMPLETE',
         'protocol_sha256':sha256(pp.read_bytes()).hexdigest(),
         'source_sha256':sha256(Path(__file__).read_bytes()).hexdigest(),
         'cells':cells,'selected':selected}
    (HERE/'holdout_selection.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'status':out['status'],'examined':len(cells)}))


if __name__=='__main__':main()
