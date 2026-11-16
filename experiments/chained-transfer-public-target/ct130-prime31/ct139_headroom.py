#!/usr/bin/env python3
"""CT139 independently recomputes frozen CT138 transfer-cost headroom.

Time-accounting auditor, not an elliptic-curve verifier. Run CT138's independent
arithmetic verifier first. Explicit gates also work under optimized Python.
"""
import csv
import hashlib
import io
import json
import pathlib
import sys

WIDTHS=(16,32,64)
SEEDS=(20261340,20261341,20261342,20261343)
ORDER=((20261340,16),(20261340,32),(20261340,64),
       (20261341,32),(20261341,64),(20261341,16),
       (20261342,64),(20261342,16),(20261342,32),
       (20261343,64),(20261343,32),(20261343,16))
COUNT=32
P=2147483033
Q=536857417
EXPECTED_BASE={'source_bsgs','source_neg_rho','target_glv_rho'}

def must(p,msg):
    if not p: raise ValueError(msg)

def parse(data,w,seed):
    names=EXPECTED_BASE | {f'source_batch{w}_rho',f'target_batch{w}_rho'}
    rows=list(csv.reader(io.StringIO(data)))
    must(rows[:3]==[['schema',f'ct138-width{w}-cold-v1'],['seed',str(seed)],['count','32']], 'header / seed')
    must(len(rows)==3+10*COUNT+5+2,'row count')
    totals={a:0 for a in names}
    per_target={}
    for idx in range(COUNT):
        sample=rows[3+idx*10:3+(idx+1)*10]
        seen={a:0 for a in names}
        sample_id=None
        for row in sample:
            must(len(row)==14 and row[0]=='row' and row[1]==str(idx),'row shape and index')
            arm=row[2];must(arm in names,'unknown arm')
            try:
                k,sol,px,py,ns,adds,invs,scalarinv,iterations,cycles,states=map(int,row[3:])
            except ValueError as e: raise ValueError('non-integer measurement') from e
            must(0<k<Q and k==sol, 'scalar mismatch; arithmetic checker still required')
            must(0<=px<P and 0<=py<P, 'public point range')
            must(0<ns<120_000_000_000 and adds>=0 and invs>=0 and scalarinv in (0,1)
                 and iterations>=0 and cycles>=0 and states>=0,'invalid measurement')
            must(scalarinv == (0 if arm=='source_bsgs' else 1),'inverse flag mismatch')
            if sample_id is None:sample_id=(k,px,py)
            must(sample_id==(k,px,py),'public target changed between arms')
            totals[arm]+=ns
            seen[arm]+=1
        must(all(n==2 for n in seen.values()),'ABBA/missing two repeats')
        per_target[idx]=sample_id
    for arm in names:
        expected=['total',arm,str(totals[arm])]
        must(expected in rows[3+10*COUNT:],'reported total differs')
    trailer=rows[3+10*COUNT:]
    must(sum(x[0]=='total' for x in trailer)==5,'footer totals count')
    must({x[0] for x in trailer if x[0]!='total'}==
         {'ratio_best_source_over_best_target','ratio_source_batch_over_target_batch'},'footer ratios')
    for name,calc in [
       ('ratio_best_source_over_best_target',
        min(totals[x] for x in names if x.startswith('source'))/
        min(totals[x] for x in names if x.startswith('target'))),
       ('ratio_source_batch_over_target_batch',
        totals[f'source_batch{w}_rho']/totals[f'target_batch{w}_rho'])]:
        row=next((x for x in trailer if x[0]==name),None)
        must(row is not None and len(row)==2,'missing ratio')
        must(abs(float(row[1])-calc)<0.00001,'ratio footer mismatch')
    return totals, per_target

