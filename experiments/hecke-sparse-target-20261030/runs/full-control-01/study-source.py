"""Execute the four frozen correctness/relation studies; no wall-speed claims."""
import argparse
from collections import Counter
import hashlib
import json
from math import gcd,isqrt
from pathlib import Path
import platform
import random
import signal
import subprocess
import sys
import time

import flint
from flint import nmod_mat as Mat, fmpz
from modular import Curve,Field,Modular,cm_points

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from curve_identity import curve_identity


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def sparse_rank(rows,columns,p):
    pivots={}
    for row in rows:
        current={int(k):int(v)%p for k,v in row.items() if int(v)%p}
        assert all(0<=k<columns for k in current)
        while current:
            col=min(current)
            if col not in pivots:
                inv=pow(current[col],-1,p)
                pivots[col]={k:v*inv%p for k,v in current.items()}
                break
            mult=current[col]
            for k,v in pivots[col].items():
                z=(current.get(k,0)-mult*v)%p
                if z:current[k]=z
                else:current.pop(k,None)
    return len(pivots)


def reduced(rows,n,p):
    if not rows:return [],[]
    matrix=Mat([[row.get(j,0)%p for j in range(n)] for row in rows],p)
    rref,rank=matrix.rref()
    data=rref.tolist()[:rank]
    pivots=[next(i for i,v in enumerate(row) if v) for row in data]
    assert rank==sparse_rank(rows,n,p)
    return data,pivots


def row_for(points,coefficients,index):
    row={}
    for point,value in zip(points,coefficients):
        i=index[point];row[i]=row.get(i,0)+value
    return {k:v for k,v in row.items() if v}


def verify_rows(rows,points,curve):
    for row in rows:
        assert curve.total(curve.mul(v,points[int(k)]) for k,v in row.items()) is None


def collapse(points,rows,curve,fold):
    mapped=[];columns=[];index={}
    for point in points:
        if point is None:mapped.append(None);continue
        other=curve.neg(point)
        representative=min(point,other) if fold else point
        if representative not in index:
            index[representative]=len(columns);columns.append(representative)
        mapped.append((index[representative],1 if point==representative else -1))
    newrows=[]
    for row in rows:
        out={}
        for k,v in row.items():
            if mapped[int(k)] is not None:
                i,sign=mapped[int(k)];out[i]=out.get(i,0)+sign*v
        newrows.append({k:v for k,v in out.items() if v})
    verify_rows(newrows,columns,curve)
    return columns,newrows


def scalar_rows(points,curve):
    lookup={}
    for i,p in enumerate(points):lookup.setdefault(p,[]).append(i)
    rows=[];counts={}
    for m in (2,3):
        before=len(rows)
        for i,p in enumerate(points):
            for j in lookup.get(curve.mul(m,p),[]):
                row={j:1};row[i]=row.get(i,0)-m
                rows.append(row)
        counts[str(m)]=len(rows)-before
    verify_rows(rows,points,curve)
    return rows,counts


def select_field(threshold,f):
    c=39*f*f//4;v=max(2,isqrt(max(0,threshold-c)))
    if v%2:v+=1
    attempts=[]
    for _ in range(200):
        p=v*v+c
        if p<threshold or gcd(v,3 if f==6 else 15)!=1 or not fmpz(p).is_prime():
            attempts.append(dict(v=v,p=p,status='arithmetic_rejection'));v+=2;continue
        field=Field(p);N=field.curve_order();r=max(int(q) for q,e in fmpz(N).factor());h=N//r
        ok=r*20>=p and gcd(r,h)==1
        attempts.append(dict(v=v,p=p,N=N,r=r,h=h,status='selected' if ok else 'subgroup_rejection'))
        if ok:return p,v,N,r,h,field,attempts
        v+=2
    raise RuntimeError('field selector exhausted 200 candidates: '+json.dumps(attempts))


def public_point(curve,field,h,label):
    start=int.from_bytes(hashlib.sha256(label.encode()).digest(),'big')%field.p
    for offset in range(field.p):
        for point in field.lifts((start+offset)%field.p):
            q=curve.mul(h,point)
            if q is not None:return q
    raise AssertionError('nonzero projected point absent')


