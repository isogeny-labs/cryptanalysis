"""Compute the F199 q-log vector and four relation-matrix kernels."""
import hashlib
import json
import resource
import time
from pathlib import Path

from sage.all import EllipticCurve, GF, matrix

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
PLAN = json.loads((HERE/'inputs.json').read_text())


def pinned(name):
    item=PLAN['frozen'][name]
    raw=(ROOT/item['path']).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=item['sha256']:
        raise ValueError('PIN_MISMATCH:'+name)
    return json.loads(raw)


def sparse(item):
    return {int(k):int(v) for k,v in item['row'].items() if v}


def dot(row,vector,q):
    return sum(coefficient*vector[i] for i,coefficient in row.items())%q


def main():
    cls=pinned('class-result.json')['cases'][0]
    prior=pinned('analysis.json')['cases'][0]
    result=pinned('result.json')
    if (pinned('audit-support4.json')['status'],pinned('audit-support5.json')['status'])!=('PASS','PASS'):
        raise ValueError('PARENT_AUDIT_NOT_PASS')
    p,q=PLAN['p'],PLAN['q']
    E=EllipticCurve(GF(p),[0,-1,1,-10,-20])
    if int(E.cardinality())!=PLAN['curve_order'] or cls['p']!=p or result['p']!=p:
        raise ValueError('INSTANCE_MISMATCH')
    points=[E(x,y) for x,y in cls['class_points']]
    start=time.perf_counter_ns()
    projected=[PLAN['cofactor_for_q_projection']*P for P in points]
    anchor=next(i for i,Q in enumerate(projected) if Q!=E(0))
    T=projected[anchor]
    table={k*T:k for k in range(q)}
    if len(table)!=q or int(T.order())!=q:
        raise ValueError('PROJECTION_ORDER_MISMATCH')
    if any(Q not in table for Q in projected):
        raise ValueError('Q_COMPONENT_NOT_CYCLIC')
    logs=[table[Q] for Q in projected]
    if logs[anchor]!=1 or not any(logs):
        raise ValueError('LOG_NORMALIZATION_FAIL')
    base=[sparse(x) for x in cls['base_rows']+prior['direct_candidates']+prior['hecke_candidates']]
    direct=[sparse(x) for x in result['arms']['direct']['candidates']]
    hecke=[sparse(x) for x in result['arms']['hecke']['candidates']]
    families={'support4':base,'support4_plus_direct5':base+direct,
              'support4_plus_hecke5':base+hecke,'support4_plus_both5':base+direct+hecke}
    out={'schema':'hecke-d79-p73757-kernel-result-v1','status':'RUNNING',
         'p':p,'q':q,'curve_order':int(E.cardinality()),'anchor_index':anchor,
         'anchor_point':[int(T[0]),int(T[1])],'q_logs':logs,
         'projection_nonzero_count':sum(Q!=E(0) for Q in projected),
         'families':{},'candidate_id':None,'target_online_ms':None}
    path=HERE/'result.json'
    path.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    for name,rows in families.items():
        failures=[i for i,row in enumerate(rows) if dot(row,logs,q)!=0]
        if failures:
            raise ValueError('ROW_LOG_MISMATCH:'+name+':'+str(failures[:5]))
        A=matrix(GF(q),len(rows),PLAN['class_size'],lambda i,j:rows[i].get(j,0))
        basis=[[int(x) for x in vector] for vector in A.right_kernel().basis()]
        rank=int(A.rank())
        if len(basis)!=PLAN['class_size']-rank:
            raise ValueError('KERNEL_DIMENSION_MISMATCH')
        if rank==39 and basis[0][anchor]!=0:
            z=pow(basis[0][anchor],-1,q)
            normalized=[x*z%q for x in basis[0]]
            if normalized!=logs:
                raise ValueError('UNIQUE_KERNEL_NOT_Q_LOGS')
        else:
            normalized=None
        nonzero_log_indices=[i for i,x in enumerate(logs) if x]
        anchor_rank=int(A.stack(matrix(GF(q),1,40,lambda _,j:int(j==anchor))).rank())
        out['families'][name]={'rows':len(rows),'rank_mod_q':rank,
                               'kernel_dimension':len(basis),'kernel_basis':basis,
                               'annihilated_rows':len(rows),'row_log_failures':0,
                               'normalized_unique_kernel':normalized,
                               'anchor_coordinate_rank':anchor_rank,
                               'nonzero_q_log_coordinates':len(nonzero_log_indices)}
        path.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
        print(json.dumps({'family':name,'rows':len(rows),'rank_mod_q':rank,
                          'kernel_dimension':len(basis),'anchor_rank':anchor_rank}),flush=True)
    out['q_log_vector_sha256']=hashlib.sha256(json.dumps(logs,separators=(',',':')).encode()).hexdigest()
    out['measured_wall_ns']=time.perf_counter_ns()-start
    out['peak_rss_bytes']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    out['status']='COMPLETE'
    path.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')


if __name__=='__main__':
    main()
