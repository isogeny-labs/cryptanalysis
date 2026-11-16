"""Audit and time candidate extraction on the original 32768-root workload."""
import argparse
import json
from pathlib import Path
import statistics
import time

from resultant_solver import prepare,solve,chain_resultant
from native_candidates import ChainCandidates
from known_root_gcd import KnownRootGCD


def canonical(result):
    return {tuple(sorted(map(tuple,r))) for r in result['relations']}


def run(folder,out):
    manifest=json.loads((folder/'models.json').read_text())
    previous=json.loads((folder/'runs.json').read_text())
    roots=manifest['structured_roots']
    model=prepare(manifest['curve'],auxiliary=manifest['auxiliary'],roots=roots)
    started=time.perf_counter();native=ChainCandidates(model,roots)
    native_setup=time.perf_counter()-started
    started=time.perf_counter();blocks=KnownRootGCD(roots,manifest['curve']['p'])
    block_setup=time.perf_counter()-started
    started=time.perf_counter();lifted_blocks=KnownRootGCD.for_model(model,roots)
    lifted_block_setup=time.perf_counter()-started
    assert blocks.polynomial==model.polynomial
    records=[]
    for record in previous:
        if record['encoding']!='chain':continue
        target=record['target'];poly=chain_resultant(model,target)
        # Rotate the GCD extraction timings. Both start from the exact same R.
        timings={};sets={}
        order=['flint_gcd','blocked_gcd','lifted_blocked_gcd','native_circuit']
        order=order[record['seed']%4:]+order[:record['seed']%4]
        for method in order:
            started=time.perf_counter()
            if method=='flint_gcd':
                G=model.polynomial.gcd(poly)
                roots_found={int(x) for x,_ in G.roots()}
            elif method=='blocked_gcd':roots_found=blocks.candidates(poly)
            elif method=='lifted_blocked_gcd':roots_found=lifted_blocks.candidates(poly)
            else:roots_found=native.candidates(target[0])
            timings[method]=time.perf_counter()-started;sets[method]=roots_found
        assert sets['flint_gcd']==sets['blocked_gcd']
        # Native deliberately evaluates only x coordinates lifting to E(F_p).
        assert sets['native_circuit']==sets['flint_gcd'].intersection(native.points)
        assert sets['native_circuit']==sets['lifted_blocked_gcd']
        answer=native.solve(target)
        assert canonical(answer)==canonical(record)
        for x in [native.xs[i] for i in range(0,len(native.xs),max(1,len(native.xs)//16))]:
            # Coefficient-backed evaluation independently checks the circuit.
            index=native.xs.index(x)
            assert native.values()[index]==int(poly(x))
        row=dict(seed=record['seed'],target=target,timings=timings,
                 native_full_relation_seconds=answer['elapsed_seconds'],
                 verified_relations=answer['relations'],candidate_roots=sorted(sets['native_circuit']),
                 exact_gcd_roots_agree=True,circuit_values_verified=True)
        records.append(row)
        print(record['seed'],timings,flush=True)
    summary={name:statistics.median(r['timings'][name] for r in records)
             for name in ['flint_gcd','blocked_gcd','lifted_blocked_gcd','native_circuit']}
    summary['native_full_relation_seconds']=statistics.median(r['native_full_relation_seconds'] for r in records)
    summary['blocked_gcd_speedup']=summary['flint_gcd']/summary['blocked_gcd']
    summary['lifted_blocked_gcd_speedup']=summary['flint_gcd']/summary['lifted_blocked_gcd']
    summary['native_extraction_speedup']=summary['flint_gcd']/summary['native_circuit']
    result=dict(root_count=len(roots),liftable_coordinates=len(native.xs),
                native_setup_seconds=native_setup,block_setup_seconds=block_setup,
                lifted_block_setup_seconds=lifted_block_setup,
                records=records,summary=summary)
    out.parent.mkdir(exist_ok=True,parents=True);out.write_text(json.dumps(result,indent=2)+'\n')
    native.close();print(json.dumps(summary,indent=2),flush=True)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input',type=Path,default=Path(__file__).resolve().parent/'structure_results/field31_s15')
    p.add_argument('--output',type=Path,default=Path(__file__).resolve().parent/'end_to_end/gcd_benchmark.json')
    args=p.parse_args();run(args.input,args.output)
