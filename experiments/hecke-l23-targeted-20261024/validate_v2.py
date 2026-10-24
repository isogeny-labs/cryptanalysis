"""Independent six-source degree-23 point and induced-rank audit."""
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import sys
from sage.all import GF, ZZ, classical_modular_polynomial, matrix

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
PRIOR=ROOT/'hecke-torsion-frontiers-20261024'
SCREEN=ROOT/'hecke-higher-degree-screen-20261024'
SIGN=ROOT/'hecke-sign-closure-20261024'
MODULE=ROOT/'hecke-two-sheet-small-order-20261023/tools/hecke11.py'
sys.path.insert(0,str(MODULE.parent))
import hecke11 as H
def sha(path):return sha256(path.read_bytes()).hexdigest()
def key(P):return (-1,-1) if P.is_zero() else (int(P[0]),int(P[1]))

def main():
    protocol=json.loads((HERE/'validation_protocol.v2.json').read_text())
    assert protocol['status']=='FROZEN_BEFORE_L23_VALIDATOR'
    sources={'validator':HERE/'validate_v2.py','result':HERE/'result.v2.json',
             'functions':HERE/'functions.v2.json','screen':SCREEN/'result.json',
             'frontier':PRIOR/'p20023.result.json','seed':PRIOR/'p20023.seed.result.json',
             'sign':SIGN/'result.json','hecke11':MODULE}
    assert protocol['source_sha256']=={name:sha(path) for name,path in sources.items()}
    data=json.loads(sources['result'].read_text());saved=json.loads(sources['functions'].read_text())
    F=GF(20023);funcs={}
    for tag,coeff in saved['functions'].items():
        l,part,k=tag.split(':')
        funcs[(int(l),part,int(k))]={tuple(map(int,ab.split(','))):F(v) for ab,v in coeff.items()}
    _,jfun=H.build([2,3]);rd=H.Reduced(20023,funcs,jfun,[23]);T=rd.E([5,5,1])
    assert rd.a_l[23]==-1 and 5*T==rd.E(0)
    def point(a):return rd.E(0) if tuple(a)==(-1,-1) else rd.E([a[0],a[1],1])
    def orbit(P):return min(key(P+k*T) for k in range(5))
    keys=[tuple(x) for x in data['all_column_representatives']];idx={a:i for i,a in enumerate(keys)}
    attempts={tuple(a['source']):a for a in data['attempts']}
    assert len(attempts)==6
    accepted=data['accepted_rows'];statuses=Counter();phi=classical_modular_polynomial(23)
    for rep in data['source_points']:
        P=point(rep);record=attempts[tuple(rep)]
        j=rd.j(P);assert j is not None and record['j']==int(j)
        roots=rd.neighbour_x(23,P).roots()
        m=sum(int(v) for _,v in roots)
        assert m==record['rational_x_root_multiplicity']
        if m<24:assert record['status']=='NOT_ALL_RATIONAL_X'
        elif record['status']=='ACCEPTED':
            saved_row=accepted[record['row_index']]
            nb=rd.neighbours_all(23,P)
            assert nb is not None and [key(Q) for Q in nb]==[tuple(x) for x in saved_row['neighbors']]
            assert sum(nb,rd.E(0))==-P
            assert all(phi(j,rd.j(Q))==0 for Q in nb)
            coeff=Counter(idx[orbit(Q)] for Q in nb);coeff[idx[orbit(P)]]+=1
            assert {str(i):v for i,v in coeff.items() if v}==saved_row['coefficients']
        else:assert record['status'] in ('UNRESOLVED_NEIGHBOURS','CUSP_NEIGHBOUR')
        statuses[record['status']]+=1
    assert dict(statuses)==data['status_counts']
    p=20023
    def decode(a):return None if tuple(a)==(-1,-1) else tuple(a)
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
        Q=(x,y);assert on(Q);return Q
    def mul(k,Q):
        if k<0:return mul(-k,neg(Q))
        R=None
        while k:
            if k&1:R=add(R,Q)
            Q=add(Q,Q);k>>=1
        return R
    torsion=(5,5);assert mul(5,torsion) is None
    def orbit_int(Q):
        return min((-1,-1) if add(Q,mul(k,torsion)) is None
                   else add(Q,mul(k,torsion)) for k in range(5))
    for row in accepted:
        P=decode(row['source']);neighbors=[decode(Q) for Q in row['neighbors']]
        assert on(P) and len(neighbors)==24 and all(on(Q) for Q in neighbors)
        total=None
        for Q in neighbors:total=add(total,Q)
        assert total==neg(P)
        coeff=Counter(idx[orbit_int(Q)] for Q in neighbors)
        coeff[idx[orbit_int(P)]]+=1
        assert {str(i):v for i,v in coeff.items() if v}==row['coefficients']
    prior=json.loads(sources['frontier'].read_text());seed=json.loads(sources['seed'].read_text())
    sign=json.loads(sources['sign'].read_text());old=[tuple(x) for x in prior['column_representatives']]
    old_rows=[r['coefficients'] for r in seed['accepted_rows']]+prior['rows']
    def remap(row):return {str(idx[old[int(j)]]):v for j,v in row.items()}
    new_rows=[r['coefficients'] for r in accepted]
    old_cols={idx[a] for a in old};discard=sorted(set(range(len(keys)))-old_cols)
    ranks={}
    for name,base in [('hecke',old_rows),('hecke_sign',old_rows+[r['coefficients'] for r in sign['sign_rows']])]:
        rows=[remap(row) for row in base]+new_rows
        entries={(i,int(j)):v for i,row in enumerate(rows) for j,v in row.items()}
        anchor=idx[orbit(point((1,8630)))];entries[(len(rows),anchor)]=1
        M=matrix(ZZ,len(rows)+1,len(keys),entries,sparse=False)
        full=int(M.rank());projection=int(M.matrix_from_columns(discard).rank()) if discard else 0
        ranks[name]={'full_rank':full,'new_projection_rank':projection,
                     'induced_old_rank':full-projection}
        assert full-projection==data['rank_diagnostics'][name]['combined_induced_old_rank']
    out={'status':'PASS_L23_TARGETED_POINT_AND_EXACT_RANK_REPLAY',
         'protocol_sha256':sha(HERE/'validation_protocol.v2.json'),
         'result_sha256':sha(HERE/'result.v2.json'),'validator_sha256':sha(HERE/'validate_v2.py'),
         'sources_checked':6,'status_counts':dict(statuses),
         'accepted_rows_replayed':len(accepted),'exact_rank_results':ranks}
    (HERE/'validation.v2.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
    print(json.dumps(out,sort_keys=True))

if __name__=='__main__':main()
