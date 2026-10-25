"""Necessary Frobenius-eigenvalue screen for F883-rational cyclic 432-subgroups."""
import json
from math import gcd, isqrt
from pathlib import Path

HERE=Path(__file__).resolve().parent


def order_mod(a,n):
    x=1
    for k in range(1,37):
        x=(x*a)%n
        if x==1:
            return k
    raise AssertionError((a,n))


def main():
    p,N=883,432
    trace_bound=isqrt(4*p)
    assert trace_bound==59
    rows=[]
    for t in range(-trace_bound,trace_bound+1):
        eigenvalues=[a for a in range(N) if gcd(a,N)==1 and
                     (a*a-t*a+p)%N==0]
        if not eigenvalues:
            continue
        rows.append({'trace':t,'curve_order':p+1-t,
                     'eigenvalues':eigenvalues,
                     'eigenvalue_orders':[order_mod(a,N) for a in eigenvalues]})
    assert [r['trace'] for r in rows]==[-52,-20,20,52]
    out={'status':'PASS_NECESSARY_FROBENIUS_SCREEN',
         'prime':p,'level':N,'hasse_trace_interval':[-trace_bound,trace_bound],
         'admissible_traces':rows,
         'interpretation':'necessary congruence for a Frobenius-stable cyclic subgroup; not an existence certificate'}
    (HERE/'frobenius_screen.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'status':out['status'],'admissible_traces':[r['trace'] for r in rows]},sort_keys=True))


if __name__=='__main__':
    main()
