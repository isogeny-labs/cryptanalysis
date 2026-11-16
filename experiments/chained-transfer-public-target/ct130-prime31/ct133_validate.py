#!/usr/bin/env python3
"""Independent Python-only public DLP verifier for native CT133 CSV. No producer imports.
Standing: [pcc:unverified], not a signed execution or independent timing receipt.
"""
import csv, hashlib, json, math, pathlib, sys, statistics, random
P=2147483033
Q=536857417
A=622683939
B=2147483024
G=(911976709,415929193)
H=(180482573,1535800095)
RR=969960860
II=392507391
LA=390258842
SEEDS=(20261210,20261211,20261212,20261213)
ARMS=('source_bsgs','source_neg_rho','target_glv_rho')
W=math.isqrt(Q-1)+1

def check(ok, message):
    if not ok: raise ValueError(message)

def add(X,Y,a,b):
    if X is None: return Y
    if Y is None: return X
    x,y=X;u,v=Y
    if x==u and (y+v)%P==0:return None
    if X==Y:
        den=2*y%P;num=(3*x*x+2*a*x+b)%P
    else:den=(u-x)%P;num=(v-y)%P
    check(den!=0,'zero denominator')
    lam=num*pow(den,-1,P)%P
    z=(lam*lam-a-x-u)%P
    return (z,(lam*(x-z)-y)%P)

def mult(X,k,a,b):
    out=None
    while k:
        if k&1:out=add(out,X,a,b)
        X=add(X,X,a,b);k>>=1
    return out

def on(X,a,b):
    if X is None: return True
    x,y=X
    return (y*y-x*x*x-a*x*x-b*x)%P==0

def mapping(X):
    if X is None: return None
    x,y=X
    check(x!=0,'kernel point')
    ix=pow(x,-1,P)
    return (((x+A+B*ix)*pow(4,-1,P)+RR)%P,
            (y*(1-B*ix*ix)*pow(8,-1,P))%P)

def setup():
    check(on(G,A,B),'source generator invalid')
    check(on(H,0,9),'target generator invalid')
    check(mult(G,Q,A,B) is None,'source order invalid')
    check(mult(H,Q,0,9) is None,'target order invalid')
    check(mapping(G)==H,'isogeny generator invalid')
    check((II*II+1)%P==0 and (LA*LA+1)%Q==0,'CM eigenvalues invalid')
    check(mult(H,LA,0,9)==((-H[0])%P,II*H[1]%P),'endomorphism mismatch')
    j=(256*pow((A*A-3*B)%P,3,P)*pow(B*B*(A*A-4*B)%P,-1,P))%P
    check(j!=1728,'source has direct geometric fourth roots')
    return j

def audit(text,expected_seed):
    lines=list(csv.reader(text.splitlines()))
    check(lines[0]==['schema','ct133-native-cm-v1'],'schema')
    check(lines[1]==['seed',str(expected_seed)],'seed')
    check(lines[2]==['count','64'],'count')
    check(len(lines)==3+64*6+3+1,'row count')
    sums={arm:{'ns':0,'adds':0,'invs':0,'iter':0,'cycles':0} for arm in ARMS}
    pairs=[]; seen=set(); aa=[]
    for idx in range(64):
        six=lines[3+idx*6:3+(idx+1)*6]
        schedule=ARMS+ARMS[::-1] if idx%2==0 else ARMS[::-1]+ARMS
        times={a:[] for a in ARMS}
        for n,row in enumerate(six):
            check(len(row)==13 and row[0]=='row','row schema')
            check(int(row[1])==idx and row[2]==schedule[n],'schedule')
            arm=row[2]
            known,recovered,x,y,ns,adds,invs,iterations,cycles,states=map(int,row[3:])
            check(0<known<Q and recovered==known,'discrete logarithm output mismatch')
            check(x>=0 and x<P and 0<=y<P,'public coordinates')
            check(0<ns<10**12 and adds>0 and invs>0,'timing/counter range')
            check(adds>=invs and cycles>=0,'counter plausibility')
            if arm=='source_bsgs':check(states==W and cycles==W and 0<=iterations<W,'fresh BSGS table and legacy diagnostic width')
            else:check(0<=cycles<=iterations and 0<states<=iterations<=1200000,'bounded rho states')
            Qp=(x,y)
            check(on(Qp,A,B) and mult(G,recovered,A,B)==Qp,'public source scalar audit')
            check(mapping(Qp)==mult(H,recovered,0,9),'public isogeny audit')
            val=sums[arm];val['ns']+=ns;val['adds']+=adds;val['invs']+=invs;val['iter']+=iterations;val['cycles']+=cycles
            times[arm].append(ns)
            if n==0: check(known not in seen,'duplicate target');seen.add(known)
            else:check(known in seen,'within-target inconsistency')
            if n:check((x,y)==(int(six[0][5]),int(six[0][6])) and known==int(six[0][3]),'public Q changed mid-run')
        pairs.append({a:sum(times[a]) for a in ARMS})
        aa.extend([max(t)/min(t) for t in times.values()])
    for i,arm in enumerate(ARMS):
        row=lines[3+64*6+i]
        check(len(row)==7 and row[:2]==['total',arm],'total header')
        check([int(v) for v in row[2:]] == [sums[arm][k] for k in ['ns','adds','invs','iter','cycles']],'aggregate corruption')
    end=lines[-1]
    check(len(end)==2 and end[0]=='ratio_best_source_over_target','ratio header')
    ratio=min(sums['source_bsgs']['ns'],sums['source_neg_rho']['ns'])/sums['target_glv_rho']['ns']
    check(abs(float(end[1])-ratio)<0.000006,'ratio mismatch')
    return dict(seed=expected_seed,ratio=ratio,sums=sums,pairs=pairs,aa_median=statistics.median(aa),
                raw_sha256=hashlib.sha256(text.encode()).hexdigest())

