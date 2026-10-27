"""Lift sources in the frozen residue order and check rank at fixed counts."""
import hashlib
import importlib.util
import itertools
import json
import math
import resource
import sys
import time
from collections import Counter
from pathlib import Path

from sage.all import classical_modular_polynomial

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
PLAN = json.loads((HERE / 'inputs.json').read_text())
POST_CLASS = json.loads((HERE / 'post-class.json').read_text())


def pinned(name):
    item = PLAN['frozen'][name]
    path = ROOT / item['path']
    if hashlib.sha256(path.read_bytes()).hexdigest() != item['sha256']:
        raise ValueError('PIN_MISMATCH:' + name)
    return path


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    out = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(out)
    return out


def sparse(raw):
    return {int(k):int(v) for k,v in raw.items() if v}


def group_law(p):
    def neg(A):
        return None if A is None else (A[0],(-A[1]-1)%p)
    def add(A,B):
        if A is None:return B
        if B is None:return A
        x,y=A;u,v=B
        if x==u and (y+v+1)%p==0:return None
        top,bottom=((3*x*x-2*x-10,2*y+1) if A==B else (v-y,u-x))
        slope=top*pow(bottom%p,-1,p)%p
        intercept=(y-slope*x)%p
        X=(slope*slope+1-x-u)%p
        Y=(-slope*X-intercept-1)%p
        return X,Y
    return neg,add


def rank(rows,q):
    pivots={}
    for row in rows:
        v={i:x%q for i,x in row.items() if x%q}
        while v:
            i=min(v)
            if i not in pivots:
                z=v[i]
                pivots[i]={j:x*pow(z,-1,q)%q for j,x in v.items()}
                break
            z=v[i]
            for j,x in pivots[i].items():
                y=(v.get(j,0)-z*x)%q
                if y:v[j]=y
                else:v.pop(j,None)
    return len(pivots)


def direct_rows(points,neg,add):
    out=[];trials=0
    for support in range(1,5):
        for inds in itertools.combinations(range(40),support):
            for rest in itertools.product((-1,1),repeat=support-1):
                signs=(1,)+rest
                trials+=1
                total=None
                for i,s in zip(inds,signs):
                    total=add(total,points[i] if s==1 else neg(points[i]))
                if total is None:
                    out.append({'indices':list(inds),'coefficients':list(signs),
                                'row':{str(i):s for i,s in zip(inds,signs)}})
    if trials!=772240:raise ValueError('DIRECT_TRIAL_COUNT_MISMATCH')
    return out,trials


def hecke_rows(entries,points,neg,add):
    ids=sorted(entries)
    totals={}
    for i,entry in entries.items():
        total=None
        for raw in entry['outside_traces']:
            total=add(total,tuple(raw))
        class_total=None
        for j,coeff in sparse(entry['class_part']).items():
            for _ in range(abs(coeff)):
                class_total=add(class_total,points[j] if coeff>0 else neg(points[j]))
        if add(total,class_total) is not None:
            raise ValueError('SOURCE_GROUP_MISMATCH:'+str(i))
        totals[i]=total
    out=[];trials=0
    for support in range(1,5):
        for inds in itertools.combinations(ids,support):
            for rest in itertools.product((-1,1),repeat=support-1):
                signs=(1,)+rest
                trials+=1
                total=None
                for i,s in zip(inds,signs):
                    total=add(total,totals[i] if s==1 else neg(totals[i]))
                if total is not None:continue
                row=Counter()
                for i,s in zip(inds,signs):
                    for j,coeff in sparse(entries[i]['class_part']).items():
                        row[j]+=s*coeff
                row={j:x for j,x in row.items() if x}
                check=None
                for j,coeff in row.items():
                    for _ in range(abs(coeff)):
                        check=add(check,points[j] if coeff>0 else neg(points[j]))
                if check is not None:raise ValueError('HECKE_ROW_GROUP_MISMATCH')
                out.append({'sources':list(inds),'coefficients':list(signs),
                            'row':{str(j):x for j,x in sorted(row.items())}})
    return out,trials


