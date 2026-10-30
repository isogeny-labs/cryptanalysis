"""Challenge all four frozen direct-rank decisions with full source pools."""
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


def save(path,out):
    path.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')


def main():
    gate_path=HERE/'gate-result.json'
    if hashlib.sha256(gate_path.read_bytes()).hexdigest()!=POST['gate_result_sha256']:
        raise ValueError('GATE_CHANGED_AFTER_DECISIONS')
    gate=json.loads(gate_path.read_text())
    if gate['status']!='FOUR_GATES_FROZEN' or len(gate['selected'])!=4:
        raise ValueError('FOUR_GATES_NOT_READY')
    helper=module(pinned('prior-source-runner.py'),'series_full_helpers')
    H=module(pinned('hecke11.py'),'series_full_source')
    P=module(pinned('prefix_runner.py'),'series_full_prefix')
    S=module(pinned('shared-build.py'),'series_full_digest')
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
    funcs={**funcs25,**funcs13}
    modpoly=classical_modular_polynomial(13)
    out={'schema':'hecke-d79-direct-rank-gate-series-challenge-v1',
         'status':'RUNNING','cache':cache_receipt,'cases':[],
         'candidate_id':None,'target_online_ms':None}
    path=HERE/'challenge-result.json'
    save(path,out)
    for frozen in gate['selected']:
        c=frozen['class'];p,q=frozen['p'],frozen['q']
        cell={'p':p,'q':q,'status':'RUNNING',
              'frozen_gate_decision':frozen['gate_decision'],
              'baseline_rank_mod_q':frozen['baseline_rank_mod_q'],
              'source_entries':[],'candidate_id':None,'target_online_ms':None}
        out['cases'].append(cell)
        save(path,out)
        try:
            R=H.Reduced(p,funcs,jfun13,[2,5,13])
            E=R.E
            if int(E.cardinality())!=c['curve_order']:
                raise ValueError('CURVE_ORDER_MISMATCH')
            sage_points=[E(x,y) for x,y in c['class_points']]
            points=[tuple(x) for x in c['class_points']]
            neg,add=helper.group_law(p)
            baseline=[helper.sparse(x['row']) for x in c['base_rows']+frozen['direct_candidates']]
            if helper.rank(baseline,q)!=frozen['baseline_rank_mod_q']:
                raise ValueError('GATE_BASELINE_RANK_MISMATCH')
            entries={};cache={};lift_sum=0
            for i,point in enumerate(sage_points):
                t0=time.perf_counter_ns()
                poly=R.neighbour_x(13,point)
                pattern=[[int(f.degree()),int(mult)] for f,mult in poly.factor()]
                degree=math.lcm(*(d for d,_ in pattern))
                if degree>12 or any(mult!=1 for _,mult in pattern):
                    entry={'source':i,'factor_pattern':pattern,'splitting_degree':degree,
                           'status':'CENSORED_EXTENSION_OR_MULTIPLICITY'}
                else:
                    entry,_=P.lift_source(i,point,R,jfun13,sage_points,{},cache,modpoly,pattern)
                entry['lift_wall_ns']=time.perf_counter_ns()-t0
                lift_sum+=entry['lift_wall_ns']
                cell['source_entries'].append(entry)
                if entry['status']=='OUTSIDE_CLASS_TRACE':entries[i]=entry
                save(path,out)
            cell['source_lift_sum_ns']=lift_sum
            if len(entries)==40:
                t0=time.perf_counter_ns()
                hecke,trials=helper.hecke_rows(entries,points,neg,add)
                enum_ns=time.perf_counter_ns()-t0
                full_rank=helper.rank(baseline+[helper.sparse(x['row']) for x in hecke],q)
                reached=full_rank>=PLAN['rank_goal']
                predicted=frozen['gate_decision']=='LIFT'
                cell.update({'status':'COMPLETE','hecke_candidate_count':len(hecke),
                             'hecke_trial_count':trials,'hecke_enumeration_wall_ns':enum_ns,
                             'full_pool_rank_mod_q':full_rank,'rank39_reached':reached,
                             'gate_validation':('CORRECT_ACCEPT' if predicted else 'FALSE_REJECT')
                             if reached else ('FALSE_ACCEPT' if predicted else 'CORRECT_REJECT')})
            else:
                cell.update({'status':'CENSORED_SOURCE','hecke_candidate_count':None,
                             'full_pool_rank_mod_q':None,'rank39_reached':None,
                             'gate_validation':'UNKNOWN'})
        except Exception as exc:
            cell.update({'status':'SOURCE_OR_ANALYSIS_EXCEPTION',
                         'error_type':type(exc).__name__,
                         'hecke_candidate_count':None,'full_pool_rank_mod_q':None,
                         'rank39_reached':None,'gate_validation':'UNKNOWN'})
        save(path,out)
        print(json.dumps({'p':p,'status':cell['status'],
                          'baseline_rank':cell['baseline_rank_mod_q'],
                          'full_rank':cell.get('full_pool_rank_mod_q'),
                          'gate_validation':cell['gate_validation']}),flush=True)
    out['status']='COMPLETE'
    out['gate_counts']={label:sum(c['gate_validation']==label for c in out['cases'])
                        for label in ('CORRECT_ACCEPT','CORRECT_REJECT','FALSE_ACCEPT','FALSE_REJECT','UNKNOWN')}
    out['peak_rss_bytes']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    save(path,out)
    print(json.dumps({'status':out['status'],'gate_counts':out['gate_counts']}))


if __name__=='__main__':main()