def all_audit(paths):
    check(len(paths)==4,'must provide four frozen files')
    j=setup()
    records=[audit(pathlib.Path(p).read_text(),seed) for seed,p in zip(SEEDS,paths)]
    totals={a:sum(r['sums'][a]['ns'] for r in records) for a in ARMS}
    pooled=min(totals['source_bsgs'],totals['source_neg_rho'])/totals['target_glv_rho']
    # Paired bootstrap of all 256 measured target blocks, purely descriptive of fixed cohort.
    pairs=[row for r in records for row in r['pairs']]
    rng=random.Random(0xC7133)
    sample=[]
    for _ in range(2000):
        picks=[pairs[rng.randrange(len(pairs))] for _ in pairs]
        sums={a:sum(v[a] for v in picks) for a in ARMS}
        sample.append(min(sums[ARMS[0]],sums[ARMS[1]])/sums[ARMS[2]])
    sample.sort()
    return dict(schema='ct133-independent-audit/v1',source_j=j,standing='[pcc:unverified]',
        panels=[dict(seed=r['seed'],ratio=r['ratio'],totals_ns={a:r['sums'][a]['ns'] for a in ARMS},
                     median_aa=r['aa_median'],sha256=r['raw_sha256']) for r in records],
        all_target_count=256,all_solver_invocations=1536,pooled_ratio=pooled,
        descriptive_bootstrap_95=[sample[49],sample[1949]],
        pooled_totals_ns=totals)

def selftest(paths):
    strings=[pathlib.Path(p).read_text() for p in paths]
    clean=all_audit(paths)
    check(clean['all_solver_invocations']==1536,'positive control failed')
    lines=[s.splitlines() for s in strings]
    variants=[]
    def mut(line_no,col,value):
        mutated=lines[0].copy();parts=mutated[line_no].split(',');parts[col]=value;mutated[line_no]=','.join(parts)
        variants.append('\n'.join(mutated)+'\n')
    mut(3,4,'0')
    mut(3,5,'0')
    mut(3,7,'0')
    mut(3,8,'0')
    mut(3,2,'target_glv_rho')
    mut(3,3,'0')
    mut(3+6,3,lines[0][3].split(',')[3])
    mut(3+64*6,2,'1')
    mut(3+64*6+3,1,'99')
    variants.append('\n'.join(lines[0][:-2])+'\n')
    for i,bad in enumerate(variants):
        failed=False
        try:audit(bad,SEEDS[0])
        except (ValueError,IndexError,TypeError):failed=True
        check(failed,f'mutation accepted: {i}')
    return len(variants)

if __name__=='__main__':
    ps=sys.argv[1:]
    test='--self-test' in ps
    if test:ps.remove('--self-test')
    if len(ps)!=4:raise SystemExit('usage: ct133_validate.py <seed10.csv> <seed11.csv> <seed12.csv> <seed13.csv> [--self-test]')
    output=all_audit(ps)
    if test:output['mutations_rejected']=selftest(ps)
    print(json.dumps(output,sort_keys=True,separators=(',',':')))