def main():
    class_path=HERE/'class-result.json'
    if hashlib.sha256(class_path.read_bytes()).hexdigest()!=POST_CLASS['class_result_sha256']:
        raise ValueError('CLASS_RESULT_CHANGED')
    class_result=json.loads(class_path.read_text())
    if class_result['status']!='CLASS_READY':
        raise ValueError('CLASS_NOT_READY')
    frozen=class_result['selected']
    p,q=frozen['p'],frozen['largest_prime_factor']
    order=frozen['source_order']
    if len(order)!=40 or sorted(order)!=list(range(40)):
        raise ValueError('ORDER_MISMATCH')
    H=module(pinned('hecke11.py'),'residue_holdout_source')
    P=module(pinned('prefix_runner.py'),'residue_holdout_prefix')
    S=module(pinned('shared-build.py'),'residue_holdout_digest')
    cache_path=pinned('cache-artifact.json')
    sys.path.insert(0,str(pinned('cache-api.py').parent))
    from cache_api import resolve
    funcs25,jfun25=H.build([2,5])
    def forbidden_build(*args,**kwargs):
        raise RuntimeError('DEGREE13_BUILD_FORBIDDEN')
    H.build=forbidden_build
    funcs13,jfun13,cache_receipt=resolve(
        H,cache_path,PLAN['frozen']['cache-artifact.json']['sha256'],
        PLAN['frozen']['hecke11.py']['sha256'],PLAN['cache_function_digest'],
        S.build_digest,'strict')
    if jfun13!=jfun25 or set(funcs25)&set(funcs13):
        raise ValueError('FUNCTION_MERGE_MISMATCH')
    R=H.Reduced(p,{**funcs25,**funcs13},jfun13,[2,5,13])
    E=R.E
    if int(E.cardinality())!=frozen['curve_order']:
        raise ValueError('CURVE_ORDER_MISMATCH')
    sage_points=[E(x,y) for x,y in frozen['class_points']]
    points=[tuple(x) for x in frozen['class_points']]
    neg,add=group_law(p)
    t0=time.perf_counter_ns()
    direct,trials=direct_rows(points,neg,add)
    direct_ns=time.perf_counter_ns()-t0
    baseline=[sparse(x['row']) for x in frozen['base_rows']+direct]
    baseline_rank=rank(baseline,q)
    modpoly=classical_modular_polynomial(13)
    out={'schema':'hecke-d79-residue-source-run-v1','status':'RUNNING',
         'p':p,'q':q,'curve_order':frozen['curve_order'],
         'frozen_source_order':order,'baseline_rank_mod_q':baseline_rank,
         'direct_candidate_count':len(direct),'direct_trials':trials,
         'direct_enumeration_wall_ns':direct_ns,'cache':cache_receipt,
         'source_entries':[],'checkpoints':[],'candidate_id':None,
         'target_online_ms':None}
    path=HERE/'source-result.json'
    path.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    entries={};cache={};lift_sum=0
    for count,i in enumerate(order,1):
        t0=time.perf_counter_ns()
        point=sage_points[i]
        poly=R.neighbour_x(13,point)
        pattern=[[int(f.degree()),int(mult)] for f,mult in poly.factor()]
        d=math.lcm(*(degree for degree,_ in pattern))
        if d>12 or any(mult!=1 for _,mult in pattern):
            entry={'source':i,'factor_pattern':pattern,'splitting_degree':d,
                   'status':'CENSORED_EXTENSION_OR_MULTIPLICITY'}
        else:
            entry,_=P.lift_source(i,point,R,jfun13,sage_points,{},cache,modpoly,pattern)
        entry['lift_wall_ns']=time.perf_counter_ns()-t0
        lift_sum+=entry['lift_wall_ns']
        out['source_entries'].append(entry)
        path.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
        if entry['status']!='OUTSIDE_CLASS_TRACE':
            out['status']='CENSORED_SOURCE'
            out['stop_source_count']=count
            break
        entries[i]=entry
        if count not in PLAN['checkpoints']:
            continue
        t0=time.perf_counter_ns()
        candidates,hecke_trials=hecke_rows(entries,points,neg,add)
        enumeration_ns=time.perf_counter_ns()-t0
        t0=time.perf_counter_ns()
        qrank=rank(baseline+[sparse(x['row']) for x in candidates],q)
        rank_ns=time.perf_counter_ns()-t0
        check={'source_count':count,'last_source':i,'source_ids':order[:count],
               'candidate_count':len(candidates),'hecke_trials':hecke_trials,
               'rank_mod_q':qrank,'source_lift_sum_ns':lift_sum,
               'hecke_enumeration_wall_ns':enumeration_ns,'rank_wall_ns':rank_ns,
               'status':'RANK39_STOP' if qrank>=39 else 'CONTINUE'}
        out['checkpoints'].append(check)
        path.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
        print(json.dumps({'p':p,'source_count':count,'rank_mod_q':qrank,
                          'candidate_count':len(candidates),'status':check['status']}),flush=True)
        if qrank>=39:
            out['status']='RANK39_STOP'
            out['stop_source_count']=count
            break
    else:
        out['status']='CAP40_RANK_DEFICIT'
        out['stop_source_count']=40
    out['source_lift_sum_ns']=lift_sum
    out['peak_rss_bytes']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    path.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'status':out['status'],'source_count':out['stop_source_count'],
                      'last_rank':None if not out['checkpoints'] else out['checkpoints'][-1]['rank_mod_q']}))


if __name__=='__main__':
    main()
