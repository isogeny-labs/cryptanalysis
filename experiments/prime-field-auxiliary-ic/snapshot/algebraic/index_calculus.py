"""Index calculus with Groebner or structure-aware resultant relation search."""
import argparse
import json
from pathlib import Path
import random
import time

import sympy as sp
from solver import Curve,make_system,solve


def run(public,roots,auxiliary,encoding,outdir,*,m=2,max_trials=1000,
        relation_timeout=30,total_timeout=300,seed=0,engine='groebner'):
    outdir=Path(outdir).resolve();outdir.mkdir(parents=True,exist_ok=True)
    p,n,a,b=(int(public[k]) for k in ['p','n','a','b'])
    E=Curve(p,a4=a,a6=b)
    P,Q=tuple(public['P']),tuple(public['Q'])
    relation_P=tuple(public.get('relation_P',public.get('P_full',P)))
    relation_Q=tuple(public.get('relation_Q',public.get('Q_full',Q)))
    h=int(public.get('cofactor',1))
    assert sp.isprime(n) and P is not None and E.mul(n,P) is None
    assert E.mul(h,relation_P)==P and E.mul(h,relation_Q)==Q
    F=[];seen=set()
    for x in roots:
        rhs=(x**3+a*x+b)%p
        ys=sp.sqrt_mod(rhs,p,all_roots=True)
        if not ys:continue
        R=E.mul(h,(x,int(ys[0])))
        if R is None or R[0] in seen:continue
        seen.add(R[0]);F.append((R[0],min(R[1],p-R[1])))
    lookup={}
    for j,R in enumerate(F):lookup[R]=(j,1);lookup[E.neg(R)]=(j,-1)
    K=len(F)
    if not K:raise ValueError('No nonidentity factor-base points in the subgroup')
    (outdir/'public.json').write_text(json.dumps(public|{'roots':roots,'factor_base':F},indent=2)+'\n')
    membership_seconds=0
    if engine=='resultant':
        if m not in [2,3]:raise ValueError('The resultant engine supports m=2 or m=3')
        from resultant_solver import prepare as prepare_resultant,solve as solve_resultant,solve_three,signed_base
        compiled=prepare_resultant(dict(p=p,a=a,b=b),auxiliary=auxiliary,roots=roots,encoding=encoding)
        raw_base=signed_base(compiled,roots) if m==3 else None
        membership_seconds=compiled.prepare_seconds
    elif engine!='groebner':raise ValueError('Unknown relation engine')
    rng=random.Random(seed)
    pivots={};relations=[];trials=[]
    started=time.monotonic()
    result=dict(status='incomplete',encoding=encoding,engine=engine,factor_base_columns=K,
                membership_prepare_seconds=membership_seconds,
                budget_policy='between resultant calls' if engine=='resultant' else 'bounded Groebner subprocesses')
    for trial in range(max_trials):
        remaining=total_timeout-(time.monotonic()-started)
        if remaining<=0:result['reason']='total_timeout';break
        aa,bb=rng.randrange(n),rng.randrange(n)
        target=E.add(E.mul(aa,relation_P),E.mul(bb,relation_Q))
        if target is None:continue
        if engine=='resultant':
            found=solve_resultant(compiled,target) if m==2 else solve_three(compiled,target,raw_base)
            folder=outdir/f'trial{trial:04}';folder.mkdir(exist_ok=True)
            (folder/'target.json').write_text(json.dumps(dict(target=target,a=aa,b=bb))+'\n')
            (folder/'result.json').write_text(json.dumps(found,indent=2)+'\n')
        else:
            system=make_system(dict(p=p,a=a,b=b),target,m=m,auxiliary=auxiliary,
                               roots=roots,encoding=encoding)
            found=solve(system,outdir/f'trial{trial:04}',timeout=min(relation_timeout,remaining))
        trials.append(dict(a=aa,b=bb,status=found['status'],
                           seconds=found['elapsed_seconds'],relations=len(found['relations'])))
        if found['status']!='solved':
            result['reason']='relation_solver_'+found['status'];break
        if not found['relations']:continue
        raw_points=[tuple(R) for R in found['relations'][0]]
        projected=[E.mul(h,R) for R in raw_points]
        codes=[lookup[R] for R in projected if R is not None]
        relation=dict(a=aa,b=bb,raw_points=raw_points,codes=codes,target=target)
        relations.append(relation)
        row=[0]*(K+2);weights=[0]*len(relations);weights[-1]=1
        for col,sign in codes:row[col]=(row[col]+sign)%n
        row[K],row[K+1]=-aa%n,-bb%n
        stored=False
        for col in range(K):
            if not row[col]:continue
            if col not in pivots:
                inv=pow(row[col],-1,n)
                pivots[col]=([v*inv%n for v in row],[v*inv%n for v in weights])
                stored=True;break
            pivot,pivot_weights=pivots[col]
            v=row[col]
            row=[(x-v*y)%n for x,y in zip(row,pivot)]
            for j,w in enumerate(pivot_weights):weights[j]=(weights[j]-v*w)%n
        if stored or not row[K+1]:continue
        k=-row[K]*pow(row[K+1],-1,n)%n
        assert E.mul(k,P)==Q
        # Audit the entire cancellation certificate before reporting success.
        canceled=[0]*K;A=B=0
        for w,rel in zip(weights,relations):
            total=None
            for R in rel['raw_points']:total=E.add(total,R)
            assert total==tuple(rel['target'])
            for col,sign in rel['codes']:canceled[col]+=w*sign
            A-=w*rel['a'];B-=w*rel['b']
        assert all(v%n==0 for v in canceled)
        assert A%n==row[K] and B%n==row[K+1]
        result.update(status='solved',recovered=k,dependency_A=row[K],dependency_B=row[K+1],
                      weights=weights,verified=True)
        break
    result.update(elapsed_seconds=time.monotonic()-started,trials=len(trials),
                  relations=len(relations),rank=len(pivots))
    (outdir/'relations.json').write_text(json.dumps(relations,indent=2)+'\n')
    (outdir/'trials.json').write_text(json.dumps(trials,indent=2)+'\n')
    (outdir/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--public',type=Path,required=True)
    parser.add_argument('--roots',type=Path,required=True)
    parser.add_argument('--auxiliary',type=Path)
    parser.add_argument('--encoding',choices=['chain','expanded','plain'],default='chain')
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--m',type=int,default=2)
    parser.add_argument('--engine',choices=['groebner','resultant'],default='groebner')
    parser.add_argument('--max-trials',type=int,default=1000)
    parser.add_argument('--relation-timeout',type=float,default=30,
                        help='Per-call bound for Groebner; resultant total budget is checked between calls')
    parser.add_argument('--total-timeout',type=float,default=300)
    args=parser.parse_args()
    result=run(json.loads(args.public.read_text()),json.loads(args.roots.read_text()),
               json.loads(args.auxiliary.read_text()) if args.auxiliary else None,
               args.encoding,args.output,m=args.m,max_trials=args.max_trials,
               relation_timeout=args.relation_timeout,total_timeout=args.total_timeout,engine=args.engine)
    print(json.dumps(result,indent=2))
