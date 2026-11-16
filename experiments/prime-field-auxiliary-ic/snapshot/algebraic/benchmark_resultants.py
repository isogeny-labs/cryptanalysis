"""Fair matched tests of chain-aware versus explicit/random algebraic bases."""
from array import array
import argparse
import hashlib
import json
from pathlib import Path
import random
import statistics
import sys
import time

from resultant_solver import ROOT,Curve,prepare,solve,solve_three,signed_base
from prepare import chain
from benchmark_relations import uniform_finite_point


def digest(poly):
    data=array('Q',(int(poly[i]) for i in range(poly.degree()+1)))
    if sys.byteorder!='little':data.byteswap()
    return hashlib.sha256(data.tobytes()).hexdigest()


def liftable(E,x):
    return pow((x**3+E.a4*x+E.a6)%E.p,(E.p-1)//2,E.p)!=E.p-1


def random_roots(E,count,required_lifts,seed):
    rng=random.Random(seed);result=[];seen=set();lifts=nonlifts=0
    while len(result)<count:
        x=rng.randrange(E.p)
        if x in seen:continue
        seen.add(x)
        has=liftable(E,x)
        if has and lifts<required_lifts:result.append(x);lifts+=1
        elif not has and nonlifts<count-required_lifts:result.append(x);nonlifts+=1
    return result


def make_models(bits,depth):
    curve=dict(p=2**bits-1,a=2 if bits==31 else 0,b=14 if bits==31 else 3)
    E=Curve(curve['p'],a4=curve['a'],a6=curve['b'])
    before=time.perf_counter();aux,_=chain(E.p,depth,root_limit=0)
    map_seconds=time.perf_counter()-before
    A=prepare(curve,auxiliary=aux)
    before=time.perf_counter()
    C=Curve(E.p,a4=1);T=tuple(aux['auxiliary_generator']);G=tuple(aux['kernel_generator'])
    V=[];P=T
    for _ in range(2**depth):V.append(P[0]);P=C.add(P,G)
    assert P==T and len(set(V))==len(V)
    materialize_seconds=time.perf_counter()-before
    B=prepare(curve,roots=V,encoding='expanded')
    assert A.polynomial==B.polynomial
    K=sum(liftable(E,x) for x in V)
    before=time.perf_counter();W=random_roots(E,len(V),K,20261115+bits*100+depth)
    random_seconds=time.perf_counter()-before
    C=prepare(curve,roots=W,encoding='random')
    assert sum(liftable(E,x) for x in W)==K
    manifest=dict(curve=curve,depth=depth,root_count=len(V),liftable_coordinates=K,
                  target_sampling='uniform finite E(F_p), independent of all bases',
                  auxiliary=aux,structured_roots=V,random_roots=W,
                  auxiliary_map_seconds=map_seconds,
                  structured_membership_seconds=A.prepare_seconds,
                  structured_root_materialize_seconds=materialize_seconds,
                  expanded_membership_seconds=B.prepare_seconds,
                  random_root_selection_seconds=random_seconds,
                  random_membership_seconds=C.prepare_seconds,
                  structured_membership_sha256=digest(A.polynomial),
                  random_membership_sha256=digest(C.polynomial))
    return E,dict(chain=A,expanded=B,random=C),manifest


def run(bits,depth,targets,out):
    folder=out/f'field{bits}_s{depth}';folder.mkdir(parents=True,exist_ok=True)
    E,models,manifest=make_models(bits,depth)
    (folder/'models.json').write_text(json.dumps(manifest,indent=2)+'\n')
    records=[];names=['chain','expanded','random']
    for seed in range(targets):
        target=uniform_finite_point(E,seed)
        answers={};polynomials={}
        # Rotate execution order to avoid always favoring one warm/cold case.
        order=names[seed%3:]+names[:seed%3]
        for name in order:
            answer=solve(models[name],target,keep_polynomial=True)
            poly=answer.pop('_resultant')
            answer.update(field_bits=bits,depth=depth,seed=seed,target=list(target),
                          resultant_sha256=digest(poly))
            answers[name]=answer;polynomials[name]=poly
        assert polynomials['chain']==polynomials['expanded']
        canonical=lambda a:{tuple(sorted(tuple(P) for P in rel)) for rel in a['relations']}
        assert canonical(answers['chain'])==canonical(answers['expanded'])
        for name in names:
            answer=answers[name]
            for rel in answer['relations']:
                assert E.add(*map(tuple,rel))==target
            records.append(answer)
        (folder/'runs.json').write_text(json.dumps(records,indent=2)+'\n')
        print(f'field={bits}, S={2**depth}, target={seed}, seconds='
              +','.join(f'{n}:{answers[n]["elapsed_seconds"]:.6f}' for n in names)
              +', relations='+','.join(f'{n}:{len(answers[n]["relations"])}' for n in names),flush=True)
    summary=[]
    for name in names:
        group=[r for r in records if r['encoding']==name]
        summary.append(dict(field_bits=bits,depth=depth,root_count=2**depth,encoding=name,
            targets=len(group),completed=len(group),
            relation_targets=sum(bool(r['relations']) for r in group),
            total_relations=sum(len(r['relations']) for r in group),
            median_seconds=statistics.median(r['elapsed_seconds'] for r in group),
            median_elimination_seconds=statistics.median(r['elimination_seconds'] for r in group),
            median_gcd_seconds=statistics.median(r['gcd_seconds'] for r in group),
            total_seconds=sum(r['elapsed_seconds'] for r in group)))
    (folder/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    return summary


def run_three(bits,depth,targets,out):
    folder=out/f'three_field{bits}_s{depth}';folder.mkdir(parents=True,exist_ok=True)
    E,models,manifest=make_models(bits,depth)
    (folder/'models.json').write_text(json.dumps(manifest,indent=2)+'\n')
    points={name:signed_base(model,manifest['structured_roots'] if name!='random' else manifest['random_roots'])
            for name,model in models.items()}
    records=[];names=['chain','expanded','random']
    for seed in range(targets):
        target=uniform_finite_point(E,seed);answers={}
        for name in names[seed%3:]+names[:seed%3]:
            answer=solve_three(models[name],target,points[name])
            answer.update(field_bits=bits,depth=depth,seed=seed,target=list(target))
            answers[name]=answer
        canonical=lambda a:{tuple(sorted(tuple(P) for P in rel)) for rel in a['relations']}
        assert canonical(answers['chain'])==canonical(answers['expanded'])
        assert answers['chain']['two_sum_calls']==answers['expanded']['two_sum_calls']
        for name in names:records.append(answers[name])
        (folder/'runs.json').write_text(json.dumps(records,indent=2)+'\n')
        print(f'three-sum field={bits}, S={2**depth}, target={seed}, '+
              ','.join(f'{n}:{answers[n]["elapsed_seconds"]:.3f}s/{answers[n]["two_sum_calls"]} calls/{len(answers[n]["relations"])} relations' for n in names),flush=True)
    summary=[]
    for name in names:
        group=[r for r in records if r['encoding']==name]
        summary.append(dict(field_bits=bits,depth=depth,root_count=2**depth,encoding=name,
            targets=len(group),completed=len(group),
            relation_targets=sum(bool(r['relations']) for r in group),
            median_seconds=statistics.median(r['elapsed_seconds'] for r in group),
            median_two_sum_calls=statistics.median(r['two_sum_calls'] for r in group),
            total_seconds=sum(r['elapsed_seconds'] for r in group)))
    (folder/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    return summary


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bits',type=int,choices=[31,61],default=31)
    parser.add_argument('--depths',nargs='+',type=int,default=[10,12,15])
    parser.add_argument('--targets',type=int,default=16)
    parser.add_argument('--three',action='store_true')
    args=parser.parse_args()
    out=ROOT/'structure_results';out.mkdir(exist_ok=True)
    all_rows=[]
    for depth in args.depths:
        runner=run_three if args.three else run
        all_rows.extend(runner(args.bits,depth,args.targets,out))
        (out/f'summary_{args.bits}{"_three" if args.three else ""}.json').write_text(json.dumps(all_rows,indent=2)+'\n')
    print(json.dumps(all_rows,indent=2),flush=True)
