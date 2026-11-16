"""Audit the new structural timings, inputs, identities, and point relations."""
import json
import math
from pathlib import Path
import statistics

from resultant_solver import ROOT,Curve,prepare,solve
from benchmark_resultants import digest,liftable
from benchmark_relations import uniform_finite_point


def canonical(relations):
    return {tuple(sorted(tuple(P) for P in rel)) for rel in relations}


def main():
    rows_checked=relations_checked=0
    for source in sorted((ROOT/'structure_results').glob('*/models.json')):
        folder=source.parent;manifest=json.loads(source.read_text())
        curve=manifest['curve'];E=Curve(curve['p'],a4=curve['a'],a6=curve['b'])
        V,W=manifest['structured_roots'],manifest['random_roots']
        assert len(set(V))==len(V)==len(set(W))==len(W)==manifest['root_count']
        assert sum(liftable(E,x) for x in V)==sum(liftable(E,x) for x in W)==manifest['liftable_coordinates']
        models=dict(chain=prepare(curve,auxiliary=manifest['auxiliary']),
                    expanded=prepare(curve,roots=V,encoding='expanded'),
                    random=prepare(curve,roots=W,encoding='random'))
        assert models['chain'].polynomial==models['expanded'].polynomial
        assert digest(models['chain'].polynomial)==manifest['structured_membership_sha256']
        assert digest(models['random'].polynomial)==manifest['random_membership_sha256']
        rows=json.loads((folder/'runs.json').read_text())
        by_case={}
        for row in rows:
            assert row['status']=='solved'
            target=tuple(row['target'])
            assert target==uniform_finite_point(E,row['seed'])
            model=models[row['encoding']]
            for relation in row['relations']:
                total=None
                for P in relation:
                    P=tuple(P)
                    assert E.contains(P) and int(model.polynomial(P[0]))==0
                    total=E.add(total,P)
                assert total==target;relations_checked+=1
            by_case.setdefault(row['seed'],{})[row['encoding']]=row
            rows_checked+=1
        for seed,answers in by_case.items():
            assert canonical(answers['chain']['relations'])==canonical(answers['expanded']['relations'])
            if 'resultant_sha256' in answers['chain']:
                assert answers['chain']['resultant_sha256']==answers['expanded']['resultant_sha256']
            else:
                assert answers['chain']['two_sum_calls']==answers['expanded']['two_sum_calls']
        summary=json.loads((folder/'summary.json').read_text())
        for item in summary:
            group=[r for r in rows if r['encoding']==item['encoding']]
            assert item['completed']==item['targets']==len(group)
            assert item['relation_targets']==sum(bool(r['relations']) for r in group)
            assert math.isclose(item['median_seconds'],statistics.median(r['elapsed_seconds'] for r in group))
        # Recompute a full native-field resultant outside the timed benchmark.
        if not folder.name.startswith('three_'):
            target=uniform_finite_point(E,0)
            A=solve(models['chain'],target,keep_polynomial=True)
            B=solve(models['expanded'],target,keep_polynomial=True)
            assert A['_resultant']==B['_resultant']
            assert digest(A['_resultant'])==by_case[0]['chain']['resultant_sha256']
            assert canonical(A['relations'])==canonical(by_case[0]['chain']['relations'])
    print(f'PASS: {rows_checked} timed computations, {relations_checked} point relations,')
    print('all model/target controls, same-base polynomial identities, and timing summaries verified.')


if __name__=='__main__':main()
