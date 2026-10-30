"""Separate short-Weierstrass arithmetic verifier of retained finite receipts."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import numpy as np

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]


class ShortCurve:
    def __init__(self,p):
        self.p=p;self.a=-31*pow(3,-1,p)%p;self.b=-2501*pow(108,-1,p)%p

    def point(self,P):
        if P is None:return None
        x,y=P
        assert 0<=x<self.p and 0<=y<self.p
        X,Y=(x-pow(3,-1,self.p))%self.p,(y+pow(2,-1,self.p))%self.p
        assert (Y*Y-X**3-self.a*X-self.b)%self.p==0
        return X,Y

    def original(self,P):
        return None if P is None else ((P[0]+pow(3,-1,self.p))%self.p,(P[1]-pow(2,-1,self.p))%self.p)

    def neg(self,P):return None if P is None else (P[0],-P[1]%self.p)

    def plus(self,P,Q):
        if P is None:return Q
        if Q is None:return P
        x,y=P;u,v=Q
        if x==u and (y+v)%self.p==0:return None
        slope=((3*x*x+self.a)*pow(2*y%self.p,-1,self.p) if P==Q else
               (v-y)*pow((u-x)%self.p,-1,self.p))%self.p
        X=(slope*slope-x-u)%self.p;Y=(slope*(x-X)-y)%self.p
        assert (Y*Y-X**3-self.a*X-self.b)%self.p==0
        return X,Y

    def times(self,k,P):
        if k<0:return self.times(-k,self.neg(P))
        # Left-to-right ladder, separate from producer's right-to-left implementation.
        Q=None
        for bit in bin(k)[2:]:
            Q=self.plus(Q,Q)
            if bit=='1':Q=self.plus(Q,P)
        return Q

    def rows(self,rows,points):
        for row in rows:
            result=None
            for i,value in row.items():result=self.plus(result,self.times(value,points[int(i)]))
            assert result is None


def rank(rows,n,p):
    if not rows or not n:return 0
    M=np.array([[row.get(j,0)%p for j in range(n)] for row in rows],dtype=np.int64)
    pivot=0
    for col in range(n):
        indices=np.flatnonzero(M[pivot:,col])
        if not len(indices):continue
        i=pivot+int(indices[0]);M[[i,pivot]]=M[[pivot,i]]
        M[pivot]=M[pivot]*pow(int(M[pivot,col]),-1,p)%p
        others=np.flatnonzero(M[:,col]);others=others[others!=pivot]
        M[others]=(M[others]-M[others,col,None]*M[pivot])%p
        pivot+=1
        if pivot==len(M):break
    return pivot


def fold(points,rows,curve):
    columns=[];lookup={};mapped=[]
    for P in points:
        if P is None:mapped.append(None);continue
        original=curve.original(P);negative=curve.original(curve.neg(P))
        rep=min(original,negative)
        if rep not in lookup:lookup[rep]=len(columns);columns.append(rep)
        mapped.append((lookup[rep],1 if original==rep else -1))
    rewritten=[]
    for row in rows:
        out={}
        for k,value in row.items():
            entry=mapped[int(k)]
            if entry is not None:
                i,sign=entry;out[i]=out.get(i,0)+sign*value
        rewritten.append({k:v for k,v in out.items() if v})
    return columns,rewritten


def verify(path):
    r=json.loads(path.read_text());curve=ShortCurve(r['p'])
    raw=[curve.point(P) for P in r['raw_points']]
    curve.rows(r['hecke_rows'],raw)
    projected=[curve.times(r['h'],P) for P in raw]
    curve.rows(r['atkin_rows'],projected)
    G=curve.point(r['curve']['generator']);Q=curve.point(r['public_target'])
    assert G is not None and Q is not None
    assert curve.times(r['r'],G) is None and curve.times(r['r'],Q) is None
    base=[curve.point(P) for P in r['normalized_base']]
    assert all(curve.times(log,G)==P for log,P in zip(r['base_logs'],base))
    assert curve.times(r['generic_same_target']['scalar'],G)==Q
    if r['target']['scalar'] is not None:assert curve.times(r['target']['scalar'],G)==Q
    lookup={};scalar=[]
    for i,P in enumerate(projected):lookup.setdefault(P,[]).append(i)
    for m in (2,3):
        for i,P in enumerate(projected):
            for j in lookup.get(curve.times(m,P),[]):
                row={j:1};row[i]=row.get(i,0)-m;scalar.append(row)
    rawrows=[{int(k):v for k,v in row.items()} for row in r['hecke_rows']+r['atkin_rows']]+scalar
    original,oldrows=fold(projected,rawrows,curve)
    oldrank=rank(oldrows,len(original),r['r'])
    assert original==[tuple(P) for P in r['normalized_base']]
    assert oldrank==r['bootstrap']['rank']
    rich=None
    if r['richer']:
        richer=r['richer']
        tracepoints=[curve.point(P) for P in richer['trace_points']]
        curve.rows(richer['trace_rows'],tracepoints)
        traceprojected=[curve.times(r['h'],P) for P in tracepoints]
        tracerows=[{int(k):v for k,v in row.items()} for row in richer['trace_rows']]
        extended,allrows=fold(traceprojected,rawrows+tracerows,curve)
        assert extended[:len(original)]==original
        fullrank=rank(allrows,len(extended),r['r'])
        assert fullrank==richer['rank']
        newonly=[{k-len(original):v for k,v in row.items() if k>=len(original)} for row in allrows]
        newrank=rank(newonly,len(extended)-len(original),r['r'])
        projected_rank=fullrank-newrank
        rich=dict(total_columns=len(extended),full_rank=fullrank,new_column_block_rank=newrank,
                  rank_of_constraints_on_original_columns=projected_rank,
                  extra_independent_constraints_on_original=projected_rank-oldrank,
                  residual_nullity_on_original=len(original)-projected_rank,
                  trace_rows_checked=len(tracerows))
    return dict(path=str(path.relative_to(ROOT)),p=r['p'],r=r['r'],status='independently_verified',
                base_labels_checked=len(base),target_scalar_verified=True,
                natural_target_status=r['target']['status'],effective_rank=oldrank,richer=rich,
                receipt_sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True);args=parser.parse_args()
    subprocess.run(['bash','scripts/checkpoint.sh','gate'],cwd=ROOT,check=True)
    results=[]
    for cell in ['f6-small-01','f6-medium-01','f6-large-01','f30-01']:
        path=HERE/'runs'/cell/'receipt.json'
        results.append(verify(path));print(json.dumps(results[-1],sort_keys=True),flush=True)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    with args.out.open('x') as output:output.write(json.dumps(dict(status='verified',results=results),indent=2)+'\n')


if __name__=='__main__':main()
