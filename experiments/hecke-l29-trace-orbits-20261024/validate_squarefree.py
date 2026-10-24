"""Independent replay of every squarefree fiber and its exact-rank effect."""
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import sys
from sage.all import EllipticCurve, GF, ZZ, PolynomialRing, classical_modular_polynomial, matrix

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
sys.path.insert(0,str(ROOT/'hecke-two-sheet-small-order-20261023/tools'))
import hecke11 as H
def sha(p):return sha256(p.read_bytes()).hexdigest()
def key(P):return [-1,-1] if P.is_zero() else [int(P[0]),int(P[1])]

def main():
    protocol=json.loads((HERE/'squarefree_validation_protocol.json').read_text())
    assert protocol['status']=='FROZEN_BEFORE_SQUAREFREE_VALIDATION'
    paths={'functions':ROOT/'hecke-degree-next-screen-20261024/l29_functions.json',
           'traces':HERE/'squarefree_result.json','rank':HERE/'squarefree_rank_result.json',
           'frontier':ROOT/'hecke-torsion-frontiers-20261024/p20023.result.json',
           'seed':ROOT/'hecke-torsion-frontiers-20261024/p20023.seed.result.json',
           'sign':ROOT/'hecke-sign-closure-20261024/result.json',
           'l23':ROOT/'hecke-l23-targeted-20261024/result.v2.json',
           'l29':ROOT/'hecke-degree-next-screen-20261024/l29_result.json'}
    data={k:json.loads(v.read_text()) for k,v in paths.items()}
    F=GF(20023);R=PolynomialRing(F,'z');z=R.gen()
    funcs={}
    for tag,coeff in data['functions']['functions'].items():
        ell,part,k=tag.split(':')
        funcs[(int(ell),part,int(k))]={tuple(map(int,ab.split(','))):F(v) for ab,v in coeff.items()}
    _,jfun=H.build([2,3]);rd=H.Reduced(20023,funcs,jfun,[29])
    phi=classical_modular_polynomial(29)
    T=rd.E([5,5,1]);assert 5*T==rd.E(0) and rd.a_l[29]==0
    def point(a):return rd.E(0) if a==[-1,-1] else rd.E([*a,1])
    def orbit(P):return min(tuple(key(P+k*T)) for k in range(5))

    # Separate integer affine group law for all rational trace-point sums.
    p=20023
    def decode(a):return None if a==[-1,-1] else tuple(a)
    def on(Q):
        if Q is None:return True
        x,y=Q;return (y*y+y-x*x*x+x*x+10*x+20)%p==0
    def add(A,B):
        if A is None:return B
        if B is None:return A
        x1,y1=A;x2,y2=B
        if x1==x2 and (y1+y2+1)%p==0:return None
        if A==B:s=((3*x1*x1-2*x1-10)*pow((2*y1+1)%p,-1,p))%p
        else:s=((y2-y1)*pow((x2-x1)%p,-1,p))%p
        c=(y1-s*x1)%p;x=(s*s+1-x1-x2)%p;y=(-s*x-c-1)%p
        Q=(x,y);assert on(Q);return Q

    confirmed=[]
    for record in data['traces']['sources']:
        P=point(record['source']);jP=rd.j(P)
        f=R(record['x_polynomial_coefficients']);h=R(record['y_polynomial_coefficients'])
        assert f==R(rd.neighbour_x(29,P)) and f.degree()==30 and f.is_squarefree()
        assert (h*h+h-z**3+z**2+10*z+20)%f==0
        product=R(1);momx=[F(0)]*31;momy=[F(0)]*30
        integer_total=None;rd_total=rd.E(0)
        for part in record['factor_traces']:
            g=R(part['factor_coefficients']);d=int(part['factor_degree'])
            assert g.degree()==d and g.is_irreducible()
            product*=g
            if d==1:
                K=F;alpha=-g[0];beta=h(alpha)
                E=rd.E
            else:
                K=GF(p**d,'beta_root',modulus=g)
                alpha=K.gen();beta=h(alpha)
                E=EllipticCurve(K,H.AINV)
            Q=E(alpha,beta)
            A,j0,_=jfun
            # Evaluate the saved reduced j map in the extension field.
            jQ=rd.A(alpha,beta)/(alpha-rd.x0)**11
            assert phi(F(jP),jQ)==0
            conj=[(alpha**(p**i),beta**(p**i)) for i in range(d)]
            for k in range(31):
                mx=sum(a**k for a,_ in conj)
                assert mx**p==mx
                momx[k]+=F(mx)
                if k<30:
                    my=sum(b*a**k for a,b in conj)
                    assert my**p==my
                    momy[k]+=F(my)
            group_trace=E(0)
            for a,b in conj:group_trace+=E(a,b)
            if group_trace.is_zero():rational=rd.E(0)
            else:
                assert group_trace[0]**p==group_trace[0] and group_trace[1]**p==group_trace[1]
                rational=rd.E([F(group_trace[0]),F(group_trace[1]),F(1)])
            assert key(rational)==part['trace']
            rd_total+=rational
            a=decode(part['trace']);assert on(a)
            integer_total=add(integer_total,a)
        assert product==f
        assert momx[0]==30
        assert all(momx[k]==rd.funcs[(29,'x',k)](P[0],P[1]) for k in range(1,31))
        assert all(momy[k]==rd.funcs[(29,'xy',k)](P[0],P[1]) for k in range(30))
        assert rd_total==rd.E(0) and integer_total is None
        confirmed.append(record['source'])
    assert len(confirmed)==34

    old=[tuple(x) for x in data['frontier']['column_representatives']]
    l23=[tuple(x) for x in data['l23']['all_column_representatives']]
    l29=[tuple(x) for x in data['l29']['all_column_representatives']]
    reps=set(l29)
    for record in data['traces']['sources']:
        reps.update(orbit(point(part['trace'])) for part in record['factor_traces'])
    keys=sorted(reps);idx={a:i for i,a in enumerate(keys)}
    assert [list(a) for a in sorted(reps-set(l29))]==data['rank']['additional_representatives']
    def remap(row,oldreps):return {str(idx[oldreps[int(j)]]):v for j,v in row.items()}
    rows=[remap(r['coefficients'],old) for r in data['seed']['accepted_rows']]
    rows += [remap(r,old) for r in data['frontier']['rows']]
    rows += [remap(r['coefficients'],old) for r in data['sign']['sign_rows']]
    rows += [remap(r['coefficients'],l23) for r in data['l23']['accepted_rows']]
    rows += [remap(r['coefficients'],l29) for r in data['l29']['accepted_rows']]
    trace_rows=[]
    for record in data['traces']['sources']:
        c=Counter(idx[orbit(point(part['trace']))] for part in record['factor_traces'])
        trace_rows.append({'source':record['source'],'coefficients':{str(i):v for i,v in c.items()}})
    assert trace_rows==data['rank']['trace_rows']
    rows += [r['coefficients'] for r in trace_rows]
    anchor=idx[orbit(point([1,8630]))]
    entries={(i,int(j)):v for i,row in enumerate(rows) for j,v in row.items()}
    entries[(len(rows),anchor)]=1
    M=matrix(ZZ,len(rows)+1,len(keys),entries,sparse=False)
    old_idx={idx[a] for a in old};new_idx=sorted(set(range(len(keys)))-old_idx)
    rank=int(M.rank());projection=int(M.matrix_from_columns(new_idx).rank())
    assert rank==data['rank']['exact_integer']['rank']
    assert projection==data['rank']['exact_integer']['new_column_projection_rank']
    assert rank-projection==data['rank']['exact_integer']['induced_old_rank']
    extension_count=sum(sum(t['factor_degree']>1 for t in row['factor_traces'])
                        for row in data['traces']['sources'])
    rational_count=sum(sum(t['factor_degree']==1 for t in row['factor_traces'])
                       for row in data['traces']['sources'])
    result={'status':'PASS_SQUAREFREE_TRACE_AND_EXACT_RANK_REPLAY','sources_checked':len(confirmed),
            'extension_orbits_checked':extension_count,'rational_orbits_checked':rational_count,
            'exact_integer_rank':rank,'new_column_projection_rank':projection,
            'induced_old_rank':rank-projection,
            'source_sha256':{k:sha(v) for k,v in paths.items()}}
    (HERE/'squarefree_validation.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:result[k] for k in ('status','sources_checked','exact_integer_rank','induced_old_rank')},sort_keys=True))

if __name__=='__main__':main()
