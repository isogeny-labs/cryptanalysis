"""Serial, three-seed comparison on identical public target instances."""
import json
import os
import statistics
import sys
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent))
from prepare import Curve


def audit(folder,method):
    public=json.loads((folder/'public.json').read_text())
    metrics=json.loads((folder/'metrics.json').read_text())
    p,n=public['p'],public['n']
    E=Curve(p,a4=public['a'],a6=public['b'])
    P,Q=tuple(public['P']),tuple(public['Q'])
    k=metrics['recovered']
    assert E.mul(k,P)==Q
    if method=='rho':
        a1,b1,a2,b2=[metrics[name] for name in ['collision_a1','collision_b1','collision_a2','collision_b2']]
        assert (a1-a2+(b1-b2)*k)%n==0 and (b1-b2)%n!=0
        assert E.add(E.mul(a1,P),E.mul(b1,Q))==E.add(E.mul(a2,P),E.mul(b2,Q))
        return
    cert=json.loads((folder/'certificate.json').read_text())
    F=[tuple(R) for R in public['factor_base_representatives']]
    assert all(E.contains(R) for R in F)
    rels=[json.loads(line) for line in (folder/'relations.jsonl').read_text().splitlines()]
    assert len(rels)==len(cert['weights'])==cert['relations']
    coefficients=[0]*len(F)
    aug_a=aug_b=0
    for rel,weight in zip(rels,cert['weights']):
        R=None
        for code in rel['codes']:
            C=F[code//2]
            R=E.add(R,E.neg(C) if code&1 else C)
            coefficients[code//2]+=weight*(-1 if code&1 else 1)
        assert R==E.add(E.mul(rel['a'],P),E.mul(rel['b'],Q))
        aug_a-=weight*rel['a'];aug_b-=weight*rel['b']
    assert all(c%n==0 for c in coefficients)
    assert aug_a%n==cert['dependency_A']
    assert aug_b%n==cert['dependency_B']!=0
    assert -aug_a*pow(aug_b,-1,n)%n==k==cert['recovered']


def main():
    records=[]
    setup={entry['field_bits']:entry for entry in json.loads((ROOT/'setup.json').read_text())}
    for bits in [31,61]:
        for method in ['auxiliary','plain']:
            dataset=ROOT/f'field{bits}'/method
            executable=ROOT/f'{"rho" if method=="rho" else "ic"}{bits}'
            for seed in range(3):
                folder=dataset/f'seed{seed}'
                folder.mkdir(exist_ok=True)
                for name in ['public.txt','public.json']:
                    (folder/name).write_bytes((dataset/name).read_bytes())
                log=folder/'stdout.txt'
                started=time.perf_counter()
                pid=os.posix_spawn('/usr/bin/env',
                    ['env','-C',str(folder),str(executable),str(seed)],os.environ,
                    file_actions=[(os.POSIX_SPAWN_OPEN,1,str(log),os.O_WRONLY|os.O_CREAT|os.O_TRUNC,0o600),
                                  (os.POSIX_SPAWN_DUP2,1,2)])
                _,status,usage=os.wait4(pid,0)
                wall=time.perf_counter()-started
                if os.waitstatus_to_exitcode(status)!=0:
                    raise RuntimeError(log.read_text())
                audit(folder,method)
                metrics=json.loads((folder/'metrics.json').read_text())
                precompute=setup[bits].get(f'{method}_setup_seconds',0)
                record=dict(field_bits=bits,method=method,seed=seed,
                            wall_seconds=wall,
                            input_setup_seconds=precompute,
                            verified=True,**metrics)
                records.append(record)
                (ROOT/'runs.json').write_text(json.dumps(records,indent=2)+'\n')
                print(f'{bits}-bit field {method} seed {seed}: '
                      f'{metrics["solver_seconds"]:.6f}s; verified',flush=True)
    summary=[]
    for bits in [31,61]:
        for method in ['auxiliary','plain']:
            runs=[r for r in records if r['field_bits']==bits and r['method']==method]
            times=[r['solver_seconds'] for r in runs]
            summary.append(dict(field_bits=bits,method=method,
                median_solver_seconds=statistics.median(times),
                min_solver_seconds=min(times),max_solver_seconds=max(times),
                input_setup_seconds=runs[0]['input_setup_seconds'],
                median_total_seconds=statistics.median(times)+runs[0]['input_setup_seconds'],
                recovered=runs[0]['recovered'],all_verified=True))
            assert len({r['recovered'] for r in runs})==1
    for bits in [31,61]:
        assert len({r['recovered'] for r in records if r['field_bits']==bits})==1
    (ROOT/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2),flush=True)


if __name__=='__main__':main()
