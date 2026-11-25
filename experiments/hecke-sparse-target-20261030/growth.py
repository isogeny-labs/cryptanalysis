"""Execute the prespecified known-label trace-growth follow-up."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

from modular import Modular
from study import collect_rows,collapse,reduced,scalar_rows,target_query
from verify import ShortCurve

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    subprocess.run(['bash','scripts/checkpoint.sh','gate'],cwd=ROOT,check=True)
    prior=HERE/'runs/f6-large-01/receipt.json';saved=json.loads(prior.read_text())
    p,r,h=saved['p'],saved['r'],saved['h']
    assert (p,r,h)==(1032607,206477,5)
    modular=Modular(p,[2,3,5,7]);curve=modular.curve
    points=[tuple(P) for P in saved['raw_points']]
    G=tuple(saved['curve']['generator']);Q=tuple(saved['public_target'])
    projected=[curve.mul(h,P) for P in points]
    known={}
    for P,k in zip(saved['normalized_base'],saved['base_logs']):
        P=tuple(P);known[P]=k;known[curve.neg(P)]=-k%r
    known[None]=0
    _,counts,fibers,tracepoints,tracerows=collect_rows(modular,points,[2,3,5,7],traces=True)
    grown=dict(known);eligible=0;skipped=0;derivation_ops=0
    derivations=[]
    for fiber in fibers:
        nonlinear=[i for i,d in enumerate(fiber['pattern']) if d>1]
        if len(nonlinear)!=1:skipped+=1;continue
        source=projected[fiber['source_column']]
        rational=[curve.mul(h,tuple(P)) for P in fiber['rational']]
        if source not in known or any(P not in known for P in rational):skipped+=1;continue
        start=curve.ops
        result=curve.mul(modular.a[fiber['degree']],source)
        label=modular.a[fiber['degree']]*known[source]%r
        for P in rational:
            result=curve.add(result,curve.neg(P));label=(label-known[P])%r
        derivation_ops+=curve.ops-start
        trace=fiber['traces'][nonlinear[0]]
        actual=curve.mul(h,None if trace is None else tuple(trace))
        assert result==actual and curve.mul(label,G)==result
        if result in grown:assert grown[result]==label
        grown[result]=label;grown[curve.neg(result)]=-label%r
        eligible+=1
        derivations.append(dict(source=fiber['source_column'],degree=fiber['degree'],point=result,label=label))
    seed=sorted((P,k) for P,k in known.items() if P is not None)
    generic=dict(known)
    for i in range(derivation_ops):
        data=hashlib.sha256(('generic-growth-v1/'+str(i)).encode()).digest()
        P,a=seed[int.from_bytes(data[:16],'big')%len(seed)]
        R,b=seed[int.from_bytes(data[16:],'big')%len(seed)]
        point=curve.add(P,R);label=(a+b)%r
        if point in generic:assert generic[point]==label
        generic[point]=label;generic[curve.neg(point)]=-label%r
    short=ShortCurve(p);shortG=short.point(G);shortQ=short.point(Q)
    arms=[]
    for name,labels in [('original',known),('trace_growth',grown),('generic_growth',generic)]:
        nonzero=sorted((P,k) for P,k in labels.items() if P is not None)
        assert all(short.times(k,shortG)==short.point(P) for P,k in nonzero)
        result=target_query([P for P,k in nonzero],[k for P,k in nonzero],curve,G,Q,r)
        if result['scalar'] is not None:assert short.times(result['scalar'],shortG)==shortQ
        arms.append(dict(arm=name,known_points_including_zero=len(labels),labels_replayed=len(nonzero),
                         points=[P for P,k in nonzero],logs=[k for P,k in nonzero],target=result))
    scalar,_=scalar_rows(projected,curve)
    rows=[{int(k):v for k,v in row.items()} for row in saved['hecke_rows']+saved['atkin_rows']]+scalar
    base,oldrows=collapse(projected,rows,curve,True)
    traceprojected=[curve.mul(h,P) for P in tracepoints]
    full,allrows=collapse(traceprojected,rows+tracerows,curve,True)
    assert full[:len(base)]==base
    fullrank=len(reduced(allrows,len(full),r)[1])
    newrows=[{k-len(base):v for k,v in row.items() if k>=len(base)} for row in allrows]
    newrank=len(reduced(newrows,len(full)-len(base),r)[1])
    oldrank=len(reduced(oldrows,len(base),r)[1])
    result=dict(status='verified_finite_followup',p=p,r=r,h=h,public_target=Q,
                prior_receipt_sha256=hashlib.sha256(prior.read_bytes()).hexdigest(),degrees=counts,
                eligible_trace_derivations=eligible,skipped_fibers=skipped,derivations=derivations,
                trace_derivation_group_additions=derivation_ops,generic_growth_group_additions=derivation_ops,
                old_columns=len(base),baseline_rank=oldrank,extended_columns=len(full),full_rank=fullrank,
                new_column_block_rank=newrank,rank_on_original=fullrank-newrank,
                extra_constraints_on_original=fullrank-newrank-oldrank,
                source_hashes={name:hashlib.sha256((HERE/name).read_bytes()).hexdigest()
                               for name in ['growth.py','modular.py','study.py','verify.py','FOLLOWUP_PROTOCOL.md']},
                arms=arms,performance_speedup=None)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    with args.out.open('x') as output:output.write(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ['derivations','arms']}),flush=True)
    for arm in arms:print(json.dumps({k:v for k,v in arm.items() if k not in ['points','logs']}),flush=True)


if __name__=='__main__':main()
