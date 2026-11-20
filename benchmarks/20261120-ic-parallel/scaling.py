"""Strong scaling of `ic bench --threads N`: paired, interleaved, with count parity.

Arms: threads 1,2,3,4 on one config; rounds R; order rotated per round.
Per run: process wall, sum of collector_wall_seconds (relation+LA phase),
and a fingerprint of every integer count (must equal the threads-1 one).
"""
import json, subprocess, sys, time, random, statistics, hashlib, os
BIN, OUT = sys.argv[1], sys.argv[2]
CONFIGS = {
 "prime24-subtract": "--bits 24 --factor-base prime-abscissa:size=256 --oracle subtract --repeats 4",
 "char2-23-descent-f4": "--char2-degree 23 --factor-base binary-subspace:dimension=7 --oracle descent-algebraic:m=2 --solver f4-f2 --repeats 2",
 "koblitz43-frobmitm": "--koblitz-degree 43 --factor-base koblitz-orbit:divisor=1 --oracle mitm-frobenius --repeats 4",
 "prime24-mitm2": "--bits 24 --factor-base prime-abscissa:size=256 --oracle mitm --repeats 8",
}
THREADS=[1,2,3,4]; ROUNDS=int(os.environ.get("ROUNDS","5"))
SKIP=('parallel','threads','wall','ns','seconds','elapsed','bytes','calibration','software','markdown','gae','rho')
def leaves(o,p=''):
    if isinstance(o,dict):
        for k,v in o.items():
            if any(t in k for t in SKIP): continue
            yield from leaves(v,p+'/'+k)
    elif isinstance(o,list):
        for i,v in enumerate(o): yield from leaves(v,f'{p}[{i}]')
    elif isinstance(o,(int,str,bool)) or o is None: yield p,o
rows=[]; rng=random.Random(20261120)
for name,args in CONFIGS.items():
    for rd in range(ROUNDS):
        order=THREADS[rd%4:]+THREADS[:rd%4]
        for t in order:
            f=f"{OUT}/{name}-r{rd}-t{t}.json"
            if os.path.exists(f): os.remove(f)
            t0=time.monotonic()
            subprocess.run([BIN,"bench",*args.split(),"--rho-runs","0","--threads",str(t),"--json","--out",f],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=True)
            wall=time.monotonic()-t0
            d=json.load(open(f))
            fp=hashlib.sha256(json.dumps(sorted(leaves({'i':d['instance'],'r':d['rows']}))).encode()).hexdigest()[:16]
            coll=sum(r['collector_wall_seconds'] for r in d['rows'])
            par=[r.get('parallel') for r in d['rows']]
            rows.append(dict(config=name,round=rd,threads=t,process_wall=wall,collector_wall=coll,fingerprint=fp,
                verified=all(r['verified'] for r in d['rows']), s=[r['s'] for r in d['rows']],
                discarded=sum((p or {}).get('discarded',0) for p in par), decomposed=sum((p or {}).get('decomposed',0) for p in par)))
            print(name,rd,t,round(wall,3),round(coll,3),fp,flush=True)
json.dump(rows,open(f"{OUT}/scaling_rows.json","w"),indent=1)
# summary: per config/threads, speedup of collector wall vs threads 1, paired by round
def boot(xs,n=10000,seed=1):
    r=random.Random(seed); m=[]
    for _ in range(n):
        smp=[xs[r.randrange(len(xs))] for _ in xs]; m.append(statistics.geometric_mean(smp))
    m.sort(); return m[int(.025*n)], m[int(.975*n)]
summ=[]
for name in CONFIGS:
    base={r['round']:r for r in rows if r['config']==name and r['threads']==1}
    fps={r['fingerprint'] for r in rows if r['config']==name}
    for t in THREADS:
        tr=[r for r in rows if r['config']==name and r['threads']==t]
        sc=[base[r['round']]['collector_wall']/r['collector_wall'] for r in tr]
        sp=[base[r['round']]['process_wall']/r['process_wall'] for r in tr]
        lo,hi=boot(sc)
        summ.append(dict(config=name,threads=t,collector_speedup=statistics.geometric_mean(sc),ci95=[lo,hi],
            process_speedup=statistics.geometric_mean(sp),collector_wall_median=statistics.median(r['collector_wall'] for r in tr),
            process_wall_median=statistics.median(r['process_wall'] for r in tr),
            counts_identical_to_t1=len(fps)==1, all_verified=all(r['verified'] for r in tr),
            discarded_frac=sum(r['discarded'] for r in tr)/max(1,sum(r['decomposed'] for r in tr))))
json.dump(summ,open(f"{OUT}/scaling_summary.json","w"),indent=1)
for s in summ: print(f"{s['config']:22s} t={s['threads']} speedup(collector)={s['collector_speedup']:.2f} [{s['ci95'][0]:.2f},{s['ci95'][1]:.2f}] process={s['process_speedup']:.2f} med_coll={s['collector_wall_median']:.3f}s counts_identical={s['counts_identical_to_t1']} verified={s['all_verified']} discarded={s['discarded_frac']:.3f}")
