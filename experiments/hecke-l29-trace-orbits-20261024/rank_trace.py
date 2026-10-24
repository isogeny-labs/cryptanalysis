"""Insert verified Frobenius-orbit trace rows into the saved Hecke matrices."""
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import sys
from sage.all import GF, ZZ, matrix

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
sys.path.insert(0,str(ROOT/'hecke-two-sheet-small-order-20261023/tools'))
import hecke11 as H
def sha(p):return sha256(p.read_bytes()).hexdigest()
def key(P):return (-1,-1) if P.is_zero() else (int(P[0]),int(P[1]))

def main():
    path=HERE/'rank_protocol.json';raw=path.read_bytes()
    protocol=json.loads(raw);assert protocol['status']=='FROZEN_BEFORE_TRACE_RANK'
    paths={'trace':HERE/'trace_result.json',
           'frontier':ROOT/'hecke-torsion-frontiers-20261024/p20023.result.json',
           'seed':ROOT/'hecke-torsion-frontiers-20261024/p20023.seed.result.json',
           'sign':ROOT/'hecke-sign-closure-20261024/result.json',
           'l23':ROOT/'hecke-l23-targeted-20261024/result.v2.json',
           'l29':ROOT/'hecke-degree-next-screen-20261024/l29_result.json'}
    data={k:json.loads(v.read_text()) for k,v in paths.items()}
    old=[tuple(x) for x in data['frontier']['column_representatives']]
    l23=[tuple(x) for x in data['l23']['all_column_representatives']]
    keys=[tuple(x) for x in data['l29']['all_column_representatives']]
    assert len(old)==3949 and len(l23)==3953 and len(keys)==3955
    idx={a:i for i,a in enumerate(keys)}
    funcs,jfun=H.build([2,3]);rd=H.Reduced(20023,funcs,jfun,[2,3])
    T=rd.E([5,5,1]);assert 5*T==rd.E(0)
    def point(a):return rd.E(0) if tuple(a)==(-1,-1) else rd.E([*a,1])
    def orbit(P):return min(key(P+k*T) for k in range(5))
    def remap(row,reps):return {str(idx[reps[int(j)]]):v for j,v in row.items()}
    base=[remap(r['coefficients'],old) for r in data['seed']['accepted_rows']]
    base += [remap(r,old) for r in data['frontier']['rows']]
    sign=[remap(r['coefficients'],old) for r in data['sign']['sign_rows']]
    higher=[remap(r['coefficients'],l23) for r in data['l23']['accepted_rows']]
    higher += [r['coefficients'] for r in data['l29']['accepted_rows']]
    trace_rows=[]
    for record in data['trace']['sources']:
        assert record['group_sum']==[-1,-1] and len(record['factor_traces'])==6
        coeff=Counter()
        group_sum=rd.E(0)
        for part in record['factor_traces']:
            P=point(part['trace']);group_sum+=P
            rep=orbit(P);assert rep in idx
            coeff[idx[rep]]+=1
        assert group_sum==rd.E(0)
        trace_rows.append({'source':record['source'],
                           'coefficients':{str(i):v for i,v in coeff.items() if v}})
    old_cols={idx[x] for x in old}
    new_cols=sorted(set(range(len(keys)))-old_cols)
    anchor=idx[orbit(point(protocol['anchor_point']))]
    stages=[]
    for count in range(3):
        rows=base+sign+higher+[r['coefficients'] for r in trace_rows[:count]]
        entries={(i,int(j)):v for i,row in enumerate(rows) for j,v in row.items()}
        entries[(len(rows),anchor)]=1
        M=matrix(GF(4021),len(rows)+1,len(keys),entries,sparse=False)
        rank=int(M.rank());projection=int(M.matrix_from_columns(new_cols).rank())
        K=M.right_kernel()
        support=set().union(*(set(v.support()) for v in K.basis()))
        stages.append({'trace_rows_added':count,'rank':rank,
                       'new_column_projection_rank':projection,
                       'induced_old_rank':rank-projection,
                       'nullity':int(K.dimension()),
                       'ambiguous_old_indices':sorted(old.index(keys[i]) for i in support&old_cols)})
        print(json.dumps(stages[-1],sort_keys=True),flush=True)
    rows=base+sign+higher+[r['coefficients'] for r in trace_rows]
    entries={(i,int(j)):v for i,row in enumerate(rows) for j,v in row.items()}
    entries[(len(rows),anchor)]=1
    M=matrix(ZZ,len(rows)+1,len(keys),entries,sparse=False)
    exact={'rank':int(M.rank()),
           'new_column_projection_rank':int(M.matrix_from_columns(new_cols).rank())}
    exact['induced_old_rank']=exact['rank']-exact['new_column_projection_rank']
    assert exact['rank']==stages[-1]['rank']
    assert exact['induced_old_rank']==stages[-1]['induced_old_rank']
    result={'status':'L29_TRACE_RANK_PRODUCED','protocol_sha256':sha(path),
            'source_sha256':{k:sha(v) for k,v in paths.items()},
            'trace_rows':trace_rows,'stages':stages,'exact_integer':exact,
            'candidate_id':None,'timing_claim':None}
    (HERE/'rank_result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'exact_integer':exact},sort_keys=True),flush=True)

if __name__=='__main__':main()
