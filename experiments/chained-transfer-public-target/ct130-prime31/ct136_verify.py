#!/usr/bin/env python3
"""Independent arithmetic and sample auditor for CT136 five-arm cold ECDLP.
No C++ imports. Explicit checks survive -O; no signed PCC/execution attestation.
"""
import csv, hashlib, json, pathlib, random, statistics, sys
P = 2147483033
Q = 536857417
A, B = 622683939, 2147483024
G = (911976709,415929193)
H = (180482573,1535800095)
I, LAM, SHIFT = 392507391,390258842,969960860
ARMS = ('source_bsgs','source_neg_rho','target_glv_rho','source_batch32_rho','target_batch32_rho')
MASK = (1<<64)-1

def need(cond, reason):
    if not cond: raise ValueError(reason)

# Independent implementation of the standard C++ mt19937_64, used only to
# reconstruct the public scalar cohort; no dependence on C++ producer bytes.
class MT64:
    def __init__(self, seed):
        self.state=[seed&MASK]
        for idx in range(1,312):
            x=self.state[-1]
            self.state.append((6364136223846793005*(x^(x>>62))+idx)&MASK)
        self.idx=312
    def next(self):
        if self.idx==312:
            for i in range(312):
                x=(self.state[i]&0xffffffff80000000)|(self.state[(i+1)%312]&0x7fffffff)
                xa=x>>1
                if x&1: xa^=0xb5026f5aa96619e9
                self.state[i]=self.state[(i+156)%312]^xa
            self.idx=0
        y=self.state[self.idx];self.idx+=1
        y^=(y>>29)&0x5555555555555555
        y^=(y<<17)&0x71d67fffeda60000
        y^=(y<<37)&0xfff7eee000000000
        y^=y>>43
        return y&MASK

def ecadd(p,q,a,b):
    if p is None:return q
    if q is None:return p
    x,y=p;z,w=q
    if x==z and (y+w)%P==0:return None
    if p==q:
        need(y!=0,'cannot double order 2')
        n=3*x*x+2*a*x+b;d=2*y
    else:n=w-y;d=z-x
    slope=n*pow(d%P,-1,P)%P
    xx=(slope*slope-a-x-z)%P
    return xx,(slope*(x-xx)-y)%P

def mul_point(p,k,a,b):
    v=None
    while k:
        if k&1:v=ecadd(v,p,a,b)
        p=ecadd(p,p,a,b);k>>=1
    return v

def on(p,a,b):
    return p is None or (p[1]**2-p[0]**3-a*p[0]**2-b*p[0])%P==0

def map2(p):
    if p is None:return None
    x,y=p;need(x!=0,'kernel input')
    invx=pow(x,-1,P)
    return (((x+A+B*invx)*pow(4,-1,P)+SHIFT)%P, y*(1-B*invx*invx)*pow(8,-1,P)%P)

def preflight():
    need(on(G,A,B) and on(H,0,9),'on curve')
    need(mul_point(G,Q,A,B) is None and mul_point(H,Q,0,9) is None,'order')
    need(map2(G)==H,'isogeny G')
    need((I*I+1)%P==0 and (LAM*LAM+1)%Q==0,'GLV roots')
    need(mul_point(H,LAM,0,9)==((-H[0])%P,I*H[1]%P),'GLV action')
    # Independent standard-engine sanity vector, scalar k=1 maps to G.
    need(mul_point(G,1,A,B)==G,'identity scalar')

