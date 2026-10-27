"""Freeze four new D79 class choices and direct-rank gate decisions."""
import hashlib
import importlib.util
import json
import resource
import time
from pathlib import Path

from sage.all import EllipticCurve, GF, factor, hilbert_class_polynomial, is_prime

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent.parent
PLAN=json.loads((HERE/'inputs.json').read_text())


def module(name,alias):
    item=PLAN['frozen'][name]
    path=ROOT/item['path']
    if hashlib.sha256(path.read_bytes()).hexdigest()!=item['sha256']:
        raise ValueError('PIN_MISMATCH:'+name)
    spec=importlib.util.spec_from_file_location(alias,path)
    out=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(out)
    return out


def main():
    C=module('prior-class-builder.py','series_class_builder')
    R=module('prior-source-runner.py','series_relation_helpers')
    H=module('hecke11.py','series_hecke_source')
    funcs,jfun=H.build([2,5])
    H79=hilbert_class_polynomial(-79)
    checked=[];selected=[]
    path=HERE/'gate-result.json'
    for v in range(303,502,2):
        p=v*v+316
        if not is_prime(p):continue
        E=EllipticCurve(GF(p),[0,-1,1,-10,-20])
        n=int(E.cardinality())
        q=int(max(prime for prime,_ in factor(n)))
        if not (n%5==0 and (p-1)%5!=0 and q>=53):continue
        try:
            cell=C.class_case(H,funcs,jfun,H79,p,v,n,q)
        except Exception as exc:
            cell={'p':p,'v':v,'curve_order':n,'largest_prime_factor':q,
                  'status':'CLASS_CONSTRUCTION_ERROR','error_type':type(exc).__name__}
        checked.append(cell)
        if cell['status']=='CLASS_READY':
            points=[tuple(x) for x in cell['class_points']]
            neg,add=R.group_law(p)
            t0=time.perf_counter_ns()
            direct,trials=R.direct_rows(points,neg,add)
            elapsed=time.perf_counter_ns()-t0
            baseline=[R.sparse(x['row']) for x in cell['base_rows']+direct]
            direct_rank=R.rank(baseline,q)
            selected.append({'p':p,'q':q,'class':cell,
                             'direct_candidates':direct,'direct_trial_count':trials,
                             'direct_candidate_count':len(direct),
                             'direct_enumeration_wall_ns':elapsed,
                             'baseline_rank_mod_q':direct_rank,
                             'gate_decision':'LIFT' if direct_rank>=37 else 'SKIP'})
        out={'schema':'hecke-d79-direct-rank-gate-series-selection-v1',
             'status':'RUNNING','checked_eligible_cases':checked,'selected':selected,
             'gate_threshold':37,'candidate_id':None,'target_online_ms':None}
        path.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
        print(json.dumps({'p':p,'v':v,'class_status':cell['status'],
                          'gate_decision':None if cell['status']!='CLASS_READY' else selected[-1]['gate_decision'],
                          'direct_rank':None if cell['status']!='CLASS_READY' else selected[-1]['baseline_rank_mod_q']}),flush=True)
        if len(selected)==4 or len(checked)==16:break
    out['status']='FOUR_GATES_FROZEN' if len(selected)==4 else 'SELECTION_SHORTAGE'
    out['peak_rss_bytes']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    path.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'status':out['status'],'selected_p':[x['p'] for x in selected]}))


if __name__=='__main__':main()
