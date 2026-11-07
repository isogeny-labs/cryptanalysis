"""Known-representation factor bases, built without knowing log_P(Q).

The degree-five family uses six uniform labeled seed points and forward
differences. It is six-wise independent at distinct indices modulo r.
"""
from itertools import combinations,product
from math import comb
from pathlib import Path
import sys
import time

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from core import canonical


def random_label(E,P,Q,r,rng):
    u,v=rng.randrange(r),rng.randrange(r)
    return E.add(E.mul(u,P),E.mul(v,Q)),u,v


class WindowSampler:
    """Exact independent uniform points Q+[u]P, with labels (u,1).

    Fixed-base tables are built once per DLP and reused across failed
    bases. At cube-root base sizes their group-operation setup and
    sampling cost is linear with suitable window size.
    """
    def __init__(self,E,P,Q,r,width=4):
        cpu=time.process_time();wall=time.perf_counter()
        self.E,self.r,self.width=E,r,width
        self.radix=1<<width;self.tables=[]
        point=P
        positions=(r.bit_length()+width-1)//width
        for j in range(positions):
            table=[None]
            for digit in range(1,self.radix):table.append(E.add(table[-1],point))
            self.tables.append(table)
            if j+1<positions:point=E.mul(self.radix,point)
        self.tables[0]=[E.add(T,Q) for T in self.tables[0]]
        self.stored_points=sum(len(table) for table in self.tables)
        self.cpu_s=time.process_time()-cpu;self.wall_s=time.perf_counter()-wall

    def sample(self,rng):
        u=rng.randrange(self.r);value=u
        point=self.tables[0][value&(self.radix-1)];value>>=self.width
        for table in self.tables[1:]:
            point=self.E.add(point,table[value&(self.radix-1)])
            value>>=self.width
        assert value==0
        return point,u,1


def stirling(n,k):
    if n==k==0:return 1
    if not n or not k:return 0
    return k*stirling(n-1,k)+stirling(n-1,k-1)


def normalize(E,point,u,v,r):
    if point is None:return None,u%r,v%r
    if point[1]>E.p-point[1]:return E.neg(point),-u%r,-v%r
    return point,u%r,v%r


def build(E,P,Q,r,B,rng,kind='moment5',sampler=None):
    start=time.perf_counter();cpu=time.process_time()
    entries={};construction_relation=None
    all_points=[];seeds=[]
    def insert(point,u,v,index):
        nonlocal construction_relation
        point,u,v=normalize(E,point,u,v,r)
        all_points.append({'index':index,'point':point,'u':u,'v':v})
        if point is None:
            if v:construction_relation=(-u*pow(v,-1,r)%r)
            return
        x=point[0]
        if x in entries:
            old=entries[x]
            dv=(v-old['v'])%r;du=(u-old['u'])%r
            if dv:construction_relation=-du*pow(dv,-1,r)%r
        else:entries[x]={'point':point,'u':u,'v':v,'index':index}
    if kind=='windowed':
        assert sampler is not None
        for index in range(B):insert(*sampler.sample(rng),index)
    elif kind=='random':
        for index in range(B):insert(*random_label(E,P,Q,r,rng),index)
    elif kind in ['moment1','moment5']:
        degree=int(kind[-1])
        seeds=[random_label(E,P,Q,r,rng) for _ in range(degree+1)]
        differences=[]
        factorial=1
        for k in range(degree+1):
            if k:factorial*=k
            point=None;u=v=0
            for j in range(k,degree+1):
                coefficient=factorial*stirling(j,k)
                if coefficient:
                    point=E.add(point,E.mul(coefficient,seeds[j][0]))
                    u=(u+coefficient*seeds[j][1])%r
                    v=(v+coefficient*seeds[j][2])%r
            differences.append((point,u,v))
        for index in range(B):
            insert(*differences[0],index)
            for j in range(degree):
                point,u,v=differences[j];nextpoint,nu,nv=differences[j+1]
                differences[j]=(E.add(point,nextpoint),(u+nu)%r,(v+nv)%r)
    else:raise ValueError(kind)
    return {'entries':entries,'seeds':seeds,'vertices':all_points,
            'construction_relation':construction_relation,
            'wall_s':time.perf_counter()-start,'cpu_s':time.process_time()-cpu}


def first_relation(E,P,Q,r,base):
    """Find one useful signed triple, and verify the recovered logarithm."""
    start=time.perf_counter();cpu=time.process_time()
    if base['construction_relation'] is not None:
        d=base['construction_relation']
        assert E.mul(d,P)==Q
        return {'success':True,'source':'construction','logarithm':d,
                'wall_s':time.perf_counter()-start,'cpu_s':time.process_time()-cpu,
                'pair_tests':0,'witness':None}
    entries=list(base['entries'].values())
    lookup={entry['point'][0]:entry for entry in entries}
    tests=0
    for left,right in combinations(entries,2):
        # Quotient by simultaneous sign reversal: keep left sign positive.
        for sign in [1,-1]:
            tests+=1
            point=E.neg(E.add(left['point'],right['point'] if sign==1 else E.neg(right['point'])))
            if point is None or point[0] not in lookup:continue
            last=lookup[point[0]]
            if last['point'][0] in [left['point'][0],right['point'][0]]:continue
            sign_last=1 if point==last['point'] else -1
            u=(left['u']+sign*right['u']+sign_last*last['u'])%r
            v=(left['v']+sign*right['v']+sign_last*last['v'])%r
            if not v:continue
            d=-u*pow(v,-1,r)%r
            assert E.mul(d,P)==Q
            witness={'indices':[left['index'],right['index'],last['index']],
                     'signs':[1,sign,sign_last],
                     'points':[left['point'],right['point'],last['point']],
                     'u_sum':u,'v_sum':v}
            return {'success':True,'source':'triple','logarithm':d,
                    'wall_s':time.perf_counter()-start,'cpu_s':time.process_time()-cpu,
                    'pair_tests':tests,'witness':witness}
    return {'success':False,'source':None,'logarithm':None,
            'wall_s':time.perf_counter()-start,'cpu_s':time.process_time()-cpu,
            'pair_tests':tests,'witness':None}


def lower_bound(r,B):
    M=4*comb(B,3)
    return M/(r+M-1)-B*B/r-M/(r*r)