class BSGS:
    def __init__(self,curve,G,r):
        self.curve,self.G,self.r=curve,G,r
        self.m=isqrt(r)+1;self.table={};point=None
        for j in range(self.m):
            self.table.setdefault(point,j);point=curve.add(point,G)
        self.stride=curve.neg(point)

    def log(self,point):
        current=point
        for i in range(self.m+1):
            if current in self.table:
                k=(i*self.m+self.table[current])%self.r
                assert self.curve.mul(k,self.G)==point
                return k
            current=self.curve.add(current,self.stride)
        raise AssertionError('public point is not in declared cyclic subgroup')


def bootstrap(points,rows,curve,G,r,solver):
    rr,pivots=reduced(rows,len(points),r)
    free=[i for i in range(len(points)) if i not in pivots]
    start=curve.ops;logs=[0]*len(points)
    for i in free:logs[i]=solver.log(points[i])
    queries=curve.ops-start
    for row,pivot in zip(rr,pivots):logs[pivot]=-sum(int(row[i])*logs[i] for i in free)%r
    assert all(curve.mul(k,G)==point for k,point in zip(logs,points))
    return logs,dict(free_logs_solved_generically=len(free),rank=len(pivots),columns=len(points),
                     generic_query_group_additions_including_replay=queries,all_labels_replayed=True)


def target_query(points,logs,curve,G,Q,r):
    signed={}
    for point,log in zip(points,logs):
        signed[point]=log;signed[curve.neg(point)]=-log%r
    signed[None]=0
    values=list(signed.items());pairs={};start=curve.ops
    for i,(P,a) in enumerate(values):
        for R,b in values[i:]:pairs.setdefault(curve.add(P,R),(a+b)%r)
    setup=curve.ops-start;start=curve.ops;current=Q
    for shift in range(256):
        if current in pairs:
            answer=(pairs[current]-shift)%r
            assert curve.mul(answer,G)==Q
            return dict(status='verified',scalar=answer,attempts=shift+1,pair_entries=len(pairs),
                        pair_setup_group_additions=setup,query_group_additions_including_replay=curve.ops-start)
        current=curve.add(current,G)
    return dict(status='no_match_within_256',scalar=None,attempts=256,pair_entries=len(pairs),
                pair_setup_group_additions=setup,query_group_additions=curve.ops-start)


def collect_rows(modular,points,degrees,traces=False):
    index={P:i for i,P in enumerate(points)};rows=[];by_degree={};fibers=[];trace_rows=[];trace_points=list(points)
    trace_index=dict(index)
    for l in degrees:
        before=len(rows);patterns=Counter();complete=0;repeated=0
        for i,P in enumerate(points):
            fiber=modular.fiber(l,P,traces=traces)
            patterns[str(sorted(fiber['pattern']))]+=1
            if fiber['status']!='verified':repeated+=1;continue
            if fiber['complete']:
                complete+=1
                if all(q in index for q in fiber['rational']):
                    rows.append(row_for([P]+fiber['rational'],[-modular.a[l]]+[1]*len(fiber['rational']),index))
            if traces:
                for q in fiber['traces']:
                    if q not in trace_index:trace_index[q]=len(trace_points);trace_points.append(q)
                trace_rows.append(row_for([P]+fiber['traces'],[-modular.a[l]]+[1]*len(fiber['traces']),trace_index))
                fibers.append(dict(source_column=i,degree=l,**fiber))
        by_degree[str(l)]=dict(rows=len(rows)-before,complete_fibers=complete,repeated_x=repeated,
                              factor_patterns=dict(patterns))
    verify_rows(rows,points,modular.curve)
    return rows,by_degree,fibers,trace_points,trace_rows


