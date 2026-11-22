"""Reuse the frozen original signed pair index for bounded 3/4-term queries."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

from modular import Curve
from verify import ShortCurve

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]


def key(point):return (-1,-1) if point is None else point


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out',type=Path,required=True);args=parser.parse_args()
    subprocess.run(['bash','scripts/checkpoint.sh','gate'],cwd=ROOT,check=True)
    source=HERE/'runs/f6-large-01/receipt.json';saved=json.loads(source.read_text())
    curve=Curve(saved['p']);r=saved['r'];G=tuple(saved['curve']['generator']);Q=tuple(saved['public_target'])
    labels={None:0}
    for P,k in zip(saved['normalized_base'],saved['base_logs']):
        P=tuple(P);labels[P]=k;labels[curve.neg(P)]=-k%r
    values=sorted(labels,key=key);pairs={};start=curve.ops
    for i,P in enumerate(values):
        for R in values[i:]:pairs.setdefault(curve.add(P,R),(P,R,(labels[P]+labels[R])%r))
    setup=curve.ops-start;short=ShortCurve(saved['p']);shortG=short.point(G);shortQ=short.point(Q)
    results=[]
    for name,offsets,cap in [('three_term',values,len(values)),('four_term',sorted(pairs,key=key),256)]:
        start=curve.ops;answer=None;witness=None;attempts=0
        for D in offsets[:cap]:
            attempts+=1;remaining=curve.add(Q,curve.neg(D))
            if remaining in pairs:
                A,B,pair_log=pairs[remaining]
                if name=='three_term':
                    witness=[A,B,D];answer=(pair_log+labels[D])%r
                else:
                    C,E,second_log=pairs[D];witness=[A,B,C,E];answer=(pair_log+second_log)%r
                assert curve.total(witness)==Q and curve.mul(answer,G)==Q
                assert short.times(answer,shortG)==shortQ
                break
        results.append(dict(arm=name,status='verified' if answer is not None else 'no_match_within_cap',
                            cap=cap,attempts=attempts,scalar=answer,witness=witness,
                            query_group_additions_including_replay=curve.ops-start))
    result=dict(status='verified_finite_arity_control',p=saved['p'],r=r,public_target=Q,
                original_base_points_including_zero=len(values),pair_entries=len(pairs),
                pair_setup_group_additions=setup,pair_points_digest=hashlib.sha256(json.dumps(sorted(pairs,key=key)).encode()).hexdigest(),
                source_receipt_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),arms=results,
                source_hashes={name:hashlib.sha256((HERE/name).read_bytes()).hexdigest() for name in ['arity.py','ARITY_PROTOCOL.md']},
                performance_speedup=None)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    with args.out.open('x') as output:output.write(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(result),flush=True)


if __name__=='__main__':main()
