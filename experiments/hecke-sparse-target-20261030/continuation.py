"""Two fixed continuation controls; previous evidence is never overwritten."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

from modular import Curve
from study import run_field,target_query
from verify import ShortCurve,verify

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]


def matched():
    saved=json.loads((HERE/'runs/growth-01/receipt.json').read_text())
    prior=json.loads((HERE/'runs/f6-large-01/receipt.json').read_text())
    curve=Curve(saved['p']);r=saved['r'];G=tuple(prior['curve']['generator']);Q=tuple(saved['public_target'])
    original=saved['arms'][0]
    labels={tuple(P):k for P,k in zip(original['points'],original['logs'])};labels[None]=0
    seed=sorted((P,k) for P,k in labels.items() if P is not None)
    requested=saved['arms'][1]['known_points_including_zero'];attempts=0
    for i in range(saved['generic_growth_group_additions']):
        data=hashlib.sha256(('generic-growth-v1/'+str(i)).encode()).digest()
        P,a=seed[int.from_bytes(data[:16],'big')%len(seed)]
        R,b=seed[int.from_bytes(data[16:],'big')%len(seed)]
        point=curve.add(P,R);label=(a+b)%r
        labels[point]=label;labels[curve.neg(point)]=-label%r;attempts=i+1
        if len(labels)>=requested:break
    assert len(labels)>=requested
    values=sorted((P,k) for P,k in labels.items() if P is not None)
    short=ShortCurve(saved['p']);g=short.point(G)
    assert all(short.times(k,g)==short.point(P) for P,k in values)
    result=target_query([P for P,k in values],[k for P,k in values],curve,G,Q,r)
    if result['scalar'] is not None:assert short.times(result['scalar'],g)==short.point(Q)
    return dict(status='verified_matched_base_control',p=saved['p'],r=r,group_additions=attempts,
                trace_growth_group_additions=saved['trace_derivation_group_additions'],
                trace_base_points=requested,generic_base_points=len(labels),target=result)


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--cell',choices=['matched','f30-large'],required=True)
    parser.add_argument('--out',type=Path,required=True);args=parser.parse_args()
    subprocess.run(['bash','scripts/checkpoint.sh','gate'],cwd=ROOT,check=True)
    result=matched() if args.cell=='matched' else run_field(1000000,30,True)
    result['source_hashes']={name:hashlib.sha256((HERE/name).read_bytes()).hexdigest()
                             for name in ['continuation.py','study.py','modular.py','SPARSE_TRACE_PROTOCOL.md']}
    args.out.parent.mkdir(parents=True,exist_ok=True)
    with args.out.open('x') as output:output.write(json.dumps(result,indent=2,sort_keys=True)+'\n')
    if args.cell=='f30-large':
        result['independent_replay']=verify(args.out)
        with args.out.with_name('independent.json').open('x') as output:output.write(json.dumps(result['independent_replay'],indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k in ['status','p','r','C','group_additions','trace_growth_group_additions','trace_base_points','generic_base_points','target','independent_replay']}),flush=True)


if __name__=='__main__':main()
