"""Select the next D79 class and freeze a direct-rank gate before lifts."""
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
    C=module('prior-class-builder.py','gate_class_builder')
    R=module('prior-source-runner.py','gate_relation_helpers')
    H=module('hecke11.py','gate_hecke_source')
    funcs,jfun=H.build([2,5])
    H79=hilbert_class_polynomial(-79)
    checked=[];selected=None
    for v in range(281,502,2):
        p=v*v+316
        if not is_prime(p):continue
        E=EllipticCurve(GF(p),[0,-1,1,-10,-20])
        n=int(E.cardinality())
        q=int(max(prime for prime,_ in factor(n)))
        if not (n%5==0 and (p-1)%5!=0 and q>=53):continue
        cell=C.class_case(H,funcs,jfun,H79,p,v,n,q)
        checked.append(cell)
        print(json.dumps({'p':p,'v':v,'class_size':cell['class_size'],
                          'status':cell['status']}),flush=True)
        if cell['status']=='CLASS_READY':
            selected=cell
            break
        if len(checked)==8:break
    out={'schema':'hecke-d79-direct-rank-gate-v1','status':'NO_CLASS',
         'checked_eligible_cases':checked,'selected':selected,
         'gate_threshold':37,'candidate_id':None,'target_online_ms':None}
    if selected:
        p,q=selected['p'],selected['largest_prime_factor']
        points=[tuple(x) for x in selected['class_points']]
        neg,add=R.group_law(p)
        t0=time.perf_counter_ns()
        direct,trials=R.direct_rows(points,neg,add)
        elapsed=time.perf_counter_ns()-t0
        baseline=[R.sparse(x['row']) for x in selected['base_rows']+direct]
        rank=R.rank(baseline,q)
        out.update({'status':'GATE_FROZEN','p':p,'q':q,
                    'direct_candidates':direct,'direct_trial_count':trials,
                    'direct_candidate_count':len(direct),
                    'direct_enumeration_wall_ns':elapsed,
                    'baseline_rank_mod_q':rank,
                    'gate_predicts_rank39':rank>=37,
                    'gate_decision':'LIFT' if rank>=37 else 'SKIP'})
    out['peak_rss_bytes']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    (HERE/'gate-result.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'status':out['status'],'selected_p':out.get('p'),
                      'baseline_rank':out.get('baseline_rank_mod_q'),
                      'gate_decision':out.get('gate_decision')}))


if __name__=='__main__':main()
