"""Solve the audited p63317 F2531 class-log system from one anchor."""
import hashlib
import json
import resource
import time
from pathlib import Path

from sage.all import EllipticCurve, GF, matrix, vector

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent.parent
PLAN=json.loads((HERE/'inputs.json').read_text())


def pinned(name):
    item=PLAN['frozen'][name]
    raw=(ROOT/item['path']).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=item['sha256']:
        raise ValueError('PIN_MISMATCH:'+name)
    return json.loads(raw)


def sparse(item):
    return {int(k):int(v) for k,v in item['row'].items() if v}


def main():
    cls=next(x for x in pinned('class-result.json')['cases'] if x['p']==PLAN['p'])
    analysis=next(x for x in pinned('analysis.json')['cases'] if x['p']==PLAN['p'])
    if pinned('audit.json')['status']!='PASS':
        raise ValueError('PARENT_AUDIT_NOT_PASS')
    p,q=PLAN['p'],PLAN['q']
    E=EllipticCurve(GF(p),[0,-1,1,-10,-20])
    if int(E.cardinality())!=PLAN['curve_order'] or cls['status']!='CLASS_READY' or analysis['status']!='COMPLETE':
        raise ValueError('INSTANCE_NOT_READY')
    points=[E(x,y) for x,y in cls['class_points']]
    projected=[PLAN['cofactor']*P for P in points]
    anchor=next(i for i,Q in enumerate(projected) if Q!=E(0))
    T=projected[anchor]
    if int(T.order())!=q:
        raise ValueError('ANCHOR_ORDER_MISMATCH')
    rows=[sparse(x) for x in cls['base_rows']+analysis['direct_candidates']+analysis['hecke_candidates']]
    if any(sum((v*points[i] for i,v in row.items()),E(0))!=E(0) for row in rows):
        raise ValueError('ROW_GROUP_MISMATCH')
    start=time.perf_counter_ns()
    F=GF(q)
    A=matrix(F,len(rows),40,lambda i,j:rows[i].get(j,0))
    rank=int(A.rank())
    if rank!=39:
        raise ValueError('RELATION_RANK_NOT_39')
    anchor_row=matrix(F,1,40,lambda _,j:int(j==anchor))
    augmented=A.stack(anchor_row)
    if int(augmented.rank())!=40:
        raise ValueError('ANCHOR_NOT_FULL_RANK')
    rhs=vector(F,[0]*len(rows)+[1])
    logs=[int(x) for x in augmented.solve_right(rhs)]
    if logs[anchor]!=1 or A*vector(F,logs)!=vector(F,[0]*len(rows)):
        raise ValueError('SOLVE_REPLAY_FAIL')
    out={'schema':'hecke-d79-p63317-class-logs-v1','status':'PASS','p':p,'q':q,
         'curve_order':int(E.cardinality()),'class_points':40,'relation_rows':len(rows),
         'relation_rank_mod_q':rank,'anchor_index':anchor,'anchor_point':[int(T[0]),int(T[1])],
         'q_logs':logs,'distinct_projected_base_points':len(set(projected)),
         'solve_wall_ns':time.perf_counter_ns()-start,
         'peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
         'candidate_id':None,'target_online_ms':None}
    (HERE/'class-logs.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'status':'PASS','rank_mod_q':rank,'anchor_index':anchor,
                      'distinct_base':out['distinct_projected_base_points']}))


if __name__=='__main__':
    main()
