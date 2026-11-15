#!/usr/bin/env python3
"""Independent CT144 toy-arithmetic and fixed-source-cost receipt auditor.
No import from C++ producer or CT135/136 source. Unverified scientific standing.
"""
from __future__ import annotations
import csv, hashlib, json, math, pathlib, random, re, statistics, sys, tempfile
P=2147483033; Q=536857417
A=622683939; B=2147483024; SHIFT=969960860
G=(911976709,415929193); H=(180482573,1535800095)
SEEDS=(20261340,20261341,20261342,20261343)
ARMS=("source_affine_bsgs","source_projective_bsgs","source_batch4_rho","target_batch16_rho")
E=(0,1,2,3,3,2,1,0); O=(3,2,1,0,0,1,2,3)
TARGETS_SHA='ea17d4ae6d39bbc61f834d50967cceae37f69fdf04806bfd80ff2750c439a7e3'
REF_SHA={'ct135_native.cpp':'5422e02524850bfb0f595901c063a07326079e9dd82a483e6085996ce97bbdb0',
         'ct136_native.cpp':'20b0305d0b291602dd141a278c00459c47e78608f17e33bea6395a3106438921'}

def need(ok,msg):
    if not ok: raise ValueError('CT144 REJECTED: '+msg)

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def plus(v,w,a,b):
    if v is None:return w
    if w is None:return v
    x,y=v;u,z=w
    if x==u and (y+z)%P==0:return None
    if x==u:
        need(y==z and y!=0, 'unexpected tangent denominator')
        slope=((3*x*x+2*a*x+b)*pow(2*y,-1,P))%P
    else:slope=((z-y)*pow((u-x)%P,-1,P))%P
    xx=(slope*slope-a-x-u)%P
    return xx, (slope*(x-xx)-y)%P

def times(v,k,a=A,b=B):
    r=None
    while k:
        if k&1:r=plus(r,v,a,b)
        v=plus(v,v,a,b);k//=2
    return r

def map2(v):
    if v is None:return None
    x,y=v
    need(x!=0,'2-torsion map in source subgroup')
    ix=pow(x,-1,P)
    return (((x+A+B*ix)*pow(4,-1,P)+SHIFT)%P,(y*(1-B*ix*ix)*pow(8,-1,P))%P)

