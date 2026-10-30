"""Indexed support-five census and prospective source-order rank paths."""
import hashlib
import importlib.util
import json
import math
import resource
import time
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
POST = json.loads((HERE/'post_analysis_v2.json').read_text())


def checked(name):
    raw = (HERE/name).read_bytes()
    if hashlib.sha256(raw).hexdigest() != POST['sha256'][name]:
        raise ValueError('PIN_MISMATCH:' + name)
    return json.loads(raw)


def sparse(raw):
    return {int(k): int(v) for k, v in raw.items() if v}


def main():
    cls = checked('class-result.json')['cases'][0]
    src = checked('source-result.json')['cases'][0]
    prior = checked('analysis.json')['cases'][0]
    kernel_path = ROOT / POST['kernel_path']
    if hashlib.sha256(kernel_path.read_bytes()).hexdigest() != POST['kernel_sha256']:
        raise ValueError('KERNEL_SOURCE_MISMATCH')
    spec = importlib.util.spec_from_file_location('hecke_support5_holdout_kernel', kernel_path)
    K = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(K)
    if cls['status'] != 'CLASS_READY' or src['status'] != 'COMPLETE' or prior['status'] != 'COMPLETE':
        raise ValueError('PARENT_STAGE_INCOMPLETE')
    p, q = cls['p'], cls['largest_prime_factor']
    neg, add = K.group_law(p)
    points = [tuple(x) for x in cls['class_points']]
    source_entries = src['degree13_sources']
    totals = []
    for entry in source_entries:
        total = None
        for raw in entry['outside_traces']:
            total = add(total, tuple(raw))
        class_total = None
        for i, coefficient in sparse(entry['class_part']).items():
            for _ in range(abs(coefficient)):
                class_total = add(class_total, points[i] if coefficient > 0 else neg(points[i]))
        if add(class_total, total) is not None:
            raise ValueError('SOURCE_GROUP_MISMATCH')
        totals.append(total)
    base = [sparse(x['row']) for x in cls['base_rows']]
    base += [sparse(x['row']) for x in prior['direct_candidates']]
    base += [sparse(x['row']) for x in prior['hecke_candidates']]
    out = {'schema':'hecke-d79-support5-order-holdout-result-v1','status':'RUNNING',
           'p':p,'q':q,'curve_order':cls['curve_order'],'baseline_rows':len(base),
           'baseline_rank_qq':K.rank(base),'baseline_rank_mod_q':K.rank(base,q),
           'arms':{},'paths':{},'candidate_id':None,'target_online_ms':None}
    path = HERE/'result.json'
    path.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    arm_rows = {}
    for label, terms in [('direct',points),('hecke',totals)]:
        t0 = time.perf_counter_ns()
        candidates, hits, pair_entries = K.enumerate_indexed(terms,neg,add)
        index_ns = time.perf_counter_ns()-t0
        t0 = time.perf_counter_ns()
        records=[]
        for indices,signs in candidates:
            if label=='direct':
                row=dict(zip(indices,signs))
            else:
                row=Counter()
                for i,sign in zip(indices,signs):
                    for k,coefficient in sparse(source_entries[i]['class_part']).items():
                        row[k]+=sign*coefficient
                row={k:v for k,v in row.items() if v}
            total=None
            for k,coefficient in row.items():
                for _ in range(abs(coefficient)):
                    total=add(total,points[k] if coefficient>0 else neg(points[k]))
            if total is not None:
                raise ValueError('ROW_GROUP_MISMATCH')
            records.append({'indices' if label=='direct' else 'sources':list(indices),
                            'coefficients':list(signs),
                            'row':{str(k):v for k,v in sorted(row.items())}})
        verify_ns=time.perf_counter_ns()-t0
        arm_rows[label]=[sparse(x['row']) for x in records]
        out['arms'][label]={'status':'COMPLETE','candidate_count':len(records),
                            'signed_patterns':math.comb(40,5)*16,'raw_index_hits':hits,
                            'pair_entries':pair_entries,'index_wall_ns':index_ns,
                            'verification_wall_ns':verify_ns,'candidates':records,
                            'rank_qq':K.rank(base+arm_rows[label]),
                            'rank_mod_q':K.rank(base+arm_rows[label],q)}
        path.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
        print(json.dumps({'arm':label,'candidates':len(records),
                          'rank_qq':out['arms'][label]['rank_qq']}),flush=True)
    out['combined_rank_qq']=K.rank(base+arm_rows['direct']+arm_rows['hecke'])
    out['combined_rank_mod_q']=K.rank(base+arm_rows['direct']+arm_rows['hecke'],q)
    hecke=out['arms']['hecke']['candidates']
    for order_name in ('ascending','priority'):
        order=cls[order_name+'_order']
        first={'support4':0 if K.rank(base)==40 else None,
               'support4_plus_direct5':0 if K.rank(base+arm_rows['direct'])==40 else None}
        steps=[]
        for source in order:
            seen=set(order[:len(steps)+1])
            selected=[sparse(x['row']) for x in hecke if set(x['sources'])<=seen]
            ranks={}
            for label,rows in [('support4',base+selected),
                               ('support4_plus_direct5',base+arm_rows['direct']+selected)]:
                ranks[label]={'rank_qq':K.rank(rows),'rank_mod_q':K.rank(rows,q)}
                if ranks[label]['rank_qq']==40 and first[label] is None:
                    first[label]=len(steps)+1
            steps.append({'source':source,'source_count':len(steps)+1,
                          'candidate_count':len(selected),'ranks':ranks})
            if all(x is not None for x in first.values()):
                break
        out['paths'][order_name]={'status':'COMPLETE' if all(x is not None for x in first.values()) else 'CAP40',
                                  'first_rank40':first,'steps':steps}
        path.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    out['status']='COMPLETE'
    out['peak_rss_bytes']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    path.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'status':out['status'],'combined_rank_qq':out['combined_rank_qq'],
                      'paths':{k:v['first_rank40'] for k,v in out['paths'].items()}}))


if __name__=='__main__':
    main()
