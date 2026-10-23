"""Preflight the uniform two-sheet hypothesis for an X0(11) CM class walk.

Run through the checked repository Sage launcher. This gate is independent of
the Hecke relation producer and should precede any rank forecast that assumes
two rational X0(11) points above every order-class j-invariant.
"""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys

from sage.all import EllipticCurve_from_j, hilbert_class_polynomial, pari

P=Path(__file__).resolve().parent
sys.path.insert(0,str(P/'tools'))
import hecke11 as H

def divisors(n):
    return [d for d in range(1,n+1) if n%d==0]

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--dk',type=int,required=True)
    parser.add_argument('--f',type=int,required=True)
    parser.add_argument('--p',type=int,required=True)
    parser.add_argument('--u',type=int,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    assert args.dk<0 and args.f>0 and args.p>3
    assert args.u*args.u-4*args.p==args.dk*args.f*args.f
    funcs,jfun=H.build([2,3]);rd=H.Reduced(args.p,funcs,jfun,[2,3])
    strata={};exceptions=[]
    for conductor in divisors(args.f):
        D=args.dk*conductor*conductor
        js=hilbert_class_polynomial(D).change_ring(rd.Fp).roots(multiplicities=False)
        h=int(pari.qfbclassno(D))
        counts={};point_count=0
        for j in js:
            trace=abs(int(EllipticCurve_from_j(j).trace_of_frobenius()))
            points=rd.points_with_j(j)
            count=len(points);point_count+=count
            counts[count]=counts.get(count,0)+1
            if trace!=args.u or count!=2:
                exceptions.append({'conductor':conductor,'j':int(j),'trace_abs':trace,
                                   'rational_point_count':count,
                                   'rational_points':[str(q) for q in points]})
        if len(js)!=h:
            exceptions.append({'conductor':conductor,'reason':'class_polynomial_not_fully_split',
                               'class_number':h,'rational_j_count':len(js)})
        strata[str(conductor)]={'class_number':h,'rational_j_count':len(js),
                                 'rational_point_count':point_count,
                                 'points_per_j':{str(k):v for k,v in sorted(counts.items())}}
    result={'status':'PASS_UNIFORM_TWO_SHEET_GATE' if not exceptions else 'FAIL_UNIFORM_TWO_SHEET_GATE',
            'dk':args.dk,'f':args.f,'p':args.p,'u':args.u,'strata':strata,
            'exceptions':exceptions,
            'script_sha256':sha256((P/'fiber_gate.py').read_bytes()).hexdigest()}
    args.output.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'status':result['status'],'exceptions':len(exceptions),
                      'total_points':sum(x['rational_point_count'] for x in strata.values())}))

if __name__=='__main__':main()
