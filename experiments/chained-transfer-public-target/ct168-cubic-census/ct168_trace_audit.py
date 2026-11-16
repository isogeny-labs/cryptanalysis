#!/usr/bin/env python3
"""CT168: independent integer trace audit. Does not sign scientific PCC."""
import json
import sys
from pathlib import Path
p=223
q=p**3

def rec(t,n=6):
    seq=[2,t]
    for _ in range(2,n+1):seq.append(t*seq[-1]-q*seq[-2])
    return seq

def strict_load(path):
    def pairs(ps):
        d={}
        for k,v in ps:
            if k in d:raise ValueError("duplicate key: "+k)
            d[k]=v
        return d
    return json.loads(Path(path).read_text(),object_pairs_hook=pairs,
        parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))

def audit(primary,secondary):
    a=strict_load(primary)
    b=strict_load(secondary)
    assert a['field_size']==q and a['x_enumerations_each']==q and a['y_square_enumerations']==q
    assert a['source_prime_order']==219 and a['d_sixth_character']==40
    for ai,bi in zip(('source_cubic','twist_cubic','mutated_twist'),b['counts']):
        ca=a[ai]
        assert type(ca['points']) is int and ca['points']==bi['n']
        assert ca['zero_rhs_x']==bi['zero']
        assert ca['nonzero_square_x']==bi['nonzero_square']
        assert 1+ca['zero_rhs_x']+2*ca['nonzero_square_x']==ca['points']
        assert ca['nonzero_square_x']+ca['zero_rhs_x']+ca['nonsquare_x']==q
    assert a['twist_cubic']['points']!=a['mutated_twist']['points']
    ts=q+1-a['source_cubic']['points']
    td=q+1-a['twist_cubic']['points']
    assert ts==-3220 and td==3439
    assert 219==3*73
    assert (q+1-ts)%73==0
    S,D=rec(ts),rec(td)
    assert all(S[r]!=D[r] for r in range(1,6))
    assert S[6]==D[6]
    assert (q+1-td)%73!=0 and (q*q+1-D[2])%73==0
    return {'schema':'ct168-minimal-isogeny-degree-v1','base_prime':p,'K_cardinality':q,
            'source_trace_K':ts,'twist_trace_K':td,
            'isogenous_extension_degrees_1_through_6':[r for r in range(1,7) if S[r]==D[r]],
            'minimal_isogeny_extension_degree_over_K':6,
            'minimal_isogeny_extension_degree_over_F223':18,
            'source_traces':S[1:], 'twist_traces':D[1:],
            'source_order73_at_K':(q+1-ts)%73==0,
            'twist_order73_at_K':(q+1-td)%73==0,
            'twist_order73_at_K2':(q*q+1-D[2])%73==0,
            'conclusion':'No nonzero K^r-defined elliptic-curve homomorphism for r=1,...,5; explicit isomorphism exists at r=6',
            'standing':'pcc:unverified'}

if __name__=='__main__':
    out=audit(sys.argv[1],sys.argv[2]);print(json.dumps(out,sort_keys=True,separators=(',',':')))
