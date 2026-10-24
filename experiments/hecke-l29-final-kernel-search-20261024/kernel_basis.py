"""Rebuild the exact saved relation matrix and extract its residual kernel."""
from hashlib import sha256
import json
from pathlib import Path
from sage.all import EllipticCurve, GF, matrix

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
def sha(p):return sha256(p.read_bytes()).hexdigest()
def key(P):return (-1,-1) if P.is_zero() else (int(P[0]),int(P[1]))

def main():
    path=HERE/'protocol.json';raw=path.read_bytes()
    protocol=json.loads(raw);assert protocol['status']=='FROZEN_BEFORE_KERNEL_AND_SOURCE_SELECTION'
    paths={'completion':ROOT/'hecke-l29-trace-orbits-20261024/all_completion_result.json',
           'rank':ROOT/'hecke-l29-trace-orbits-20261024/all_rank_result.json',
           'frontier':ROOT/'hecke-torsion-frontiers-20261024/p20023.result.json',
           'seed':ROOT/'hecke-torsion-frontiers-20261024/p20023.seed.result.json',
           'sign':ROOT/'hecke-sign-closure-20261024/result.json',
           'l23':ROOT/'hecke-l23-targeted-20261024/result.v2.json',
           'l29':ROOT/'hecke-degree-next-screen-20261024/l29_result.json'}
    data={k:json.loads(v.read_text()) for k,v in paths.items()}
    keys=[tuple(a) for a in data['completion']['all_column_representatives']]
    old=[tuple(a) for a in data['frontier']['column_representatives']]
    l23=[tuple(a) for a in data['l23']['all_column_representatives']]
    l29=[tuple(a) for a in data['l29']['all_column_representatives']]
    assert len(keys)==3959 and len(old)==3949
    idx={a:i for i,a in enumerate(keys)}
    def remap(row,reps):return {str(idx[reps[int(j)]]):v for j,v in row.items()}
    rows=[remap(r['coefficients'],old) for r in data['seed']['accepted_rows']]
    rows += [remap(r,old) for r in data['frontier']['rows']]
    rows += [remap(r['coefficients'],old) for r in data['sign']['sign_rows']]
    rows += [remap(r['coefficients'],l23) for r in data['l23']['accepted_rows']]
    rows += [remap(r['coefficients'],l29) for r in data['l29']['accepted_rows']]
    rows += [r['coefficients'] for r in data['rank']['trace_rows']]
    E=EllipticCurve(GF(20023),[0,-1,1,-10,-20]);T=E([5,5,1])
    P=E([1,8630,1]);anchor=idx[min(key(P+k*T) for k in range(5))]
    entries={(i,int(j)):v for i,row in enumerate(rows) for j,v in row.items()}
    entries[(len(rows),anchor)]=1
    M=matrix(GF(4021),len(rows)+1,len(keys),entries,sparse=False)
    assert M.rank()==3958
    K=M.right_kernel();assert K.dimension()==1
    basis=K.basis()[0]
    # Normalise at the previously selected generic seed coordinate.
    seed_index=data['completion']['seed_log']['column_index']
    assert basis[seed_index]!=0
    basis=basis/basis[seed_index]
    assert M*basis==0
    support={str(i):int(v) for i,v in enumerate(basis) if v}
    old_support=[old.index(keys[int(i)]) for i in support if keys[int(i)] in set(old)]
    out={'status':'FINAL_KERNEL_REBUILT','protocol_sha256':sha(path),
         'source_sha256':{k:sha(v) for k,v in paths.items()},
         'column_representatives':keys,'matrix_rows':len(rows)+1,
         'rank':int(M.rank()),'nullity':int(K.dimension()),
         'normalization_column':seed_index,'kernel_support':support,
         'old_support_indices':sorted(old_support),'candidate_id':None,'timing_claim':None}
    (HERE/'kernel_result.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'rank':out['rank'],'nullity':out['nullity'],
                      'support_count':len(support),'old_support_indices':out['old_support_indices']},sort_keys=True))

if __name__=='__main__':main()