def parse(text,seed):
    data=list(csv.reader(text.splitlines()))
    need(data[:3]==[['schema','ct144-projective-bsgs-cold-v1'],['seed',str(seed)],['count','32']], 'header identity/seed')
    rows=[r for r in data[3:] if r and r[0]=='row']
    totals=[r for r in data[3:] if r and r[0]=='total']
    ratio=[r for r in data[3:] if r and r[0]=='ratio_best_source_over_mapped']
    need(len(rows)==256 and len(totals)==4 and len(ratio)==1 and len(data)==264, 'incomplete or extra records')
    need([r[1] for r in totals]==list(ARMS), 'total ordering')
    observed={a:0 for a in ARMS}; by_target={}; ids=set()
    for z,r in enumerate(rows):
        need(len(r)==13,'row width')
        i,arm,secret,answer,x,y,ns,adds,invs,it,cy,states=(int(r[1]),r[2],*map(int,r[3:]))
        need(0<=i<32 and arm==ARMS[(O if i%2 else E)[z%8]] and i==z//8,'row/arm A/A permutation')
        need(0<secret<Q and secret==answer,'wrong public recovered log')
        need(ns>0 and adds>=0 and invs>=0 and it>=0 and cy>=0 and states>=0,'invalid counter/time')
        point=(x,y)
        need((y*y-x*x*x-A*x*x-B*x)%P==0,'source point off curve')
        if i not in by_target:
            need(secret not in ids,'duplicate target secret')
            ids.add(secret)
            need(times(G,secret)==point,'independently recomputed scalar point disagrees')
            need(times(H,secret,0,9)==map2(point),'isogeny target mismatch')
            by_target[i]=(secret,point)
        else:need(by_target[i]==(secret,point),'target inconsistent among arms')
        observed[arm]+=ns
    need(len(by_target)==32,'wrong distinct target count')
    for arm,sumrow in zip(ARMS,totals):
        need(len(sumrow)==3 and int(sumrow[2])==observed[arm],'forged total')
    expected=min(observed[a] for a in ARMS[:-1])/observed[ARMS[-1]]
    need(abs(float(ratio[0][1])-expected)<1e-4,'wrong reported solver ratio')
    return {'seed':seed,'times':observed,'targets':by_target,'rows':rows}

def frozen_keys(root,seed):
    path=root/'CT144_FROZEN_TARGETS.csv'
    need(sha(path)==TARGETS_SHA,'frozen public target manifest changed')
    rows=list(csv.DictReader(path.open()))
    need(len(rows)==128 and all(tuple(x)==('seed','index','secret','pubx','puby') for x in [rows[0].keys()]),
         'frozen manifest schema/count')
    seen=set(); out={}
    for r in rows:
        sid=int(r['seed']);i=int(r['index']);k=int(r['secret']);x=int(r['pubx']);y=int(r['puby'])
        need(sid in SEEDS and 0<=i<32 and (sid,i) not in seen,'bad frozen target identity or duplicate')
        seen.add((sid,i))
        if sid==seed:out[i]=(k,x,y)
    need(len(seen)==128 and len(out)==32,'frozen target census')
    # Optional independent crosscheck when the original CT140 external raw files are present.
    old=root/f'ct140_results/width4-{seed}.csv'
    if old.exists():
        raw=list(csv.reader(old.read_text().splitlines()))
        need(raw[:3]==[['schema','ct140-width4-cold-v1'],['seed',str(seed)],['count','32']], 'old CT140 header')
        for z in raw:
            if z and z[0]=='row':need(out[int(z[1])]==(int(z[3]),int(z[5]),int(z[6])),'CT140 original raw differs from frozen manifest')
    return out


def resource_receipt(root,repeat,seed):
    stem=root/f'ct144_results/repeat{repeat}-seed{seed}'
    need((stem.with_suffix('.exit')).read_text().strip()=='0','child exit nonzero')
    need((stem.with_suffix('.stderr')).read_text()=='','child stderr must be empty')
    lines=(stem.with_suffix('.time')).read_text()
    vals=re.findall(r'^\s*Elapsed \(wall clock\) time \(h:mm:ss or m:ss\):\s*(\S+)\s*$',lines,flags=re.M)
    rss=re.findall(r'^\s*Maximum resident set size \(kbytes\):\s*(\d+)\s*$',lines,flags=re.M)
    status=re.findall(r'^\s*Exit status:\s*(\d+)\s*$',lines,flags=re.M)
    need(len(vals)==len(rss)==len(status)==1,'missing/duplicate process metric')
    comps=vals[0].split(':')
    need(len(comps) in (2,3),'invalid elapsed shape')
    elapsed=0.
    for x in comps:elapsed=60*elapsed+float(x)
    peak=int(rss[0]);need(elapsed>0 and 0<peak<=2097152 and status[0]=='0','invalid process runtime/peak/status')
    return {'elapsed_seconds':elapsed,'peak_rss_kib':peak}

def audit(root):
    root=pathlib.Path(root)
    for name,digest in REF_SHA.items():need(sha(root/name)==digest,'changed frozen '+name)
    results={}; samples={arm:{} for arm in ARMS};max_rss=0;process_elapsed=0.
    for repeat in (1,2):
        for seed in SEEDS:
            path=root/f'ct144_results/repeat{repeat}-seed{seed}.csv'
            cur=parse(path.read_text(),seed)
            old=frozen_keys(root,seed)
            for idx,(secret,point) in cur['targets'].items():
                need((secret,*point)==old[idx],'modified CT140 target cohort')
            results[(repeat,seed)]={a:cur['times'][a] for a in ARMS}
            receipt=resource_receipt(root,repeat,seed)
            max_rss=max(max_rss,receipt['peak_rss_kib'])
            process_elapsed+=receipt['elapsed_seconds']
            for z in cur['rows']:
                samples[z[2]].setdefault((seed,int(z[1])),[]).append(int(z[7]))
    for arm in ARMS:need(len(samples[arm])==128 and all(len(x)==4 for x in samples[arm].values()),'missing A/A data '+arm)
    totals={arm:sum(x[arm] for x in results.values()) for arm in ARMS}
    best=min(ARMS[:-1],key=lambda a:totals[a]);ratio=totals[best]/totals[ARMS[-1]]
    # Paired target bootstrap over fixed selected arm (no reselecting winner).
    rnd=random.Random(14420261115)
    keys=sorted(samples[best]);pairs=[(sum(samples[best][key]),sum(samples[ARMS[-1]][key])) for key in keys]
    boot=[]
    for _ in range(3000):
        p=[pairs[rnd.randrange(len(pairs))] for _ in pairs]
        boot.append(sum(s for s,t in p)/sum(t for s,t in p))
    boot.sort()
    return {'schema':'ct144-independent-audit-v1','standing':'[pcc:unverified]',
            'complete_recoveries':2048,'distinct_targets':128,'runs':len(results),'process_elapsed_total_seconds':process_elapsed,
            'max_process_rss_kib':max_rss,
            'whole_cohort_ns':totals,'fastest_fixed_source':best,'source_over_mapped':ratio,
            'paired_bootstrap_95':[boot[75],boot[2924]],'paired_bootstrap_scope':'descriptive fixed-arm resampling; same virtual host, producer-run',
            'frozen_ct135_sha256':REF_SHA['ct135_native.cpp'],'frozen_ct136_sha256':REF_SHA['ct136_native.cpp']}

def sabotage_tests(root):
    seed=SEEDS[0];txt=(root/f'ct144_results/repeat1-seed{seed}.csv').read_text()
    lines=txt.splitlines()
    def changed(target,before,after):
        s=txt.replace(before,after,1)
        need(s!=txt,'sabotage target missing');return s
    mut={
       'wrong_scalar':changed('row',',239186786,239186786,',',239186786,239186785,'),
       'wrong_point':changed('row',',1436800083,1423547810,',',1436800084,1423547810,'),
       'missing_row':'\n'.join(x for j,x in enumerate(lines) if j!=4)+'\n',
       'forged_total':changed('total', 'total,source_affine_bsgs,','total,source_affine_bsgs,3'),
       'wrong_seed':changed('seed','seed,20261340','seed,20261341'),
       'duplicate_row':'\n'.join(lines[:6]+[lines[5]]+lines[6:])+'\n',
       'wrong_arm':changed('row','row,0,source_affine_bsgs','row,0,target_batch16_rho')
    }
    passed=[]
    for name,altered in mut.items():
        try:parse(altered,seed)
        except ValueError:passed.append(name)
        else:raise ValueError('sabotage survived: '+name)
    return passed

if __name__=='__main__':
    root=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else '.').resolve()
    out=audit(root)
    out['synthetic_controls_rejected']=sabotage_tests(root)
    print(json.dumps(out,sort_keys=True,indent=2))
