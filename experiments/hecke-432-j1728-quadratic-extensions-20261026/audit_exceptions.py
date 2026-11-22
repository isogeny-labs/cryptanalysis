"""Independent modular factor audit for the denominator exceptions."""
import json
from hashlib import sha256
from pathlib import Path

from sympy import Poly, Symbol, factor_list

HERE=Path(__file__).resolve().parent
X=Symbol('x')


def main():
    cp=HERE/'sqrt3_certificate.json';cert=json.loads(cp.read_text())
    ep=HERE/'exceptional_result.json';result=json.loads(ep.read_text())
    a=list(map(int,cert['field_polynomial_coefficients_low_to_high']))
    assert result['status']=='EXACT_EXCEPTIONAL_PRIME_AUDIT'
    cells=[]
    for cell in result['cells']:
        p=cell['prime'];f=Poly.from_list(list(reversed(a)),X,modulus=p)
        _,factors=factor_list(f)
        roots=[]
        for q,m in factors:
            if q.degree()!=1:continue
            b0,b1=[int(q.nth(i))%p for i in (0,1)]
            x=-b0*pow(b1,-1,p)%p
            roots.append({'x_C':x,'multiplicity':m})
        stored=[{'x_C':r['x_C'],'multiplicity':r['multiplicity']} for r in cell['x_root_details']]
        assert sorted(roots,key=lambda z:z['x_C'])==sorted(stored,key=lambda z:z['x_C'])
        for r in cell['x_root_details']:
            disc=(4*(pow(r['x_C'],3,p)-7)+1)%p
            assert disc==r['curve_discriminant']
            assert disc and pow(disc,(p-1)//2,p)==p-1
        assert not cell['source_j1728_C_points']
        cells.append({'prime':p,'linear_x_roots':len(roots),'curve_discriminants_nonsquare':True})
    out={'status':'PASS_INDEPENDENT_EXCEPTIONAL_AUDIT',
         'certificate_sha256':sha256(cp.read_bytes()).hexdigest(),
         'exceptional_result_sha256':sha256(ep.read_bytes()).hexdigest(),
         'cells':cells}
    (HERE/'exceptional_audit.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
    print(json.dumps(out,sort_keys=True))


if __name__=='__main__':main()
