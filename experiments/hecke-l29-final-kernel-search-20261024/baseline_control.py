"""Test generator-shift closure before any higher-degree or trace rows."""
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
from sage.all import EllipticCurve, GF, ZZ, matrix, vector

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
def sha(p):return sha256(p.read_bytes()).hexdigest()
def key(P):return (-1,-1) if P.is_zero() else (int(P[0]),int(P[1]))

def main():
    path=HERE/'control_protocol.json';raw=path.read_bytes()
    protocol=json.loads(raw);assert protocol['status']=='FROZEN_BEFORE_EARLIER_TABLE_CONTROL'
    paths={'frontier':ROOT/'hecke-torsion-frontiers-20261024/p20023.result.json',
           'seed':ROOT/'hecke-torsion-frontiers-20261024/p20023.seed.result.json',
           'sign':ROOT/'hecke-sign-closure-20261024/result.json'}
    data={k:json.loads(v.read_text()) for k,v in paths.items()}
    keys=[tuple(x) for x in data['frontier']['column_representatives']]
    assert len(keys)==3949
    E=EllipticCurve(GF(20023),[0,-1,1,-10,-20]);O=E(0);T=E([5,5,1])
    def point(a):return O if a==(-1,-1) else E([*a,1])
    def orbit(P):return min(key(P+k*T) for k in range(5))
    A=point((1,8630));G=5*A;assert 4021*G==O
    idx={a:i for i,a in enumerate(keys)};anchor=idx[orbit(A)]
    projected={}
    for i,rep in enumerate(keys):
        Q=5*point(rep)
        assert key(Q) not in projected
        projected[key(Q)]=i
    base=[r['coefficients'] for r in data['seed']['accepted_rows']]+data['frontier']['rows']
    sign=[r['coefficients'] for r in data['sign']['sign_rows']]
    def build(rows,ring):
        entries={(i,int(j)):v for i,row in enumerate(rows) for j,v in row.items()}
        entries[(len(rows),anchor)]=1
        return matrix(ring,len(rows)+1,len(keys),entries,sparse=False)
    results={}
    for name,rows in [('seed_plus_degree2_3_hecke',base),
                      ('seed_plus_degree2_3_hecke_plus_inversion',base+sign)]:
        M=build(rows,GF(4021));K=M.right_kernel()
        basis=K.basis();dim=len(basis)
        assert int(M.rank())+dim==len(keys)
        support=sorted(set().union(*(set(v.support()) for v in basis)))
        attempts=[];chosen=[];evals=[]
        for i in support:
            Q=5*point(keys[i])
            for offset in (1,2):
                shifted=Q+offset*G
                hit=projected.get(key(shifted))
                record={'source_column':i,'source_projected':key(Q),
                        'offset':offset,'shifted_point':key(shifted),'hit_column':hit}
                if hit is None:
                    record['status']='MISSING';attempts.append(record);continue
                if any(b[hit]!=0 for b in basis):
                    record['status']='HIT_KERNEL_SUPPORT';attempts.append(record);continue
                assert 5*point(keys[hit])==shifted
                coeff=Counter({i:1,anchor:offset});coeff[hit]-=1
                ev=[sum(GF(4021)(v)*b[j] for j,v in coeff.items()) for b in basis]
                assert ev==[b[i] for b in basis]
                if matrix(GF(4021),evals+[ev]).rank()>len(evals):
                    record['status']='SELECTED_INDEPENDENT'
                    record['coefficients']={str(j):v for j,v in coeff.items() if v}
                    chosen.append(record);evals.append(ev)
                else:record['status']='DEPENDENT'
                attempts.append(record);break
            if len(chosen)==dim:break
        assert len(chosen)==dim, (name,dim,len(chosen))
        augmented=build(rows+[r['coefficients'] for r in chosen],GF(4021))
        assert augmented.rank()==len(keys)
        integer=build(rows+[r['coefficients'] for r in chosen],ZZ)
        assert integer.rank()==len(keys)
        rhs=vector(GF(4021),[0]*(len(rows)+len(chosen))+[1])
        logs=augmented.solve_right(rhs);assert augmented*logs==rhs
        for j,rep in enumerate(keys):assert int(logs[j])*G==5*point(rep)
        results[name]={'baseline_rank':int(M.rank()),'baseline_nullity':dim,
                       'kernel_support_columns':support,'attempts':attempts,
                       'selected_rows':chosen,'shift_augmented_rank':int(augmented.rank()),
                       'exact_integer_rank':int(integer.rank()),
                       'logs_by_column':[int(v) for v in logs],
                       'generic_seed_logs':0}
        print(json.dumps({'stage':name,'baseline_rank':int(M.rank()),
                          'baseline_nullity':dim,'selected_shifts':len(chosen),
                          'full_rank':int(augmented.rank())},sort_keys=True),flush=True)
    out={'status':'EARLIER_TABLE_TRANSLATION_CONTROL_PRODUCED',
         'protocol_sha256':sha(path),'source_sha256':{k:sha(v) for k,v in paths.items()},
         'column_representatives':keys,'results':results,'candidate_id':None,'timing_claim':None}
    (HERE/'control_result.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')

if __name__=='__main__':main()
