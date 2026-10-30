"""Reuse signed pair-index collisions as certified base-log relations."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import time

from modular import Curve
from study import BSGS,bootstrap,collapse,reduced,scalar_rows
from verify import ShortCurve,rank as independent_rank

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
CELLS=('f6-small-01','f6-medium-01','f6-large-01','f30-01')


def point_key(point):
    return (-1,-1) if point is None else point


def combine(left,right,multiplier=1):
    row=dict(left)
    for k,v in right.items():
        row[k]=row.get(k,0)+multiplier*v
        if not row[k]:row.pop(k)
    return row


class Basis:
    def __init__(self,p):
        self.p=p
        self.pivots={}

    def add(self,row):
        current={int(k):int(v)%self.p for k,v in row.items() if int(v)%self.p}
        while current:
            col=min(current)
            if col not in self.pivots:
                inv=pow(current[col],-1,self.p)
                self.pivots[col]={k:v*inv%self.p for k,v in current.items()}
                return True
            scale=current[col]
            for k,v in self.pivots[col].items():
                value=(current.get(k,0)-scale*v)%self.p
                if value:current[k]=value
                else:current.pop(k,None)
        return False


def signed_basis(base,curve):
    signed={}
    for i,P in enumerate(base):
        signed[P]={i:1}
        signed[curve.neg(P)]={i:-1}
    signed[None]={}
    return list(signed.items())


def harvest(base,curve,r):
    """Uses no input point logs; preserves original target_query pair order."""
    values=signed_basis(base,curve)
    index={};basis=Basis(r);rows=[];certificates=[]
    stream=hashlib.sha256();collisions=0;zero_identities=0
    start=curve.ops;wall=time.monotonic();cpu=time.process_time()
    for i,(P,expression) in enumerate(values):
        for j in range(i,len(values)):
            Q,right=values[j]
            point=curve.add(P,Q)
            stream.update(json.dumps([i,j,point],separators=(',',':')).encode()+b'\n')
            result=combine(expression,right)
            if point not in index:
                index[point]=(result,(i,j))
                continue
            first,first_pair=index[point]
            row=combine(result,first,-1)
            collisions+=1
            if not row:
                zero_identities+=1
                continue
            # A nonzero actual point-log vector bounds valid relation rank by n-1.
            if len(basis.pivots)<len(base)-1 and basis.add(row):
                rows.append(row)
                certificates.append(dict(pair=[i,j],first_pair=list(first_pair),row=row))
    construction=curve.ops-start
    assert construction==len(values)*(len(values)+1)//2
    result=dict(signed_points=[P for P,_ in values],pair_entries=len(index),
                pair_construction_group_additions=construction,collisions=collisions,
                coefficient_zero_identities=zero_identities,nonzero_collision_rows=collisions-zero_identities,
                independent_collision_rank=len(rows),basis_rows=rows,basis_witnesses=certificates,
                stream_sha256=stream.hexdigest(),
                pair_points_digest=hashlib.sha256(json.dumps(sorted(index,key=point_key)).encode()).hexdigest(),
                wall_seconds_diagnostic=time.monotonic()-wall,cpu_seconds_diagnostic=time.process_time()-cpu)
    return index,result


def check_index(base,r,stats,p):
    """Re-enumerate all pairs with separate short-model arithmetic and rank."""
    curve=ShortCurve(p)
    signed=[None if P is None else tuple(P) for P in stats['signed_points']]
    expressions=[]
    for P in signed:
        if P is None:expressions.append({});continue
        if P in base:expressions.append({base.index(P):1})
        else:
            negative=(P[0],(-P[1]-1)%p)
            assert negative in base
            expressions.append({base.index(negative):-1})
    converted=[curve.point(P) for P in signed]
    index={};all_rows=[];stream=hashlib.sha256()
    for i,P in enumerate(converted):
        for j in range(i,len(converted)):
            point=curve.plus(P,converted[j])
            original=curve.original(point)
            stream.update(json.dumps([i,j,original],separators=(',',':')).encode()+b'\n')
            expression=combine(expressions[i],expressions[j])
            if point in index:
                row=combine(expression,index[point],-1)
                if row:all_rows.append(row)
            else:index[point]=expression
    assert stream.hexdigest()==stats['stream_sha256']
    assert len(index)==stats['pair_entries']
    assert len(all_rows)==stats['nonzero_collision_rows']
    basis=[{int(k):v for k,v in row.items()} for row in stats['basis_rows']]
    rank=independent_rank(all_rows,len(base),r)
    assert rank==independent_rank(basis,len(base),r)==stats['independent_collision_rank']
    curve.rows(basis,[curve.point(P) for P in base])
    for witness in stats['basis_witnesses']:
        a,b=witness['pair'];c,d=witness['first_pair']
        assert curve.plus(converted[a],converted[b])==curve.plus(converted[c],converted[d])
        row=combine(combine(expressions[a],expressions[b]),combine(expressions[c],expressions[d]),-1)
        assert row=={int(k):v for k,v in witness['row'].items()}
    return dict(status='independently_verified',all_pairs_checked=len(signed)*(len(signed)+1)//2,
                all_nonzero_collision_rows_checked=len(all_rows),collision_rank=rank)


def target_from_index(index,logs,curve,G,Q,r):
    start=curve.ops;current=Q
    for shift in range(256):
        if current in index:
            expression,_=index[current]
            scalar=(sum(v*logs[k] for k,v in expression.items())-shift)%r
            assert curve.mul(scalar,G)==Q
            return dict(status='verified',scalar=scalar,attempts=shift+1,
                        query_group_additions_including_replay=curve.ops-start)
        current=curve.add(current,G)
    return dict(status='no_match_within_256',scalar=None,attempts=256,
                query_group_additions=curve.ops-start)


def run_cell(cell):
    source=HERE/'runs'/cell/'receipt.json';data=json.loads(source.read_text())
    p,r,h=data['p'],data['r'],data['h'];curve=Curve(p)
    base=[tuple(P) for P in data['normalized_base']]
    projected=[curve.mul(h,tuple(P)) for P in data['raw_points']]
    original=[{int(k):v for k,v in row.items()} for row in data['hecke_rows']+data['atkin_rows']]
    scalar,_=scalar_rows(projected,curve)
    columns,hecke=collapse(projected,original+scalar,curve,True)
    assert columns==base
    index,stats=harvest(base,curve,r)
    collisions=stats['basis_rows']
    generic_rank=len(reduced(collisions,len(base),r)[1])
    old_rank=len(reduced(hecke,len(base),r)[1])
    combined_rank=len(reduced(hecke+collisions,len(base),r)[1])
    assert generic_rank==stats['independent_collision_rank']
    _,scalar_folded=collapse(projected,scalar,curve,True)
    assert len(reduced(collisions+scalar_folded,len(base),r)[1])==generic_rank
    independent=check_index(base,r,stats,p)
    assert independent_rank(hecke+collisions,len(base),r)==combined_rank
    if cell=='f6-large-01':
        old=json.loads((HERE/'runs/arity-01/receipt.json').read_text())
        assert old['pair_points_digest']==stats['pair_points_digest']
    G=tuple(data['curve']['generator']);Q=tuple(data['public_target'])
    start=curve.ops;solver=BSGS(curve,G,r);setup=curve.ops-start
    short=ShortCurve(p);shortG=short.point(G);shortQ=short.point(Q)
    arms=[]
    for name,rows in [('previous_hecke',hecke),('generic_pair_reuse',collisions),
                       ('hecke_pair_reuse',hecke+collisions)]:
        start=time.monotonic();cpu=time.process_time()
        logs,bootstrap_info=bootstrap(base,rows,curve,G,r,solver)
        assert logs==data['base_logs']
        assert all(short.times(k,shortG)==short.point(P) for k,P in zip(logs,base))
        elapsed=time.monotonic()-start;cpu_elapsed=time.process_time()-cpu
        target=target_from_index(index,logs,curve,G,Q,r)
        assert target['status']==data['target']['status']
        if target['scalar'] is not None:
            assert target['scalar']==data['target']['scalar']
            assert short.times(target['scalar'],shortG)==shortQ
        arms.append(dict(arm=name,**bootstrap_info,target=target,
                         label_preparation_wall_seconds_diagnostic=elapsed,
                         label_preparation_cpu_seconds_diagnostic=cpu_elapsed))
    return dict(status='verified_finite_pair_reuse',cell=cell,p=p,r=r,columns=len(base),
                identity=data['identity'],input_receipt_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                index=stats,independent=independent,previous_hecke_rank=old_rank,
                generic_pair_rank=generic_rank,combined_rank=combined_rank,
                marginal_hecke_rank_over_pair_control=combined_rank-generic_rank,
                previous_free_logs=len(base)-old_rank,new_free_logs=len(base)-combined_rank,
                shared_bsgs_setup_group_additions=setup,arms=arms,
                same_total_budget_advantage='not established; geometric and bookkeeping costs not fully priced',
                performance_speedup=None)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cell',choices=CELLS,required=True)
    parser.add_argument('--out',type=Path,required=True);args=parser.parse_args()
    subprocess.run(['bash','scripts/checkpoint.sh','gate'],cwd=ROOT,check=True)
    result=run_cell(args.cell)
    result['source_hashes']={name:hashlib.sha256((HERE/name).read_bytes()).hexdigest()
                             for name in ['pair_reuse.py','PAIR_REUSE_PROTOCOL.md','study.py','verify.py','modular.py']}
    args.out.parent.mkdir(parents=True,exist_ok=True)
    with args.out.open('x') as output:output.write(json.dumps(result,indent=2,sort_keys=True)+'\n')
    summary={k:v for k,v in result.items() if k not in ['index','arms','source_hashes','identity']}
    summary['arms']=[{k:v for k,v in arm.items() if not k.endswith('_diagnostic')} for arm in result['arms']]
    print(json.dumps(summary,sort_keys=True),flush=True)


if __name__=='__main__':main()