def audit(root):
    root=pathlib.Path(root)
    must((root/'sequence.txt').read_text().splitlines()==[f'{s}:{w}' for s,w in ORDER], 'rotating sequence')
    results=root/'results'
    expected={f'width{w}-{s}.csv' for s,w in ORDER}
    must({f.name for f in results.glob('*.csv')}==expected,'raw CSV set')
    t_by_w={w:{} for w in WIDTHS}
    targets={}
    sha={}
    resource={}
    for seed,w in ORDER:
        path=results/f'width{w}-{seed}.csv'
        raw=path.read_bytes()
        sha[f'{seed}:{w}']=hashlib.sha256(raw).hexdigest()
        total,items=parse(raw.decode(),w,seed)
        timep=path.with_suffix('.time')
        must(timep.exists() and path.with_suffix('.stderr').exists(),'missing resource / stderr')
        timing={k:v for k,v in (word.split('=',1) for word in timep.read_text().split())}
        must(set(timing)=={'wall_seconds','maxrss_kb'},'receipt schema')
        must(0<=float(timing['wall_seconds'])<120 and 0<int(timing['maxrss_kb'])<2097152,'receipt bounds')
        resource[f'{seed}:{w}']={'wall_seconds':float(timing['wall_seconds']), 'maxrss_kb':int(timing['maxrss_kb'])}
        must(path.with_suffix('.stderr').read_text()=='','nonempty stderr')
        for idx,point in items.items():
            tag=(seed,idx)
            if tag in targets:must(targets[tag]==point,'different scalar/public point across widths')
            else:targets[tag]=point
        for arm,cost in total.items():t_by_w[w][arm]=t_by_w[w].get(arm,0)+cost
    s=min((cost,w,arm) for w,block in t_by_w.items() for arm,cost in block.items() if arm.startswith('source'))
    t=min((cost,w,arm) for w,block in t_by_w.items() for arm,cost in block.items() if arm.startswith('target'))
    out={'scope':'same selected 31-bit CM-neighbor public toy curve; no 695-record Jacobian full transfer',
         'standing':'[pcc:unverified]', 'public_targets':len(targets),'complete_recoveries':len(ORDER)*COUNT*10,
         'best_source':[s[0],s[1],s[2]],'best_transferred':[t[0],t[1],t[2]],
         'ratio':s[0]/t[0], 'transfer_extra_headroom_ns_per_target':(s[0]-t[0])/len(targets),
         'transfer_extra_headroom_ms_per_target':(s[0]-t[0])/len(targets)/1e6,
         'total_margin_ns':s[0]-t[0], 'by_width':{},'raw_sha256':sha,'resource':resource,
         'interpretation':'Arithmetic maximum unmeasured EXTRA overhead for selected paired toy run. Existing mapped timings already contain two isogeny evaluations and scalar verification. Cannot extrapolate to other curve or original 695/701 chain.'}
    for w in WIDTHS:
        so=min((v,a) for a,v in t_by_w[w].items() if a.startswith('source'))
        ta=min((v,a) for a,v in t_by_w[w].items() if a.startswith('target'))
        out['by_width'][str(w)]={'source_ns':so[0],'source_arm':so[1],
            'transferred_ns':ta[0],'target_arm':ta[1],
            'source_over_transfer':so[0]/ta[0],
            'extra_headroom_ms_per_target':(so[0]-ta[0])/len(targets)/1e6}
    return out

def negative():
    root=pathlib.Path(__file__).resolve().parent
    data=(root/'results/width16-20261340.csv').read_text()
    variants={
       'corrupt_scalar':data.replace(',239186786,239186786,',',239186786,239186787,',1),
       'negative_ns':data.replace(',4254697,',',-1,',1),
       'wrong_arm':data.replace(',source_bsgs,',',source_glv_bsgs,',1),
       'missing_row':'\n'.join(data.splitlines()[:-7])+'\n',
       'changed_point':data.replace(',1436800083,1423547810,',',1436800083,1423547811,',1),
       'wrong_width':data.replace('schema,ct138-width16-cold-v1','schema,ct138-width999-cold-v1',1),
    }
    for name,bad in variants.items():
        try:parse(bad,16,20261340)
        except (ValueError,StopIteration):pass
        else:raise RuntimeError('fail-open: '+name)
    return list(variants)

if __name__=='__main__':
    must(len(sys.argv)==3,'usage: script OLD_RUN_ROOT NEW_RUN_ROOT')
    controls=negative()
    old=audit(sys.argv[1]);new=audit(sys.argv[2]);
    must(old['public_targets']==new['public_targets']==128,'target count')
    report={'schema':'ct139-extra-cold-transfer-headroom-v1','negative_controls_rejected':controls,
            'old':old,'new':new,
            'ratio_difference_new_minus_old':new['ratio']-old['ratio'],
            'same_physical_host_confirmed':False,
            'host_note':'different container IDs; both AMD EPYC 9V74 VM, GCC 14.2.0, 4-vCPU quota, physical host independence NOT demonstrated',
            'limitation':'Neither run measures original-prime C169,C13a,C13b,D, complete 695/701 Jacobian setup or strongest source IC. No new original-prime complete solve advantage.'}
    print(json.dumps(report,sort_keys=True,indent=2))
