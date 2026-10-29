"""Direct finite-field audit at the denominator's nonsquare-prime exceptions."""
import json
from hashlib import sha256
from pathlib import Path

from sage.all import GF, PolynomialRing

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]


def rational(terms,x,y,F):
    value=F(0)
    for t in terms:
        raw=t['coefficient'];a,b=(map(int,raw.split('/')) if '/' in raw else (int(raw),1))
        value+=F(a)/F(b)*x**t['x_power']*y**t['y_power']
    return value


def main():
    audit_path=HERE/'sqrt3_audit.json';audit=json.loads(audit_path.read_text())
    cert_path=HERE/'sqrt3_certificate.json';cert=json.loads(cert_path.read_text())
    assert audit['certificate_sha256']==sha256(cert_path.read_bytes()).hexdigest()
    coord_path=ROOT/'experiments/hecke-27-coordinate-bridge-20261025/coordinate_map.json'
    coord=json.loads(coord_path.read_text())['source_j']
    cells=[]
    for p in audit['exceptional_nonsquare_primes']:
        F=GF(p);R=PolynomialRing(F,'x')
        f=R([F(int(c)) for c in cert['field_polynomial_coefficients_low_to_high']])
        x_roots=f.roots()
        cs=[];root_rows=[]
        for x,m in x_roots:
            discriminant=4*(x**3-7)+1
            root_row={'x_C':int(x),'multiplicity':int(m),
                      'curve_discriminant':int(discriminant),
                      'curve_discriminant_square':bool(discriminant.is_square())}
            root_rows.append(root_row)
            if not discriminant.is_square():continue
            z=discriminant.sqrt()
            for w in set((z,-z)):
                y=(w-1)/2
                assert y*y+y==x**3-7
                den=rational(coord['denominator'],x,y,F)
                if den and -rational(coord['numerator'],x,y,F)/den==F(1728):
                    cs.append([int(x),int(y)])
        cell={'prime':p,'eliminant_x_roots':len(x_roots),
              'x_root_details':root_rows,'source_j1728_C_points':sorted(cs)}
        cells.append(cell)
        print(json.dumps(cell,sort_keys=True),flush=True)
    out={'status':'EXACT_EXCEPTIONAL_PRIME_AUDIT',
         'sqrt3_audit_sha256':sha256(audit_path.read_bytes()).hexdigest(),
         'coordinate_map_sha256':sha256(coord_path.read_bytes()).hexdigest(),
         'cells':cells}
    (HERE/'exceptional_result.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')


if __name__=='__main__':main()
