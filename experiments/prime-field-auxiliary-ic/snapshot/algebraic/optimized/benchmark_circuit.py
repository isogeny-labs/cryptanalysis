"""Compare v1 and v2 circuit extraction on the original large factor base."""
import json
from pathlib import Path
import statistics
import sys
import time

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent))
from native_candidates import ChainCandidates
from resultant_solver import prepare


def run():
    original=ROOT.parent/'structure_results/field31_s15'
    manifest=json.loads((original/'models.json').read_text())
    targets=[r for r in json.loads((original/'runs.json').read_text()) if r['encoding']=='chain']
    model=prepare(manifest['curve'],auxiliary=manifest['auxiliary'],roots=manifest['structured_roots'])
    solvers={'v1':ChainCandidates(model,manifest['structured_roots']),
             'v2':ChainCandidates(model,manifest['structured_roots'],native_source=ROOT/'native_v2.cpp')}
    rows=[]
    for target in targets:
        X=target['target'][0];answers={};timings={}
        order=['v1','v2'] if target['seed']%2==0 else ['v2','v1']
        for label in order:
            solver=solvers[label];samples=[]
            for _ in range(8):
                started=time.perf_counter();answer=solver.candidates(X);samples.append(time.perf_counter()-started)
            answers[label]=answer;timings[label]=statistics.median(samples)
        assert answers['v1']==answers['v2']
        assert solvers['v1'].xs==solvers['v2'].xs
        assert solvers['v1'].values()==solvers['v2'].values()
        old_relations=solvers['v1'].solve(target['target'])['relations']
        new_relations=solvers['v2'].solve(target['target'])['relations']
        canonical=lambda rs:{tuple(sorted(map(tuple,r))) for r in rs}
        assert canonical(old_relations)==canonical(new_relations)==canonical(target['relations'])
        rows.append(dict(seed=target['seed'],target=target['target'],timings=timings,
                         all_scalar_values_agree=True,verified_relations=new_relations))
    medians={label:statistics.median(row['timings'][label] for row in rows) for label in solvers}
    result=dict(root_count=len(manifest['structured_roots']),liftable_coordinates=len(solvers['v1'].xs),
                records=rows,summary=dict(medians=medians,speedup=medians['v1']/medians['v2'],
                exact_scalar_values_checked=len(targets)*len(solvers['v1'].xs)))
    (ROOT/'circuit_results.json').write_text(json.dumps(result,indent=2)+'\n')
    for solver in solvers.values():solver.close()
    print(json.dumps(result['summary'],indent=2));return result


if __name__=='__main__':run()
