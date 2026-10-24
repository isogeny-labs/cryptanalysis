"""Measure all twelve degree-seven-factor trace rows against old-column rank."""
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
    path=HERE/'degree7_rank_protocol.json';raw=path.read_bytes()
    protocol=json.loads(raw);assert protocol['status']=='FROZEN_BEFORE_ALL_DEGREE7_RANK'
    paths={'traces':HERE/'degree7_result.json',
           'frontier':ROOT/'hecke-torsion-frontiers-20261024/p20023.result.json',
           'seed':ROOT/'hecke-torsion-frontiers-20261024/p20023.seed.result.json',
           'sign':ROOT/'hecke-sign-closure-20261024/result.json',
           'l23':ROOT/'hecke-l23-targeted-20261024/result.v2.json',
           'l29':ROOT/'hecke-degree-next-screen-20261024/l29_result.json'}
    data={k:json.loads(v.read_text()) for k,v in paths.items()}
    old=[tuple(x) for x in data['frontier']['column_representatives']]
    l23=[tuple(x) for x in data['l23']['all_column_representatives']]
    l29=[tuple(x) for x in data['l29']['all_column_representatives']]
    assert len(old)==3949 and len(l23)==3953 and len(l29)==3955
    funcs,jfun=H.build([2,3]);rd=H.Reduced(20023,funcs,jfun,[2,3])
    T=rd.E([5,5,1]);assert 5*T==rd.E(0)
    def point(a):return rd.E(0) if tuple(a)==(-1,-1) else rd.E([*a,1])
    def orbit(P):return min(key(P+k*T) for k in range(5))
    trace_orbits=[];new=set()
    for record in data['traces']['sources']:
        assert record['group_sum']==[-1,-1] and len(record['factor_traces'])==6
        reps=[];total=rd.E(0)
        for part in record['factor_traces']:
            P=point(part['trace']);reps.append(orbit(P));total+=P
        assert total==rd.E(0)
        new.update(set(reps)-set(l29))
        trace_orbits.append((record['source'],reps))
    keys=sorted(set(l29)|new);idx={a:i for i,a in enumerate(keys)}
    def remap(row,reps):return {str(idx[reps[int(j)]]):v for j,v in row.items()}
    base=[remap(r['coefficients'],old) for r in data['seed']['accepted_rows']]
    base += [remap(r,old) for r in data['frontier']['rows']]
    base += [remap(r['coefficients'],old) for r in data['sign']['sign_rows']]
    base += [remap(r['coefficients'],l23) for r in data['l23']['accepted_rows']]
    base += [remap(r['coefficients'],l29) for r in data['l29']['accepted_rows']]
    trace_rows=[{'source':source,'coefficients':{str(i):v for i,v in Counter(idx[a] for a in reps).items()}}
                for source,reps in trace_orbits]
    old_indices={idx[a] for a in old};new_indices=sorted(set(range(len(keys)))-old_indices)
    anchor=idx[orbit(point(protocol['anchor_point']))]
    def build(rows,ring):
        entries={(i,int(j)):v for i,row in enumerate(rows) for j,v in row.items()}
        entries[(len(rows),anchor)]=1
        return matrix(ring,len(rows)+1,len(keys),entries,sparse=False)
    before=build(base,GF(4021));K0=before.right_kernel()
    evaluation=matrix(GF(4021),[[sum(GF(4021)(v)*b[int(j)] for j,v in row['coefficients'].items())
                                 for b in K0.basis()] for row in trace_rows])
    gain=int(evaluation.rank())
    after=build(base+[r['coefficients'] for r in trace_rows],GF(4021))
    K=after.right_kernel()
    support=set().union(*(set(v.support()) for v in K.basis()))
    before_rank=int(before.rank());after_rank=int(after.rank())
    assert after_rank-before_rank==gain
    before_proj=int(before.matrix_from_columns(new_indices).rank())
    after_proj=int(after.matrix_from_columns(new_indices).rank())
    integer=build(base+[r['coefficients'] for r in trace_rows],ZZ)
    exact_rank=int(integer.rank())
    exact_proj=int(integer.matrix_from_columns(new_indices).rank())
    assert exact_rank==after_rank and exact_proj==after_proj
    result={'status':'L29_ALL_DEGREE7_TRACE_RANK_PRODUCED','protocol_sha256':sha(path),
            'source_sha256':{k:sha(v) for k,v in paths.items()},
            'trace_rows':trace_rows,'additional_representatives':sorted(new),
            'baseline':{'rank':before_rank,'new_column_projection_rank':before_proj,
                        'induced_old_rank':before_rank-before_proj,'nullity':int(K0.dimension())},
            'combined':{'rank':after_rank,'new_column_projection_rank':after_proj,
                        'induced_old_rank':after_rank-after_proj,'nullity':int(K.dimension()),
                        'ambiguous_old_indices':sorted(old.index(keys[i]) for i in support&old_indices)},
            'rank_gain_from_kernel_evaluation':gain,
            'kernel_evaluation_rows':[[int(x) for x in row] for row in evaluation.rows()],
            'exact_integer':{'rank':exact_rank,'new_column_projection_rank':exact_proj,
                             'induced_old_rank':exact_rank-exact_proj},
            'candidate_id':None,'timing_claim':None}
    (HERE/'degree7_rank_result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'new_reps':len(new),'baseline':result['baseline'],
                      'combined':result['combined'],'rank_gain':gain},sort_keys=True),flush=True)

if __name__=='__main__':main()
