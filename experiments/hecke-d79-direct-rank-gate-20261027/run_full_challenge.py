"""Challenge the frozen pre-lift decision by lifting all 40 sources."""
import hashlib
import importlib.util
import json
import math
import resource
import sys
import time
from pathlib import Path

from sage.all import classical_modular_polynomial

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent.parent
PLAN=json.loads((HERE/'inputs.json').read_text())
POST=json.loads((HERE/'post-gate.json').read_text())


def pinned(name):
    item=PLAN['frozen'][name]
    path=ROOT/item['path']
    if hashlib.sha256(path.read_bytes()).hexdigest()!=item['sha256']:
        raise ValueError('PIN_MISMATCH:'+name)
    return path


def module(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    out=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(out)
    return out


def main():
    gate_path=HERE/'gate-result.json'
    if hashlib.sha256(gate_path.read_bytes()).hexdigest()!=POST['gate_result_sha256']:
        raise ValueError('GATE_CHANGED_AFTER_DECISION')
    gate=json.loads(gate_path.read_text())
    if gate['status']!='GATE_FROZEN':raise ValueError('GATE_NOT_READY')
    c=gate['selected'];p,q=gate['p'],gate['q']
    Rhelp=module(pinned('prior-source-runner.py'),'gate_full_helpers')
    H=module(pinned('hecke11.py'),'gate_full_source')
    P=module(pinned('prefix_runner.py'),'gate_full_prefix')
    S=module(pinned('shared-build.py'),'gate_full_digest')
    cache_path=pinned('cache-artifact.json')
    sys.path.insert(0,str(pinned('cache-api.py').parent))
    from cache_api import resolve
    funcs25,jfun25=H.build([2,5])
    def forbidden_build(*args,**kwargs):raise RuntimeError('DEGREE13_BUILD_FORBIDDEN')
    H.build=forbidden_build
    funcs13,jfun13,cache_receipt=resolve(
        H,cache_path,PLAN['frozen']['cache-artifact.json']['sha256'],
        PLAN['frozen']['hecke11.py']['sha256'],PLAN['cache_function_digest'],
        S.build_digest,'strict')
    if jfun13!=jfun25 or set(funcs25)&set(funcs13):
        raise ValueError('FUNCTION_MERGE_MISMATCH')
    R=H.Reduced(p,{**funcs25,**funcs13},jfun13,[2,5,13])
    E=R.E
    if int(E.cardinality())!=c['curve_order']:
        raise ValueError('CURVE_ORDER_MISMATCH')
    sage_points=[E(x,y) for x,y in c['class_points']]
    points=[tuple(x) for x in c['class_points']]
    neg,add=Rhelp.group_law(p)
    baseline=[Rhelp.sparse(x['row']) for x in c['base_rows']+gate['direct_candidates']]
    if Rhelp.rank(baseline,q)!=gate['baseline_rank_mod_q']:
        raise ValueError('GATE_BASELINE_RANK_MISMATCH')
    modpoly=classical_modular_polynomial(13)
    out={'schema':'hecke-d79-direct-rank-gate-challenge-v1','status':'RUNNING',
         'p':p,'q':q,'frozen_gate_decision':gate['gate_decision'],
         'baseline_rank_mod_q':gate['baseline_rank_mod_q'],
         'cache':cache_receipt,'source_entries':[],
         'candidate_id':None,'target_online_ms':None}
    path=HERE/'challenge-result.json'
    path.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    entries={};cache={};lift_sum=0
    for i,point in enumerate(sage_points):
        t0=time.perf_counter_ns()
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
        if entry['status']=='OUTSIDE_CLASS_TRACE':entries[i]=entry
        print(json.dumps({'source':i,'status':entry['status']}),flush=True)
    out['source_lift_sum_ns']=lift_sum
    if len(entries)==40:
        t0=time.perf_counter_ns()
        hecke,trials=Rhelp.hecke_rows(entries,points,neg,add)
        enum_ns=time.perf_counter_ns()-t0
        full_rank=Rhelp.rank(baseline+[Rhelp.sparse(x['row']) for x in hecke],q)
        out.update({'status':'COMPLETE','hecke_candidate_count':len(hecke),
                    'hecke_trial_count':trials,'hecke_enumeration_wall_ns':enum_ns,
                    'full_pool_rank_mod_q':full_rank,
                    'rank39_reached':full_rank>=PLAN['rank_goal'],
                    'gate_validation':'CORRECT_REJECT' if not gate['gate_predicts_rank39'] and full_rank<39
                    else 'FALSE_REJECT' if not gate['gate_predicts_rank39'] else
                    'CORRECT_ACCEPT' if full_rank>=39 else 'FALSE_ACCEPT'})
    else:
        out.update({'status':'CENSORED_SOURCE','hecke_candidate_count':None,
                    'full_pool_rank_mod_q':None,'rank39_reached':None,
                    'gate_validation':'UNKNOWN'})
    out['peak_rss_bytes']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    path.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'status':out['status'],'full_rank':out['full_pool_rank_mod_q'],
                      'gate_validation':out['gate_validation']}))


if __name__=='__main__':main()
