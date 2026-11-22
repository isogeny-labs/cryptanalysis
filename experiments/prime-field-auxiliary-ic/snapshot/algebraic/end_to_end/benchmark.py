"""Time full public-input attacks, then audit independent relation certificates."""
import argparse
import hashlib
import json
from pathlib import Path
import statistics
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent.parent))
from prepare import Curve
from sympy import isprime

METHODS={'chain':('chain.txt','chain','factor_base'),
         'same_base':('same_base.txt','explicit','factor_base'),
         'random':('random.txt','explicit','random_factor_base')}


def audit(folder,method,prefix):
    manifest=json.loads((folder/'public.json').read_text());pub=manifest['public']
    data=json.loads(prefix.with_suffix('.json').read_text())
    rels=[json.loads(line) for line in prefix.with_suffix('.relations.jsonl').read_text().splitlines()]
    E=Curve(pub['p'],a4=pub['a'],a6=pub['b']);n=pub['n']
    P,Q=tuple(pub['P']),tuple(pub['Q'])
    assert isprime(n) and E.contains(P) and E.contains(Q) and E.mul(n,P) is None
    # A nonzero n-torsion point and a unique multiple of n in Hasse's interval
    # certify the full target curve order, rather than assuming a small subgroup.
    radius=__import__('math').isqrt(4*pub['p'])
    assert (pub['p']+1-radius+n-1)//n==(pub['p']+1+radius)//n==1
    F=[tuple(x) for x in manifest[METHODS[method][2]]]
    assert all(E.contains(f) for f in F) and len({f[0] for f in F})==len(F)
    columns=[0]*len(F);A=B=0;weights=data['weights'];seen=set()
    assert data['relations']==len(rels)==len(weights)
    for rel,w in zip(rels,weights):
        assert 0<=w<n and rel['si'] in [1,-1] and rel['sj'] in [1,-1]
        left=E.add(E.mul(rel['a'],P),E.mul(rel['b'],Q))
        right=E.add(E.mul(rel['si']%n,F[rel['i']]),E.mul(rel['sj']%n,F[rel['j']]))
        assert left==right
        key=[0]*len(F);key[rel['i']]+=rel['si'];key[rel['j']]+=rel['sj']
        first=next(x for x in key if x)
        key=tuple(x if first>0 else -x for x in key)
        assert key not in seen;seen.add(key)
        columns[rel['i']]=(columns[rel['i']]+w*rel['si'])%n
        columns[rel['j']]=(columns[rel['j']]+w*rel['sj'])%n
        A=(A-w*rel['a'])%n;B=(B-w*rel['b'])%n
    assert not any(columns) and A==data['A'] and B==data['B'] and B
    assert sum(w!=0 for w in weights)>=3
    assert data['recovered']==-A*pow(B,-1,n)%n
    assert E.mul(data['recovered'],P)==Q
    # Only this verifier reads the known fixture answer.
    assert data['recovered']==json.loads((folder/'expected.json').read_text())['secret']
    return dict(verified_relations=len(rels),dependency_relations=sum(w!=0 for w in weights),
                distinct_signed_relation_rows=True,verified_factor_base_cancellation=True,
                verified_public_key=True,certified_full_group_order=n)


def run(folder,seed,methods):
    manifest=json.loads((folder/'public.json').read_text());bits=manifest['public']['p'].bit_length()
    binary=ROOT/f'native{bits}';source=ROOT/'native_ic.cpp'
    if not binary.exists() or binary.stat().st_mtime<source.stat().st_mtime:
        temporary=binary.with_suffix('.new')
        subprocess.run(['g++','-O3','-march=native','-std=c++17','-Wall','-Wextra',
                        f'-DFIELD_BITS={bits}','-o',str(temporary),str(source)],check=True)
        temporary.replace(binary)
    results=[]
    # Rotate execution order across predeclared seeds to reduce order effects.
    ordered=methods[seed%len(methods):]+methods[:seed%len(methods)]
    for method in ordered:
        name,mode,_=METHODS[method];prefix=folder/f'{method}_seed{seed}'
        print(f'START {folder.name} {method} seed {seed}',flush=True)
        started=time.perf_counter()
        with prefix.with_suffix('.log').open('w') as log:
            subprocess.run([str(binary),str(folder/name),mode,str(prefix),str(seed)],stdout=log,check=True)
        wall=time.perf_counter()-started
        data=json.loads(prefix.with_suffix('.json').read_text())
        data.update(method=method,seed=seed,process_wall_seconds=wall,
                    audit=audit(folder,method,prefix),basis_size=len(manifest[METHODS[method][2]]),
                    source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                    build_flags=f'-O3 -march=native -std=c++17 -DFIELD_BITS={bits}')
        basis=manifest['random_basis_seconds' if method=='random' else 'auxiliary_basis_seconds']
        data.update(basis_seconds=basis,end_to_end_seconds=wall+basis)
        prefix.with_suffix('.audited.json').write_text(json.dumps(data,indent=2)+'\n')
        print(f"DONE {method}: {data['queries']} queries, {data['relations']} relations, "
              f"{data['end_to_end_seconds']:.6f} seconds; certificate verified",flush=True)
        results.append(data)
    if 'chain' in methods and 'same_base' in methods:
        a=json.loads((folder/f'chain_seed{seed}.json').read_text())
        b=json.loads((folder/f'same_base_seed{seed}.json').read_text())
        assert a['queries']==b['queries'] and a['weights']==b['weights']
        assert (folder/f'chain_seed{seed}.relations.jsonl').read_bytes()==(folder/f'same_base_seed{seed}.relations.jsonl').read_bytes()
    return results


def summarize(folder):
    runs=[json.loads(f.read_text()) for f in folder.glob('*_seed*.audited.json')]
    summaries={}
    for method in METHODS:
        rows=[r for r in runs if r['method']==method]
        if rows:summaries[method]=dict(runs=len(rows),
            median_end_to_end_seconds=statistics.median(r['end_to_end_seconds'] for r in rows),
            median_queries=statistics.median(r['queries'] for r in rows),
            median_seconds_per_query=statistics.median(r['loop_seconds']/r['queries'] for r in rows),
            all_certificates_verified=all(r['audit']['verified_public_key'] for r in rows))
    if 'chain' in summaries:
        for method in ['same_base','random']:
            if method in summaries:
                summaries[method]['median_time_divided_by_auxiliary_time']=summaries[method]['median_end_to_end_seconds']/summaries['chain']['median_end_to_end_seconds']
    result=dict(folder=folder.name,runs=runs,summary=summaries)
    (folder/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(summaries,indent=2),flush=True)
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('folder',type=Path)
    parser.add_argument('--seeds',type=int,nargs='+',default=[0])
    parser.add_argument('--methods',nargs='+',choices=list(METHODS),default=list(METHODS))
    parser.add_argument('--audit-only',action='store_true')
    args=parser.parse_args();folder=args.folder.resolve()
    for seed in args.seeds:
        if args.audit_only:
            for method in args.methods:print(method,seed,audit(folder,method,folder/f'{method}_seed{seed}'))
        else:run(folder,seed,args.methods)
    summarize(folder)