def audit(path,seed,count=64):
    raw=pathlib.Path(path).read_bytes()
    rows=list(csv.reader(raw.decode('utf-8').splitlines()))
    need(rows[:3]==[['schema','ct136-batched-cold-v1'],['seed',str(seed)],['count',str(count)]],'header')
    need(len(rows)==3+10*count+7,'complete record count')
    sums={arm:0 for arm in ARMS};per=[];seen=set()
    rng=MT64(seed)
    for ix in range(count):
        k_expected=Q//8+rng.next()%(Q-Q//8-1)
        need(k_expected not in seen,'duplicate target')
        seen.add(k_expected)
        exp_public=mul_point(G,k_expected,A,B)
        exp_map=mul_point(H,k_expected,0,9)
        need(exp_map==map2(exp_public),'public source-target map')
        order=list(ARMS)+list(ARMS[::-1]) if ix%2==0 else list(ARMS[::-1])+list(ARMS)
        seg=rows[3+10*ix:3+10*(ix+1)]
        p_sums={arm:0 for arm in ARMS}
        arm_signatures={}
        for j,r in enumerate(seg):
            need(len(r)==14 and r[0]=='row' and int(r[1])==ix and r[2]==order[j],'row order/schema')
            k,log,x,y,ns,adds,field_inv,scalar_inv,iters,cycles,states=map(int,r[3:])
            need(k==k_expected and log==k_expected,'unexpected target or answer')
            need((x,y)==exp_public,'public source point')
            need(0<ns<1000000000000,'timing')
            need(adds>0 and 0<field_inv<=adds+2,'field inverse counter')
            need(0<=scalar_inv<=6 and 0<=iters<=1200000 and 0<=cycles<=1200000,'counters')
            if r[2]=='source_bsgs':
                need(scalar_inv==0 and states==23171 and cycles==23171 and iters<=23171,'BSGS fresh table')
            else:
                need(scalar_inv>=1 and 0<states<=iters and cycles<=iters,'rho scope')
            sig=(adds,field_inv,scalar_inv,iters,cycles,states)
            if r[2] in arm_signatures: need(sig==arm_signatures[r[2]],'non-reproducible duplicate cold arm')
            else: arm_signatures[r[2]]=sig
            sums[r[2]]+=ns;p_sums[r[2]]+=ns
        per.append(p_sums)
    for j,arm in enumerate(ARMS):
        need(rows[3+10*count+j]==['total',arm,str(sums[arm])],'aggregate '+arm)
    best_s=min(sums[a] for a in (ARMS[0],ARMS[1],ARMS[3]))
    best_t=min(sums[a] for a in (ARMS[2],ARMS[4]))
    ratio=best_s/best_t
    need(rows[-2][0]=='ratio_best_source_over_best_target' and len(rows[-2])==2 and
         abs(float(rows[-2][1])-ratio)<0.00002,'best ratio')
    bratio=sums[ARMS[3]]/sums[ARMS[4]]
    need(rows[-1][0]=='ratio_source_batch_over_target_batch' and len(rows[-1])==2 and
         abs(float(rows[-1][1])-bratio)<0.00002,'batch ratio')
    return {'seed':seed,'sha256':hashlib.sha256(raw).hexdigest(),'targets':len(seen),
        'solves':10*count,'ns':sums,'best_source_over_best_target':ratio,
        'batch_source_over_batch_target':bratio,'paired':per}

def sabotage(path,seed,count=64):
    original=pathlib.Path(path).read_text().splitlines()
    mutated=[]
    def corrupt(line,column,content):
        a=list(original);v=a[line].split(',');v[column]=str(content);a[line]=','.join(v)
        mutated.append('\n'.join(a)+'\n')
    corrupt(3,3,'0');corrupt(3,4,'0');corrupt(3,5,'0')
    corrupt(3,7,'0');corrupt(3,8,'0');corrupt(3,9,'0')
    corrupt(3,2,'target_glv_rho')
    corrupt(3+10,3,original[3].split(',')[3]) # duplicate k for next public Q
    corrupt(3+10*count,2,'5')
    corrupt(len(original)-1,1,'0.0')
    v=list(original);v.pop(17);mutated.append('\n'.join(v)+'\n')
    invalid=0
    tmp=pathlib.Path(path).with_suffix('.sabotage.tmp')
    try:
        for v in mutated:
            tmp.write_text(v)
            try:audit(tmp,seed,count)
            except (ValueError, IndexError, TypeError, OverflowError, ZeroDivisionError): invalid+=1
        need(invalid==len(mutated),f'mutation accepted {len(mutated)-invalid}/{len(mutated)}')
    finally:tmp.unlink(missing_ok=True)
    return invalid

if __name__=='__main__':
    paths=sys.argv[1:5]
    need(len(paths)==4,'four frozen panels required')
    seeds=[int(pathlib.Path(path).stem) for path in paths]
    need(seeds==[20261230,20261231,20261232,20261233],'fixed holdout seeds')
    preflight()
    reports=[audit(p,s) for p,s in zip(paths,seeds)]
    total={arm:sum(row['ns'][arm] for row in reports) for arm in ARMS}
    pairs=[v for row in reports for v in row['paired']]
    rng=random.Random(136);boots=[]
    for _ in range(1000):
        sample=[pairs[rng.randrange(len(pairs))] for __ in pairs]
        s=min(sum(v[a] for v in sample) for a in (ARMS[0],ARMS[1],ARMS[3]))
        t=min(sum(v[a] for v in sample) for a in (ARMS[2],ARMS[4]))
        boots.append(s/t)
    boots.sort()
    output={'schema':'ct136-independent-arithmetic-v1','standing':'[pcc:unverified]',
        'panels':[{k:v for k,v in p.items() if k!='paired'} for p in reports],
        'solves':sum(x['solves'] for x in reports),'all_ns':total,
        'pooled_best_source_over_best_target':min(total[a] for a in (ARMS[0],ARMS[1],ARMS[3]))/
                                          min(total[a] for a in (ARMS[2],ARMS[4])),
        'paired_bootstrap_descriptive_95':[boots[24],boots[974]],
        'mutations_rejected':sabotage(paths[0],seeds[0])}
    print(json.dumps(output,sort_keys=True,indent=2))
