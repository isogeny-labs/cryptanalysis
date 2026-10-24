"""Replay the complete target-directed modular-fiber search."""
import json
from pathlib import Path
import sys

from sage.all import GF, PolynomialRing, classical_modular_polynomial

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / 'hecke-two-sheet-small-order-20261023/tools'))
import hecke11 as H

def main():
    data = json.loads((HERE / 'result.json').read_text())
    source = json.loads((ROOT / 'hecke-higher-degree-screen-20261024/result.json').read_text())
    source_js = {r['j']: r for r in source['records']}
    old = [tuple(x) for x in json.loads((ROOT / 'hecke-torsion-frontiers-20261024/p20023.result.json').read_text())['column_representatives']]
    funcs, jfun = H.build([2, 3])
    rd = H.Reduced(20023, funcs, jfun, [2, 3])
    T = rd.E([5, 5, 1])
    targets = {}
    for i in [487, 488, 1015, 1016, 1391, 1392, 2593, 2594]:
        a = old[i]
        P = rd.E(0) if a == (-1, -1) else rd.E([*a, 1])
        for k in range(5):
            Q = P + k*T
            j = rd.j(Q)
            if j is not None:
                targets.setdefault(str(int(j)), []).append({'orbit_index': i, 'translate': k,
                    'point': [-1, -1] if Q.is_zero() else [int(Q[0]), int(Q[1])]})
    assert targets == data['target_js']
    F = GF(20023)
    R = PolynomialRing(F, 'z')
    z = R.gen()
    report = {}
    for ell in (29, 31):
        phi = classical_modular_polynomial(ell)
        linked = {}
        reverse_counts = {}
        for j in targets:
            roots = R(phi(F(int(j)), z)).roots()
            reverse_counts[int(j)] = sum(int(m) for _, m in roots)
            for x, _ in roots:
                sj = int(x)
                if sj in source_js:
                    linked.setdefault(sj, set()).add(int(j))
        saved = data['outcomes'][str(ell)]
        assert {int(k): v for k, v in saved['reverse_root_counts'].items()} == reverse_counts
        assert len(linked) == saved['candidate_source_j_count']
        for row in saved['candidate_rows']:
            sj = row['source_j']
            assert row['source_count'] == source_js[sj]['source_count']
            roots = R(phi(F(sj), z)).roots()
            assert row['linked_target_js'] == sorted(linked.pop(sj))
            assert set(row['linked_target_js']) <= {int(x) for x, _ in roots}
            assert row['rational_root_multiplicity'] == sum(int(m) for _, m in roots)
            assert row['distinct_rational_roots'] == len(roots)
            assert row['fully_split'] == (row['rational_root_multiplicity'] == ell+1)
        assert not linked
        assert saved['fully_split_adjacencies'] == [r for r in saved['candidate_rows'] if r['fully_split']]
        report[str(ell)] = {'target_j_count': len(targets),
                            'candidate_source_j_count': saved['candidate_source_j_count'],
                            'fully_split_source_j_count': saved['fully_split_source_j_count'],
                            'validated': True}
    (HERE / 'validation.json').write_text(json.dumps(report, indent=2, sort_keys=True)+'\n')
    print(json.dumps(report, sort_keys=True))

if __name__ == '__main__':
    main()