def target_fibers(modular,Q,base,rows,h,r):
    curve=modular.curve;points=list(base);index={P:i for i,P in enumerate(points)}
    original=len(points);newrows=[];statuses=[]
    if Q not in index:index[Q]=len(points);points.append(Q)
    for l in (2,3):
        fiber=modular.fiber(l,Q)
        statuses.append(dict(degree=l,status=fiber['status'],complete=fiber.get('complete',False),pattern=fiber['pattern']))
        if not fiber.get('complete'):continue
        nbs=[curve.mul(h,P) for P in fiber['rational']]
        # Q is already in the r-subgroup; the fiber identity projects its source to [h]Q.
        for P in nbs:
            if P not in index:index[P]=len(points);points.append(P)
        newrows.append(row_for([Q]+nbs,[-modular.a[l]*h]+[1]*len(nbs),index))
    verify_rows(newrows,points,curve)
    folded,fold_rows=collapse(points,list(rows)+newrows,curve,True)
    old,oldrows=collapse(base,rows,curve,True)
    rank=len(reduced(fold_rows,len(folded),r)[1]);oldrank=len(reduced(oldrows,len(old),r)[1])
    return dict(fibers=statuses,new_original_columns=len(points)-original,
                effective_new_columns=len(folded)-len(old),new_rank=rank-oldrank,
                nullity_before=len(old)-oldrank,nullity_after=len(folded)-rank,
                relation_rows=newrows,points=points)


def run_field(threshold,f,richer):
    started=time.monotonic();p,v,N,r,h,field,selection=select_field(threshold,f)
    print('selected',f,p,N,r,h,flush=True)
    modular=Modular(p,[2,3,5,7] if richer and f==6 else [2,3,5] if f==30 else [2,3])
    curve=modular.curve;points,strata=cm_points(modular,field,f,2*v)
    degrees=[2,3,5] if f==30 else [2,3]
    rows,by_degree,_,_,_=collect_rows(modular,points,degrees)
    if f==30:
        smallrows,_,_,_,_=collect_rows(modular,points,[2,3])
    else:smallrows=rows
    projected=[curve.mul(h,P) for P in points]
    assert all(curve.mul(r,P) is None for P in projected)
    index={P:i for i,P in enumerate(points)}
    torsion=(16%p,-61%p)
    assert curve.mul(5,torsion) is None and curve.mul(h,torsion) is None
    al=[]
    for P in points:
        other=curve.add(curve.neg(P),torsion)
        assert other in index
        al.append(row_for([P,other],[1,1],index))
    verify_rows(rows+al,projected,curve)
    scalar,matches=scalar_rows(projected,curve)
    arms=[]
    for name,rr in [('hecke_23',smallrows),('hecke_all_degrees',rows),('atkin_only',al),
                    ('scalar_only',scalar),('hecke_atkin',rows+al),('all',rows+al+scalar)]:
        for stage,fold in [('original',None),('deduplicated',False),('negation_folded',True)]:
            cols,rewritten=(projected,rr) if fold is None else collapse(projected,rr,curve,fold)
            rank=len(reduced(rewritten,len(cols),r)[1])
            arms.append(dict(arm=name,stage=stage,columns=len(cols),rows=len(rr),rank=rank,nullity=len(cols)-rank))
    base,H=collapse(projected,rows+al+scalar,curve,True)
    genericbase,generic=collapse(projected,scalar,curve,True)
    assert base==genericbase
    G=None
    for x in range(p):
        for P in field.lifts(x):
            G=curve.mul(h,P)
            if G is not None:break
        if G is not None:break
    Q=public_point(curve,field,h,f'hecke-sparse-target-v1/{f}/{p}')
    assert curve.mul(r,G) is None and curve.mul(r,Q) is None
    field_record=dict(characteristic=p,degree=1,representation='prime',element_encoding='integer modulo characteristic')
    curve_record=dict(model='generalized Weierstrass',coefficients=[0,-1,1,-10,-20],curve_order=N,
                      subgroup_order=r,cofactor=h,generator=list(G),target_group='prime-order subgroup',trace=p+1-N)
    identity=curve_identity(field_record,curve_record,'x011')
    start=curve.ops;solver=BSGS(curve,G,r);bsgs_setup=curve.ops-start
    logs,boot=bootstrap(base,H,curve,G,r,solver)
    genericlogs,genericboot=bootstrap(base,generic,curve,G,r,solver)
    assert logs==genericlogs
    target=target_query(base,logs,curve,G,Q,r)
    start=curve.ops;reference=solver.log(Q);refops=curve.ops-start
    if target['scalar'] is not None:assert target['scalar']==reference
    targets=target_fibers(modular,Q,projected,rows+al,h,r)
    rand=[];randset=set()
    for counter in range(10000):
        P=public_point(curve,field,h,f'hecke-random-base-v1/{p}/{counter}')
        for q in (P,curve.neg(P)):
            if q not in randset:randset.add(q);rand.append(q)
        if len(rand)>=len(projected):break
    rand=rand[:len(projected)];randrows,randmatches=scalar_rows(rand,curve)
    randbase,randfold=collapse(rand,randrows,curve,True)
    random_control=dict(points=len(rand),scalar_matches=randmatches,effective_columns=len(randbase),
                        scalar_rank=len(reduced(randfold,len(randbase),r)[1]))
    rich=None
    if richer:
        _,richcounts,fibers,tracepoints,tracerows=collect_rows(modular,points,list(modular.degrees),traces=True)
        traceprojected=[curve.mul(h,P) for P in tracepoints]
        alltrace,tracefold=collapse(traceprojected,rows+al+tracerows,curve,True)
        rank=len(reduced(tracefold,len(alltrace),r)[1])
        oldrank=len(reduced(H,len(base),r)[1])
        rich=dict(degrees=richcounts,fibers=fibers,trace_points=tracepoints,trace_rows=tracerows,
                  effective_columns=len(alltrace),rank=rank,nullity=len(alltrace)-rank,
                  baseline_columns=len(base),baseline_rank=oldrank,baseline_nullity=len(base)-oldrank)
    return dict(status='verified_finite_diagnostic',f=f,p=p,v=v,N=N,r=r,h=h,selection=selection,
                identity=identity,field=field_record,curve=curve_record,public_target=Q,
                strata=strata,raw_points=points,raw_points_digest=digest(points),
                actual_projected_unique=len(set(projected)),projected_nonzero_unique=len(set(projected)-{None}),
                C=len(points),C_squared_over_r=len(points)**2/r,hecke_rows=rows,atkin_rows=al,
                degree_counts=by_degree,scalar_matches=matches,arms=arms,random_control=random_control,
                bootstrap=boot,generic_bootstrap=genericboot,normalized_base=base,base_logs=logs,
                bsgs_shared_setup_group_additions=bsgs_setup,target=target,
                generic_same_target=dict(scalar=reference,verified=True,query_group_additions_including_replay=refops),
                target_hecke=targets,richer=rich,total_group_additions=curve.ops,
                wall_seconds_diagnostic_only=time.monotonic()-started,performance_speedup=None)


