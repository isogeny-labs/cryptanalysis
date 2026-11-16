#!/usr/bin/env python3
"""CT135 independent arithmetic/CSV auditor; does not import producer's C++.
No signed PCC, timing/custody verification or execution-proof backend.
"""
import csv, hashlib, json, pathlib, random, statistics, sys
P=2147483033; Q=536857417; A=622683939; B=2147483024
G=(911976709,415929193); H=(180482573,1535800095)
II=392507391; LAM=390258842; SHIFT=969960860
ARMS=('source_bsgs','source_neg_rho','target_glv_rho')

def require(v,s):
    if not v:raise ValueError(s)

def ecadd(p,q,a,b):
    if p is None:return q
    if q is None:return p
    x,y=p;z,w=q
    if x==z and (y+w)%P==0:return None
    if p==q:
        require(y!=0,'unexpected order-two doubling')
        n=3*x*x+2*a*x+b;d=2*y
    else:n=w-y;d=z-x
    k=(n*pow(d%P,-1,P))%P
    x2=(k*k-a-x-z)%P
    return x2,(k*(x-x2)-y)%P

def scale(p,k,a,b):
    acc=None
    while k:
        if k&1:acc=ecadd(acc,p,a,b)
        p=ecadd(p,p,a,b);k>>=1
    return acc

def on(p,a,b):
    return p is None or (p[1]*p[1]-p[0]**3-a*p[0]**2-b*p[0])%P==0

def map2(p):
    if p is None:return None
    x,y=p;require(x!=0,'nonzero kernel source')
    iz=pow(x,-1,P)
    return (((x+A+B*iz)*pow(4,-1,P)+SHIFT)%P,
            y*(1-B*iz*iz)*pow(8,-1,P)%P)

def preflight():
    require(on(G,A,B) and on(H,0,9),'curve points')
    require(scale(G,Q,A,B) is None and scale(H,Q,0,9) is None,'group orders')
    require(map2(G)==H,'isogeny generator')
    require((II*II+1)%P==0 and (LAM*LAM+1)%Q==0,'roots of -1')
    require(scale(H,LAM,0,9)==((-H[0])%P,II*H[1]%P),'target automorphism')

def audit(path,expected_seed,count=64):
    raw=pathlib.Path(path).read_bytes()
    rows=list(csv.reader(raw.decode().splitlines()))
    require(rows[:3]==[['schema','ct135-fast-inversion-v1'],['seed',str(expected_seed)],['count',str(count)]],'headers')
    require(len(rows)==3+count*6+4,'record count')
    sums={a:0 for a in ARMS};per=[];knowns=set()
    for idx in range(count):
        segment=rows[3+idx*6:3+(idx+1)*6]
        order=list(ARMS)+list(ARMS[::-1]) if idx%2==0 else list(ARMS[::-1])+list(ARMS)
        public=None;known=None;perarm={a:0 for a in ARMS}
        for j,r in enumerate(segment):
            require(len(r)==13 and r[0]=='row' and int(r[1])==idx and r[2]==order[j],'row order')
            k,log,x,y,ns,adds,invs,steps,cycles,states=map(int,r[3:])
            require(0<k<Q and log==k,'known-answer scalar')
            require(0<=x<P and 0<=y<P and 0<ns<10**12,'coordinates and time')
            require(0<invs<=adds and steps>=0 and cycles>=0 and states>=0,'operation counters')
            if r[2]=='source_bsgs':require(states==23171 and cycles==23171 and steps<23171,'BSGS fresh table width')
            else:require(0<states<=steps<=1200000 and cycles<=steps,'rho scope')
            point=(x,y)
            require(on(point,A,B) and scale(G,log,A,B)==point,'source point/public output')
            require(map2(point)==scale(H,log,0,9),'isogeny and target output')
            if public is None:
                public=point;known=k
                require(k not in knowns,'distinct target');knowns.add(k)
            else:require(point==public and known==k,'same public input all arms')
            sums[r[2]]+=ns;perarm[r[2]]+=ns
        per.append(perarm)
    for j,arm in enumerate(ARMS):
        require(rows[3+6*count+j]==['total',arm,str(sums[arm])],f'{arm} aggregate')
    ratio=min(sums[ARMS[0]],sums[ARMS[1]])/sums[ARMS[2]]
    end=rows[-1]
    require(len(end)==2 and end[0]=='ratio_best_source_over_target' and abs(float(end[1])-ratio)<0.00001,'ratio')
    return {'seed':expected_seed,'sha256':hashlib.sha256(raw).hexdigest(),
            'sum_ns':sums,'ratio':ratio,'public_targets':len(knowns),'solves':6*count,'paired':per}

def sabotage(paths,seeds):
    good=pathlib.Path(paths[0]).read_text().splitlines()
    variants=[]
    def changed(line,col,value):
        x=list(good);v=x[line].split(',');v[col]=value;x[line]=','.join(v)
        variants.append('\n'.join(x)+'\n')
    changed(3,4,'0');changed(3,5,'0');changed(3,6,'0');changed(3,7,'0')
    changed(3,8,'0');changed(3,2,'target_glv_rho')
    changed(3+6,3,good[3].split(',')[3]);changed(3+6*64,2,'5')
    x=list(good);x.pop(9);variants.append('\n'.join(x)+'\n')
    failed=0
    for i,v in enumerate(variants):
        tmp=pathlib.Path(paths[0]).parent/'.ct135_sabotage.tmp'
        tmp.write_text(v)
        try:audit(tmp,seeds[0])
        except (ValueError,IndexError,TypeError,OverflowError):failed+=1
        finally:tmp.unlink(missing_ok=True)
    require(failed==len(variants),f'fail open: {failed}/{len(variants)}')
    return failed

if __name__=='__main__':
    paths=sys.argv[1:5]
    require(len(paths)==4,'need 4 panels')
    seeds=[int(pathlib.Path(p).stem) for p in paths]
    preflight()
    records=[audit(p,s) for p,s in zip(paths,seeds)]
    sums={a:sum(r['sum_ns'][a] for r in records) for a in ARMS}
    pairs=[p for r in records for p in r['paired']]
    rng=random.Random(0xC7135);bootstrap=[]
    for _ in range(1000):
        sample=[pairs[rng.randrange(len(pairs))] for _ in pairs]
        bootstrap.append(min(sum(x[ARMS[0]] for x in sample),sum(x[ARMS[1]] for x in sample))/sum(x[ARMS[2]] for x in sample))
    bootstrap.sort()
    output={'schema':'ct135-independent-arithmetic-audit-v1','standing':'[pcc:unverified]',
       'panels':[{k:v for k,v in r.items() if k!='paired'} for r in records],
       'total_solve_invocations':sum(r['solves'] for r in records),
       'pooled_best_tested_source_over_target':min(sums[ARMS[0]],sums[ARMS[1]])/sums[ARMS[2]],
       'descriptive_paired_bootstrap_95':[bootstrap[24],bootstrap[974]],
       'mutation_tests_rejected':sabotage(paths,seeds)}
    print(json.dumps(output,sort_keys=True,indent=2))
