"""Independent degree-29 point arithmetic and integer-rank replay."""
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import sys
from sage.all import GF, ZZ, classical_modular_polynomial, matrix

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
sys.path.insert(0,str(ROOT/'hecke-two-sheet-small-order-20261023/tools'))
import hecke11 as H

def sha(path):return sha256(path.read_bytes()).hexdigest()
def key(P):return (-1,-1) if P.is_zero() else (int(P[0]),int(P[1]))

def main():
    protocol=json.loads((HERE/'l29_validation_protocol.json').read_text())
    assert protocol['status']=='FROZEN_BEFORE_L29_VALIDATION'
    paths={'validator':HERE/'validate_l29.py','result':HERE/'l29_result.json',
           'functions':HERE/'l29_functions.json',
           'frontier':ROOT/'hecke-torsion-frontiers-20261024/p20023.result.json',
           'seed':ROOT/'hecke-torsion-frontiers-20261024/p20023.seed.result.json',
           'sign':ROOT/'hecke-sign-closure-20261024/result.json',
           'l23':ROOT/'hecke-l23-targeted-20261024/result.v2.json',
           'hecke11':ROOT/'hecke-two-sheet-small-order-20261023/tools/hecke11.py'}
    assert protocol['source_sha256']=={name:sha(p) for name,p in paths.items()}
    data=json.loads(paths['result'].read_text())
    saved=json.loads(paths['functions'].read_text())
    F=GF(20023);funcs={}
    for tag,coeff in saved['functions'].items():
        ell,part,k=tag.split(':')
        funcs[(int(ell),part,int(k))]={tuple(map(int,ab.split(','))):F(v) for ab,v in coeff.items()}
    _,jfun=H.build([2,3]);rd=H.Reduced(20023,funcs,jfun,[29])
    T=rd.E([5,5,1]);assert 5*T==rd.E(0) and rd.a_l[29]==0
    def point(a):return rd.E(0) if tuple(a)==(-1,-1) else rd.E([a[0],a[1],1])
    def orbit(P):return min(key(P+k*T) for k in range(5))
    keys=[tuple(x) for x in data['all_column_representatives']]
    idx={a:i for i,a in enumerate(keys)}
    phi=classical_modular_polynomial(29)
    assert len(data['attempts'])==2 and len(data['accepted_rows'])==2
    for attempt,row in zip(data['attempts'],data['accepted_rows']):
        assert attempt['status']=='ACCEPTED' and attempt['source']==row['source']
        P=point(row['source']);j=rd.j(P)
        assert int(j)==row['j'] and int(j)==attempt['j']
        roots=rd.neighbour_x(29,P).roots()
        assert sum(int(m) for _,m in roots)==attempt['rational_x_root_multiplicity']==30
        neighbors=rd.neighbours_all(29,P)
        assert neighbors is not None and len(neighbors)==30
        assert [key(Q) for Q in neighbors]==[tuple(x) for x in row['neighbors']]
        assert all(phi(j,rd.j(Q))==0 for Q in neighbors)
        assert sum(neighbors,rd.E(0))==rd.E(0)
        coeff=Counter(idx[orbit(Q)] for Q in neighbors)
        assert {str(i):v for i,v in coeff.items() if v}==row['coefficients']

    # Separate integer affine group law, independent of Sage point addition.
    prime=20023
    def decode(a):return None if tuple(a)==(-1,-1) else tuple(a)
    def on(Q):
        if Q is None:return True
        x,y=Q;return (y*y+y-x*x*x+x*x+10*x+20)%prime==0
    def neg(Q):return None if Q is None else (Q[0],(-Q[1]-1)%prime)
    def add(A,B):
        if A is None:return B
        if B is None:return A
        x1,y1=A;x2,y2=B
        if x1==x2 and (y1+y2+1)%prime==0:return None
        if A==B:s=((3*x1*x1-2*x1-10)*pow((2*y1+1)%prime,-1,prime))%prime
        else:s=((y2-y1)*pow((x2-x1)%prime,-1,prime))%prime
        c=(y1-s*x1)%prime;x=(s*s+1-x1-x2)%prime;y=(-s*x-c-1)%prime
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
        return min((-1,-1) if add(Q,mul(k,torsion)) is None else add(Q,mul(k,torsion))
                   for k in range(5))
    for row in data['accepted_rows']:
        neighbors=[decode(x) for x in row['neighbors']]
        assert len(neighbors)==30 and all(on(Q) for Q in neighbors)
        total=None
        for Q in neighbors:total=add(total,Q)
        assert total is None
        coeff=Counter(idx[orbit_int(Q)] for Q in neighbors)
        assert {str(i):v for i,v in coeff.items() if v}==row['coefficients']

    frontier=json.loads(paths['frontier'].read_text())
    seed=json.loads(paths['seed'].read_text())
    sign=json.loads(paths['sign'].read_text())
    l23=json.loads(paths['l23'].read_text())
    old=[tuple(x) for x in frontier['column_representatives']]
    old_rows=[r['coefficients'] for r in seed['accepted_rows']]+frontier['rows']
    def remap(row,reps):return {str(idx[reps[int(j)]]):v for j,v in row.items()}
    l23reps=[tuple(x) for x in l23['all_column_representatives']]
    l23rows=[remap(r['coefficients'],l23reps) for r in l23['accepted_rows']]
    l29rows=[r['coefficients'] for r in data['accepted_rows']]
    old_cols={idx[a] for a in old};new_cols=sorted(set(range(len(keys)))-old_cols)
    anchor=idx[orbit(point((1,8630)))]
    diagnostics={}
    for name,base in [('hecke',old_rows),
                      ('hecke_sign',old_rows+[r['coefficients'] for r in sign['sign_rows']])]:
        rows=[remap(r,old) for r in base]+l23rows+l29rows
        entries={(i,int(j)):v for i,row in enumerate(rows) for j,v in row.items()}
        entries[(len(rows),anchor)]=1
        M=matrix(ZZ,len(rows)+1,len(keys),entries,sparse=False)
        full=int(M.rank());projection=int(M.matrix_from_columns(new_cols).rank())
        observed=data['rank_diagnostics'][name]
        assert full==observed['after_rank']
        assert projection==observed['new_column_projection_rank']
        assert full-projection==observed['induced_old_rank']
        diagnostics[name]={'exact_integer_rank':full,'new_column_projection_rank':projection,
                           'induced_old_rank':full-projection}
    out={'status':'PASS_L29_POINT_AND_EXACT_RANK_REPLAY',
         'source_points_checked':2,'accepted_rows':2,
         'neighbors_replayed':60,'rank':diagnostics,
         'source_sha256':{name:sha(p) for name,p in paths.items()}}
    (HERE/'l29_validation.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps(out,sort_keys=True))

if __name__=='__main__':main()
