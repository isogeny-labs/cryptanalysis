"""Independent source-status, point-sum, and rank replay for the degree-13 sweep."""
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import sys

from sage.all import EllipticCurve_from_j, GF, ZZ, classical_modular_polynomial, matrix

HERE=Path(__file__).resolve().parent
PRIOR=HERE.parent/'hecke-torsion-frontiers-20261024'
MODULE=HERE.parent/'hecke-two-sheet-small-order-20261023/tools/hecke11.py'
sys.path.insert(0,str(MODULE.parent));sys.path.insert(0,str(HERE))
import hecke11 as H
from modular_hecke import build_mod

def sha(path):return sha256(path.read_bytes()).hexdigest()
def key(P):return (-1,-1) if P.is_zero() else (int(P[0]),int(P[1]))

def main():
    protocol=json.loads((HERE/'validation_protocol.json').read_text())
    assert protocol['status']=='FROZEN_BEFORE_L13_VALIDATOR'
    sources={'validator':HERE/'validate.py','result':HERE/'result.json',
             'functions':HERE/'functions.json','modular_hecke':HERE/'modular_hecke.py',
             'frontier':PRIOR/'p20023.result.json','seed':PRIOR/'p20023.seed.result.json'}
    assert protocol['source_sha256']=={name:sha(path) for name,path in sources.items()}
    data=json.loads(sources['result'].read_text());prior=json.loads(sources['frontier'].read_text())
    seed=json.loads(sources['seed'].read_text())
    funcs,metadata=build_mod(13,20023,H)
    saved_functions=json.loads(sources['functions'].read_text())
    encoded={f'{l}:{part}:{k}':{f'{a},{b}':int(c) for (a,b),c in f.items()}
             for (l,part,k),f in funcs.items()}
    assert saved_functions=={'functions':encoded,'metadata':metadata}
    _,jfun=H.build([2,3]);rd=H.Reduced(20023,funcs,jfun,[13]);T=rd.E([5,5,1])
    assert 5*T==rd.E(0) and rd.a_l[13]==4
    old_keys=[tuple(x) for x in prior['column_representatives']]
    keys=[tuple(x) for x in data['all_column_representatives']];idx={a:i for i,a in enumerate(keys)}
    def point(a):return rd.E(0) if tuple(a)==(-1,-1) else rd.E([a[0],a[1],1])
    def orbit(P):return min(key(P+k*T) for k in range(5))
    expected={tuple(a['source']):a for a in data['attempts']}
    assert len(expected)==len(data['attempts'])==19745
    status=Counter();roots_hist=Counter();trace_cache={};eligible=0
    for rep in old_keys:
        P0=point(rep)
        for k in range(5):
            P=P0+k*T;j=rd.j(P);saved=expected[key(P)]
            if j is None:
                assert saved['status']=='SOURCE_UNDEFINED_J';status['SOURCE_UNDEFINED_J']+=1
                continue
            jj=int(j)
            if jj not in trace_cache:trace_cache[jj]=abs(int(EllipticCurve_from_j(j).trace_of_frobenius()))
            t=trace_cache[jj];assert saved['abs_trace']==t
            if jj not in (0,1728%20023) and t%13 not in (5,8):
                assert saved['status']=='TRACE_OBSTRUCTION';status['TRACE_OBSTRUCTION']+=1
                continue
            eligible+=1
            multiplicity=sum(int(m) for _,m in rd.neighbour_x(13,P).roots())
            roots_hist[multiplicity]+=1
            if multiplicity<14:
                assert saved['status']=='NOT_ALL_RATIONAL'
                assert saved['rational_root_multiplicity']==multiplicity
                status['NOT_ALL_RATIONAL']+=1
            else:
                assert saved['status']=='ACCEPTED' and multiplicity==14
                status['ACCEPTED']+=1
    assert dict(status)==data['status_counts'] and eligible==data['eligible_source_count']==3192
    p=20023
    def decode(x):return None if tuple(x)==(-1,-1) else tuple(x)
    def on(Q):
        if Q is None:return True
        x,y=Q;return (y*y+y-x*x*x+x*x+10*x+20)%p==0
    def neg(Q):return None if Q is None else (Q[0],(-Q[1]-1)%p)
    def add(A,B):
        if A is None:return B
        if B is None:return A
        x1,y1=A;x2,y2=B
        if x1==x2 and (y1+y2+1)%p==0:return None
        if A==B:s=((3*x1*x1-2*x1-10)*pow((2*y1+1)%p,-1,p))%p
        else:s=((y2-y1)*pow((x2-x1)%p,-1,p))%p
        c=(y1-s*x1)%p;x=(s*s+1-x1-x2)%p;y=(-s*x-c-1)%p
        R=(x,y);assert on(R);return R
    def mul(k,Q):
        if k<0:return mul(-k,neg(Q))
        R=None
        while k:
            if k&1:R=add(R,Q)
            Q=add(Q,Q);k>>=1
        return R
    torsion=(5,5)
    def orbit_int(Q):return min((-1,-1) if add(Q,mul(k,torsion)) is None else add(Q,mul(k,torsion)) for k in range(5))
    phi=classical_modular_polynomial(13)
    touched=set();new=set()
    for row in data['accepted_rows']:
        P=decode(row['source']);neighbors=[decode(Q) for Q in row['neighbors']]
        assert on(P) and len(neighbors)==14 and all(on(Q) for Q in neighbors)
        total=None
        for Q in neighbors:total=add(total,Q)
        assert total==mul(4,P)
        coeff=Counter(idx[orbit_int(Q)] for Q in neighbors)
        coeff[idx[orbit_int(P)]]-=4
        assert {str(j):v for j,v in coeff.items() if v}==row['coefficients']
        jP=rd.j(point(row['source']))
        assert all(phi(jP,rd.j(point(Q)))==0 for Q in row['neighbors'])
        touched.update(keys[j] for j,v in coeff.items() if v)
        new.update({keys[j] for j,v in coeff.items() if v}-set(old_keys))
    assert sorted(new)==[tuple(x) for x in data['new_representatives']]
    bad={old_keys[i] for i in data['baseline_ambiguous_old_indices']}
    assert not (touched&bad)
    old_rows=[r['coefficients'] for r in seed['accepted_rows']]+prior['rows']
    remap=lambda row:{str(idx[old_keys[int(j)]]):v for j,v in row.items()}
    rows=[remap(row) for row in old_rows]+[row['coefficients'] for row in data['accepted_rows']]
    entries={(i,int(j)):v for i,row in enumerate(rows) for j,v in row.items()}
    M=matrix(ZZ,len(rows),len(keys),entries,sparse=False)
    full_exact=int(M.rank())
    discard=[i for i,a in enumerate(keys) if a not in set(old_keys)]
    new_exact=int(M.matrix_from_columns(discard).rank()) if discard else 0
    assert full_exact-new_exact==3943
    out={'status':'PASS_L13_COMPLETE_STATUS_AND_INTEGER_POINT_REPLAY',
         'protocol_sha256':sha(HERE/'validation_protocol.json'),
         'result_sha256':sha(HERE/'result.json'),'validator_sha256':sha(HERE/'validate.py'),
         'sources_checked':len(expected),'eligible_sources_checked':eligible,
         'status_counts':dict(status),'rational_root_multiplicity_histogram':dict(roots_hist),
         'accepted_rows_replayed':len(data['accepted_rows']),
         'new_columns_checked':len(new),'touched_ambiguous_old_columns':len(touched&bad),
         'exact_full_rank':full_exact,'exact_new_projection_rank':new_exact,
         'exact_induced_old_rank':full_exact-new_exact}
    (HERE/'validation.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps(out,sort_keys=True))

if __name__=='__main__':main()
