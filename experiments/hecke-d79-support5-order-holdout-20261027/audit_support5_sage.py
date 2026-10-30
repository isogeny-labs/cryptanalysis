"""Independent exhaustive Sage audit of support-five sets and rank paths."""
import hashlib
import itertools
import json
import resource
import time
from collections import Counter
from pathlib import Path

from sage.all import EllipticCurve, GF, QQ, matrix

HERE = Path(__file__).resolve().parent
POST = json.loads((HERE/'post_result.json').read_text())


def pinned(name):
    raw = (HERE/name).read_bytes()
    if hashlib.sha256(raw).hexdigest() != POST['sha256'][name]:
        raise ValueError('PIN_MISMATCH:' + name)
    return json.loads(raw)


def sparse(raw):
    return {int(k):int(v) for k,v in raw.items() if v}


def rank(rows,field):
    return int(matrix(field,len(rows),40,lambda i,j:rows[i].get(j,0)).rank()) if rows else 0


def exhaustive(terms):
    neg=[-x for x in terms]
    pairs={(i,j,a,b):(terms[i] if a==1 else neg[i])+(terms[j] if b==1 else neg[j])
           for i,j in itertools.combinations(range(40),2)
           for a,b in itertools.product((-1,1),repeat=2)}
    found=set()
    count=0
    for i,j,k,l,m in itertools.combinations(range(40),5):
        for b,c in itertools.product((-1,1),repeat=2):
            left=terms[i]+(terms[j] if b==1 else neg[j])+(terms[k] if c==1 else neg[k])
            for d,e in itertools.product((-1,1),repeat=2):
                count+=1
                if left == -pairs[l,m,d,e]:
                    found.add(((i,j,k,l,m),(1,b,c,d,e)))
    return found,count


def main():
    result=pinned('result.json')
    cls=pinned('class-result.json')['cases'][0]
    src=pinned('source-result.json')['cases'][0]
    earlier=pinned('analysis.json')['cases'][0]
    prior_audit=pinned('audit-support4.json')
    if prior_audit['status']!='PASS':
        raise ValueError('SUPPORT4_AUDIT_NOT_PASS')
    p,q=result['p'],result['q']
    E=EllipticCurve(GF(p),[0,-1,1,-10,-20])
    if int(E.cardinality())!=result['curve_order'] or cls['p']!=p:
        raise ValueError('CURVE_MISMATCH')
    points=[E(x,y) for x,y in cls['class_points']]
    totals=[sum((E(x,y) for x,y in item['outside_traces']),E(0))
            for item in src['degree13_sources']]
    base=[sparse(x['row']) for x in cls['base_rows']+earlier['direct_candidates']+earlier['hecke_candidates']]
    if len(base)!=result['baseline_rows'] or (rank(base,QQ),rank(base,GF(q)))!=(result['baseline_rank_qq'],result['baseline_rank_mod_q']):
        raise ValueError('BASELINE_MISMATCH')
    out={'schema':'hecke-d79-support5-order-holdout-sage-audit-v1','status':'RUNNING',
         'p':p,'q':q,'arms':{},'paths':{}}
    path=HERE/'audit-support5.json'
    path.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    arm_rows={}
    for label,terms in [('direct',points),('hecke',totals)]:
        t0=time.perf_counter_ns()
        found,trials=exhaustive(terms)
        wall_ns=time.perf_counter_ns()-t0
        records=result['arms'][label]['candidates']
        key='indices' if label=='direct' else 'sources'
        expected={(tuple(x[key]),tuple(x['coefficients'])) for x in records}
        if found!=expected or trials!=10528128:
            raise ValueError('EXHAUSTIVE_SET_MISMATCH:'+label)
        rows=[]
        for item in records:
            inds,signs=item[key],item['coefficients']
            if label=='direct':
                reconstructed=dict(zip(inds,signs))
            else:
                reconstructed=Counter()
                for source,sign in zip(inds,signs):
                    for i,coefficient in sparse(src['degree13_sources'][source]['class_part']).items():
                        reconstructed[i]+=sign*coefficient
                reconstructed={i:v for i,v in reconstructed.items() if v}
            row=sparse(item['row'])
            if row!=reconstructed or sum((v*points[i] for i,v in row.items()),E(0))!=E(0):
                raise ValueError('ROW_MISMATCH:'+label)
            rows.append(row)
        ranks=(rank(base+rows,QQ),rank(base+rows,GF(q)))
        if ranks!=(result['arms'][label]['rank_qq'],result['arms'][label]['rank_mod_q']):
            raise ValueError('ARM_RANK_MISMATCH:'+label)
        arm_rows[label]=rows
        out['arms'][label]={'status':'PASS','trials':trials,'candidates':len(found),
                            'rank_qq':ranks[0],'rank_mod_q':ranks[1],'wall_ns':wall_ns}
        path.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
        print(json.dumps({'arm':label,'status':'PASS','candidates':len(found)}),flush=True)
    both=base+arm_rows['direct']+arm_rows['hecke']
    if (rank(both,QQ),rank(both,GF(q)))!=(result['combined_rank_qq'],result['combined_rank_mod_q']):
        raise ValueError('COMBINED_RANK_MISMATCH')
    for order_name in ('ascending','priority'):
        expected_order=cls[order_name+'_order']
        path_record=result['paths'][order_name]
        first={'support4':0 if rank(base,QQ)==40 else None,
               'support4_plus_direct5':0 if rank(base+arm_rows['direct'],QQ)==40 else None}
        for number,step in enumerate(path_record['steps'],1):
            if step['source']!=expected_order[number-1] or step['source_count']!=number:
                raise ValueError('ORDER_MISMATCH')
            seen=set(expected_order[:number])
            selected=[sparse(x['row']) for x in result['arms']['hecke']['candidates']
                      if set(x['sources'])<=seen]
            if step['candidate_count']!=len(selected):
                raise ValueError('PREFIX_CANDIDATE_COUNT_MISMATCH')
            for label,rows in [('support4',base+selected),
                               ('support4_plus_direct5',base+arm_rows['direct']+selected)]:
                ranks={'rank_qq':rank(rows,QQ),'rank_mod_q':rank(rows,GF(q))}
                if step['ranks'][label]!=ranks:
                    raise ValueError('PREFIX_RANK_MISMATCH')
                if ranks['rank_qq']==40 and first[label] is None:
                    first[label]=number
        if first!=path_record['first_rank40'] or len(path_record['steps'])!=max(first.values()):
            raise ValueError('FIRST_HIT_MISMATCH')
        out['paths'][order_name]={'first_rank40':first,'checked_prefixes':len(path_record['steps'])}
    out['status']='PASS'
    out['peak_rss_bytes']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    path.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'status':'PASS','paths':out['paths']}))


if __name__=='__main__':
    main()
