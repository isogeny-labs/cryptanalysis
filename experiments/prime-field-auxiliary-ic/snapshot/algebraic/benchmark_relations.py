"""Target-independent algebraic relation benchmarks; no planted ordinary roots."""
import argparse
import itertools
import json
import random
import statistics
import time

from solver import Curve, ROOT, make_system, root_polynomial, solve
from prepare import chain


def lifted(E, roots):
    result=[]
    for x in roots:
        rhs=(x**3+E.a4*x+E.a6)%E.p
        y=pow(rhs,(E.p+1)//4,E.p)
        if y*y%E.p==rhs: result.append((x,min(y,E.p-y)))
    return result


def independent_ordinary_roots(E, count, liftable_count):
    """Match membership/base sizes using only E and counts, never a target."""
    roots=[]; have_lifts=have_nonlifts=0
    for x in range(10,E.p):
        rhs=(x**3+E.a4*x+E.a6)%E.p
        has_point=pow(rhs,(E.p-1)//2,E.p)!=E.p-1
        if has_point and have_lifts<liftable_count:
            roots.append(x);have_lifts+=1
        elif not has_point and have_nonlifts<count-liftable_count:
            roots.append(x);have_nonlifts+=1
        if len(roots)==count: return roots
    raise ValueError('Cannot construct matched ordinary base')


def uniform_finite_point(E, seed):
    """Uniform finite E(F_p) point, independent of either factor base."""
    rng=random.Random(20261114+seed)
    while True:
        x=rng.randrange(E.p)
        rhs=(x**3+E.a4*x+E.a6)%E.p
        y=pow(rhs,(E.p+1)//4,E.p)
        if y*y%E.p!=rhs: continue
        # Otherwise rational 2-torsion would receive twice the point weight.
        if y==0 and rng.getrandbits(1): continue
        if y and rng.getrandbits(1): y=E.p-y
        return x,y


def build_case(bits, depth, m, seed, summation='direct', curve=None):
    curve=curve or dict(p=2**bits-1,a=2 if bits==31 else 0,b=14 if bits==31 else 3)
    E=Curve(curve['p'],a4=curve['a'],a6=curve['b'])
    aux,V=chain(curve['p'],depth,enumerate_all=True)
    F=lifted(E,V)
    ordinary=independent_ordinary_roots(E,len(V),len(F))
    assert len(ordinary)==len(V) and len(lifted(E,ordinary))==len(F)
    # Both bases are final before sampling the common target. No answer
    # coordinates are ever appended to either base.
    target=uniform_finite_point(E,seed)
    return dict(curve=curve,target=target,m=m,depth=depth,summation=summation,
                structured_roots=V,ordinary_roots=ordinary,auxiliary=aux,
                signed_structured_points=sum(1 if P[1]==0 else 2 for P in F),
                signed_ordinary_points=sum(1 if P[1]==0 else 2 for P in lifted(E,ordinary)),
                liftable_coordinates=len(F),target_sampling='uniform finite E(F_p)',
                bases_fixed_before_target=True,planted_coordinates=False,
                cofactor_projection=False)


def exhaustive_relations(E, roots, target, m):
    signed=[]
    for P in lifted(E,roots): signed.extend([P] if P[1]==0 else [P,E.neg(P)])
    expected=set()
    for choices in itertools.product(signed,repeat=m):
        total=None
        for P in choices: total=E.add(total,P)
        if total==target: expected.add(tuple(sorted(choices)))
    return expected


def case(bits, depth, m, seed, timeout, out, summation='direct', curve=None, algorithm='std'):
    manifest=build_case(bits,depth,m,seed,summation,curve)
    curve=manifest['curve']; E=Curve(curve['p'],a4=curve['a'],a6=curve['b'])
    aux,V=manifest['auxiliary'],manifest['structured_roots']
    ordinary,target=manifest['ordinary_roots'],tuple(manifest['target'])
    case_dir=out/f'field{bits}_s{depth}_m{m}_seed{seed}'
    case_dir.mkdir(parents=True,exist_ok=True)
    (case_dir/'case.json').write_text(json.dumps(manifest,indent=2)+'\n')
    # Membership is factor-base precomputation, not repeated for each
    # coordinate or each random relation target.
    precompute={}
    for name,roots in [('expanded',V),('plain',ordinary)]:
        started=time.monotonic();root_polynomial(roots,curve['p'])
        precompute[name]=time.monotonic()-started
    records=[]
    for encoding,roots in [('chain',V),('expanded',V),('plain',ordinary)]:
        started=time.monotonic()
        system=make_system(curve,target,m=m,auxiliary=aux,roots=roots,
                           encoding=encoding,summation=summation)
        build=time.monotonic()-started
        result=solve(system,case_dir/encoding,timeout=timeout,memory_mib=1536,algorithm=algorithm)
        outcome=('relation_found' if result['relations'] else 'no_relation') if result['status']=='solved' else 'unknown'
        record=dict(field_bits=bits,p=curve['p'],depth=depth,root_count=len(V),m=m,
                    seed=seed,summation=summation,encoding=encoding,algorithm=algorithm,
                    build_seconds=build,membership_precompute_seconds=precompute.get(encoding,0),
                    elapsed_seconds=result['elapsed_seconds'],total_seconds=build+result['elapsed_seconds'],
                    backend_seconds=result['backend_seconds'],status=result['status'],outcome=outcome,
                    variables=result['variables'],equations=result['equations'],
                    relations=len(result['relations']),timeout_seconds=timeout,
                    planted_coordinates=False,target_sampling=manifest['target_sampling'])
        if result['status']=='solved':
            for relation in result['relations']:
                total=None
                for P in relation: total=E.add(total,tuple(P))
                assert total==target
            if len(V)<=8:
                actual={tuple(sorted(tuple(P) for P in rel)) for rel in result['relations']}
                assert actual==exhaustive_relations(E,roots,target,m)
        records.append(record);print(json.dumps(record),flush=True)
    answers=[json.loads((case_dir/e/'result.json').read_text()) for e in ['chain','expanded']]
    if all(a['status']=='solved' for a in answers):
        assert ({tuple(sorted(tuple(P) for P in rel)) for rel in answers[0]['relations']}
                =={tuple(sorted(tuple(P) for P in rel)) for rel in answers[1]['relations']})
    return records


def summarize(records):
    summary=[]
    for bits in sorted({r['field_bits'] for r in records}):
        for m in sorted({r['m'] for r in records if r['field_bits']==bits}):
            for encoding in ['chain','expanded','plain']:
                group=[r for r in records if r['field_bits']==bits and r['m']==m and r['encoding']==encoding]
                completed=[r for r in group if r['status']=='solved']
                summary.append(dict(field_bits=bits,m=m,encoding=encoding,attempts=len(group),
                    completed=len(completed),unknown=len(group)-len(completed),
                    targets_with_relation=sum(r['outcome']=='relation_found' for r in group),
                    total_relations=sum(r['relations'] for r in group),
                    total_solver_seconds=sum(r['total_seconds'] for r in group),
                    median_completed_seconds=statistics.median(r['total_seconds'] for r in completed) if completed else None))
    return summary


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--large',action='store_true')
    parser.add_argument('--toy',action='store_true')
    parser.add_argument('--bits',type=int,nargs='+',choices=[31,61],default=[31,61])
    parser.add_argument('--repeats',type=int,default=3)
    parser.add_argument('--timeout',type=float,default=15)
    parser.add_argument('--summation',choices=['direct','split'],default='direct')
    parser.add_argument('--algorithm',choices=['std','slimgb'],default='std')
    args=parser.parse_args()
    label='toy' if args.toy else 'large' if args.large else 'small'
    out=ROOT/'audit/benchmarks_corrected'/label;out.mkdir(parents=True,exist_ok=True)
    records=[]
    configs=[(7,3,2,dict(p=127,a=2,b=51))] if args.toy else [
        (bits,10 if bits==31 else 11,3,None) if args.large else (bits,3,m,None)
        for bits in args.bits for m in ([3] if args.large else [2,3])]
    for bits,depth,m,curve in configs:
        for seed in range(args.repeats):
            records.extend(case(bits,depth,m,seed,args.timeout,out,args.summation,curve,args.algorithm))
            (out/'runs.json').write_text(json.dumps(records,indent=2)+'\n')
    summary=summarize(records)
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2),flush=True)


if __name__=='__main__':main()
