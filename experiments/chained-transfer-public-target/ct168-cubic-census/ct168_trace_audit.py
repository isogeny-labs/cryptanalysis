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

def require(ok, message):
    if not ok:
        raise ValueError('CT168 validation failed: ' + message)

def exact_keys(value, keys, where):
    require(type(value) is dict, where + ' must be an object')
    require(set(value) == set(keys), where + ' has missing or extra keys')

def exact_int(value, where):
    require(type(value) is int, where + ' must be a JSON integer')
    return value

def audit(primary,secondary):
    a=strict_load(primary)
    b=strict_load(secondary)
    top=('schema','p','field_size','x_enumerations_each',
         'y_square_enumerations','source_prime_order','d_sixth_character',
         'source_cubic','twist_cubic','mutated_twist','producer_standing')
    exact_keys(a,top,'primary')
    exact_keys(b,('schema','counts'),'secondary')
    require(type(a['schema']) is str and a['schema']=='ct168-complete-census-v1','primary schema')
    require(type(b['schema']) is str and b['schema']=='ct168-generic-independent-crosscheck-v1','secondary schema')
    require(type(a['producer_standing']) is str and a['producer_standing']=='pcc:unverified','standing')
    for key,expected in [('p',p),('field_size',q),('x_enumerations_each',q),
                         ('y_square_enumerations',q),('source_prime_order',219),
                         ('d_sixth_character',40)]:
        require(exact_int(a[key],'primary '+key)==expected,'primary '+key)
    # zip() alone ignores trailing independent records: reject any missing or extra rows.
    require(type(b['counts']) is list and len(b['counts'])==3,'secondary counts length')
    for ai,bi in zip(('source_cubic','twist_cubic','mutated_twist'),b['counts']):
        ca=a[ai]
        exact_keys(ca,('points','zero_rhs_x','nonzero_square_x','nonsquare_x'),ai)
        exact_keys(bi,('n','zero','nonzero_square'),ai+' secondary')
        for key in ('points','zero_rhs_x','nonzero_square_x','nonsquare_x'):
            exact_int(ca[key],ai+' '+key)
            require(ca[key]>=0,ai+' '+key+' negative')
        for key in ('n','zero','nonzero_square'):
            exact_int(bi[key],ai+' secondary '+key)
        require(ca['points']==bi['n'],ai+' points mismatch')
        require(ca['zero_rhs_x']==bi['zero'],ai+' zero mismatch')
        require(ca['nonzero_square_x']==bi['nonzero_square'],ai+' square mismatch')
        require(1+ca['zero_rhs_x']+2*ca['nonzero_square_x']==ca['points'],ai+' point partition')
        require(ca['nonzero_square_x']+ca['zero_rhs_x']+ca['nonsquare_x']==q,ai+' x partition')
    require(a['twist_cubic']['points']!=a['mutated_twist']['points'],'negative control')
    # CT170: matching a second counter and recomputing point totals do not
    # authenticate the frozen component census. In particular a zero/square
    # tradeoff preserves #E and the Frobenius trace, and the mutant has no
    # separately checked trace. Bind every bucket to the preregistered output.
    frozen = {
        'source_cubic': (11092788, 3, 5546392, 5543172),
        'twist_cubic': (11086129, 0, 5543064, 5546503),
        'mutated_twist': (11086348, 3, 5543172, 5546392),
    }
    for name, expected in frozen.items():
        row = a[name]
        actual = (row['points'], row['zero_rhs_x'],
                  row['nonzero_square_x'], row['nonsquare_x'])
        require(actual == expected, name + ' frozen component mismatch')

    ts=q+1-a['source_cubic']['points']
    td=q+1-a['twist_cubic']['points']
    require(ts==-3220 and td==3439,'frozen trace')
    require(219==3*73 and (q+1-ts)%73==0,'source subgroup')
    S,D=rec(ts),rec(td)
    require(all(S[r]!=D[r] for r in range(1,6)),'short-field isogeny obstruction')
    require(S[6]==D[6],'extension-six equality')
    require((q+1-td)%73!=0,'twist K subgroup control')
    require((q*q+1-D[2])%73==0,'twist K2 subgroup control')
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