def original_control():
    path=HERE.parent/'ecdlp-hecke-d39-holdout-20261026/data/exp11_class_walk_D39_f6.json'
    saved=json.loads(path.read_text());m=Modular(367,[2,3]);points,_=cm_points(m,Field(367),6,8)
    expected=[tuple(map(int,text.strip('()').split(' : ')[:2])) for text in saved['column_points']]
    assert points==expected
    rows,counts,fibers,_,_=collect_rows(m,points,[2,3],traces=True)
    normalized=lambda rr:sorted(tuple(sorted((int(k),int(v)) for k,v in row.items() if v)) for row in rr)
    assert normalized(rows)==normalized(saved['relation_rows'])
    assert len(reduced(rows,64,11)[1])==40
    return dict(status='verified',points=64,rows=len(rows),rank_mod_11=40,
                degrees=counts,explicit_trace_fibers_checked=len(fibers),source_sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--cell',choices=['control','f6-small','f6-medium','f6-large','f30'],required=True)
    args=parser.parse_args()
    subprocess.run(['bash','scripts/checkpoint.sh','gate'],cwd=ROOT,check=True)
    def alarm(*_):raise TimeoutError('600-second cell cap')
    signal.signal(signal.SIGALRM,alarm);signal.alarm(600)
    result={'control':original_control,'f6-small':lambda:run_field(10000,6,True),
            'f6-medium':lambda:run_field(100000,6,False),'f6-large':lambda:run_field(1000000,6,False),
            'f30':lambda:run_field(200000,30,True)}[args.cell]()
    result.update(cell=args.cell,python=sys.version,flint_version=flint.__version__,platform=platform.platform(),
                  source_hashes={name:hashlib.sha256((HERE/name).read_bytes()).hexdigest() for name in ['modular.py','study.py','PROTOCOL.md']})
    args.out.parent.mkdir(parents=True,exist_ok=True)
    with args.out.open('x') as output:output.write(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k in ['status','cell','p','r','C','bootstrap','generic_bootstrap','target','arms','explicit_trace_fibers_checked']},sort_keys=True),flush=True)


if __name__=='__main__':main()
