"""Independent Eichler-Shimura point count and rational-cusp audit."""
import json
from math import gcd
from pathlib import Path

from sage.all import CuspForms, divisors, euler_phi

HERE=Path(__file__).resolve().parent


def main():
    p,N=883,432
    census=json.loads((HERE/'full_chain_census.json').read_text())
    S=CuspForms(N,2)
    genus=int(S.dimension())
    hecke_trace=int(S.hecke_operator(p).trace())
    geometric_cusps=0
    rational_cusps=0
    cusp_rows=[]
    for d in divisors(N):
        h=gcd(int(d),N//int(d))
        count=int(euler_phi(h))
        fixed=(p-1)%h==0
        geometric_cusps+=count
        rational_cusps+=count if fixed else 0
        cusp_rows.append({'denominator':int(d),'gcd':h,
                          'geometric_count':count,'F883_fixed':fixed})
    total=p+1-hecke_trace
    noncuspidal=total-rational_cusps
    assert genus==55 and hecke_trace==-4 and total==888
    assert geometric_cusps==36 and rational_cusps==24
    assert noncuspidal==census['paired_chains_total_raw']==864
    B_count=931
    out={'status':'PASS_INDEPENDENT_X0_432_POINT_COUNT',
         'level':N,'prime':p,'genus':genus,
         'hecke_Tp_trace':hecke_trace,
         'X0_Fp_points':total,
         'geometric_cusps':geometric_cusps,
         'Fp_rational_cusps':rational_cusps,
         'noncuspidal_points':noncuspidal,
         'stable_chain_pairs':census['paired_chains_total_raw'],
         'B_Fp_points':B_count,
         'minimum_B_points_without_Fp_rational_X0_preimage':B_count-total,
         'cusp_rows':cusp_rows}
    (HERE/'point_count_validation.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
    print(json.dumps({k:out[k] for k in ('status','genus','hecke_Tp_trace',
          'X0_Fp_points','Fp_rational_cusps','noncuspidal_points',
          'minimum_B_points_without_Fp_rational_X0_preimage')},sort_keys=True))


if __name__=='__main__':
    main()
