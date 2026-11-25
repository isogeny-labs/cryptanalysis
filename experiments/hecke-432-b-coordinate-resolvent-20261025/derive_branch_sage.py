"""Derive an explicit rational x_B branch from the degree-12 resolvent."""
import json
from hashlib import sha256
from math import gcd
from pathlib import Path

import sage.misc.lazy_import_cache as lazy_cache
lazy_cache.DOT_SAGE = '/Volumes/SSD990/llm/tmp/hecke432sage'

from sage.all import PolynomialRing, ZZ

HERE=Path(__file__).resolve().parent


def main():
    source_path=HERE/'relative_b_resolvent.json'
    source=json.loads(source_path.read_text())
    assert source['status']=='CERTIFIED_RELATIVE_DEGREE_12_B_RESOLVENT'
    M=PolynomialRing(ZZ,names=('xC','yC','xE'))
    xC,yC,xE=M.gens()
    U=PolynomialRing(M,'T')
    T=U.gen()
    PB=sum((M(int(row['integer_coefficient']))*xC**row['x_C_exponent']*
            yC**row['y_C_exponent']*T**row['x_B_exponent']
            for row in source['terms']),U.zero())
    F=T**3-xE*T**2-64
    quotient,remainder=PB.quo_rem(F)
    assert PB==quotient*F+remainder and remainder.degree()<=2
    a,b,c=remainder[2],remainder[1],remainder[0]
    D=b*(a*xE+b)-a*c
    N=64*a*a-c*(a*xE+b)
    assert D*T-N==a*(a*F-T*remainder)+(a*xE+b)*remainder

    def canonical(poly):
        out=M.zero()
        for (i,j,k),v in poly.dict().items():
            assert j<=2
            if j==2:
                out += v*xC**(i+3)*xE**k-7*v*xC**i*xE**k-v*xC**i*yC*xE**k
            else:
                out += v*xC**i*yC**j*xE**k
        return out

    N0,D0=canonical(N),canonical(D)
    assert canonical(N-N0)==0 and canonical(D-D0)==0
    all_values=[int(v) for v in N0.dict().values()]+[int(v) for v in D0.dict().values()]
    content=gcd(*all_values)
    assert content>0
    N0=N0//content
    D0=D0//content

    def terms(poly):
        return [{'x_C_exponent':i,'y_C_exponent':j,'x_E_exponent':k,
                 'integer_coefficient':str(v)}
                for (i,j,k),v in sorted(poly.dict().items()) if v]

    out={'status':'EXPLICIT_RATIONAL_B_X_BRANCH',
         'formula':'x_B=N(x_C,y_C,x_E)/D(x_C,y_C,x_E)',
         'curve_relation':'y_C^2+y_C=x_C^3-7',
         'cubic_relation':'x_B^3-x_E*x_B^2-64=0',
         'elimination_remainder_degree':int(remainder.degree()),
         'elimination_identity':'D*T-N=a*(a*F-T*R)+(a*x_E+b)*R; R=P_B mod F',
         'primitive_content_removed':str(content),
         'numerator_terms':terms(N0),'denominator_terms':terms(D0),
         'source_sha256':sha256(source_path.read_bytes()).hexdigest()}
    (HERE/'branch_formula.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'status':out['status'],
                      'numerator_terms':len(out['numerator_terms']),
                      'denominator_terms':len(out['denominator_terms']),
                      'content':content},sort_keys=True))


if __name__=='__main__':main()
