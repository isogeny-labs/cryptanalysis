"""Target-directed, exhaustive rational modular-fiber adjacency screen."""
from collections import defaultdict
from hashlib import sha256
import json
from pathlib import Path
import sys

from sage.all import GF, PolynomialRing, classical_modular_polynomial

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / 'hecke-two-sheet-small-order-20261023/tools'))
import hecke11 as H

def digest(path):
    return sha256(path.read_bytes()).hexdigest()

def key(P):
    return (-1, -1) if P.is_zero() else (int(P[0]), int(P[1]))

def main():
    protocol_path = HERE / 'protocol.json'
    protocol = json.loads(protocol_path.read_text())
    assert protocol['status'] == 'FROZEN_BEFORE_SCREEN'
    assert protocol['degrees'] == [29, 31]
    frontier_path = ROOT / 'hecke-torsion-frontiers-20261024/p20023.result.json'
    previous_path = ROOT / 'hecke-higher-degree-screen-20261024/result.json'
    l23_path = ROOT / 'hecke-l23-targeted-20261024/result.v2.json'
    source_hashes = {name: digest(path) for name, path in {
        'frontier': frontier_path, 'previous_screen': previous_path,
        'l23_result': l23_path,
        'hecke11': ROOT / 'hecke-two-sheet-small-order-20261023/tools/hecke11.py',
    }.items()}
    old = [tuple(x) for x in json.loads(frontier_path.read_text())['column_representatives']]
    assert len(old) == 3949
    l23 = json.loads(l23_path.read_text())
    assert len(l23['all_column_representatives']) == 3953
    previous = json.loads(previous_path.read_text())
    source_js = {r['j']: r for r in previous['records']}
    assert len(source_js) == 11619 and previous['source_point_count'] == 19745

    funcs, jfun = H.build([2, 3])
    rd = H.Reduced(20023, funcs, jfun, [2, 3])
    T = rd.E([5, 5, 1])
    assert 5 * T == rd.E(0)
    target_js = defaultdict(list)
    for i in protocol['old_ambiguous_orbit_indices']:
        rep = old[i]
        P0 = rd.E(0) if rep == (-1, -1) else rd.E([rep[0], rep[1], 1])
        for k in range(5):
            P = P0 + k*T
            j = rd.j(P)
            if j is not None:
                target_js[int(j)].append({'orbit_index': i, 'translate': k, 'point': key(P)})
    field = GF(20023)
    R = PolynomialRing(field, 'Y')
    Y = R.gen()
    outcomes = {}
    for ell in protocol['degrees']:
        print(json.dumps({'degree': ell, 'stage': 'building_modular_polynomial'}), flush=True)
        phi = classical_modular_polynomial(ell)
        candidate_sources = defaultdict(set)
        reverse_root_counts = {}
        for tj in sorted(target_js):
            # Classical modular polynomials are symmetric in their two inputs.
            roots = R(phi(field(tj), Y)).roots()
            reverse_root_counts[tj] = sum(int(m) for _, m in roots)
            for sj, _ in roots:
                if int(sj) in source_js:
                    candidate_sources[int(sj)].add(tj)
        rows = []
        for sj, linked_targets in sorted(candidate_sources.items()):
            roots = R(phi(field(sj), Y)).roots()
            root_values = {int(x) for x, _ in roots}
            count = sum(int(m) for _, m in roots)
            assert linked_targets <= root_values
            rows.append({'source_j': sj, 'source_count': source_js[sj]['source_count'],
                         'rational_root_multiplicity': count,
                         'distinct_rational_roots': len(roots),
                         'linked_target_js': sorted(linked_targets),
                         'fully_split': count == ell + 1})
        passes = [r for r in rows if r['fully_split']]
        outcomes[str(ell)] = {
            'target_j_count': len(target_js),
            'reverse_root_counts': reverse_root_counts,
            'candidate_source_j_count': len(rows),
            'candidate_source_point_count': sum(r['source_count'] for r in rows),
            'fully_split_source_j_count': len(passes),
            'fully_split_source_point_count': sum(r['source_count'] for r in passes),
            'fully_split_adjacencies': passes,
            'candidate_rows': rows,
        }
        print(json.dumps({'degree': ell, 'candidate_j': len(rows),
                          'fully_split_j': len(passes)}), flush=True)
    result = {'status': 'TARGETED_MODPOLY_SCREEN_PRODUCED',
              'protocol_sha256': digest(protocol_path),
              'source_sha256': source_hashes,
              'p': 20023, 'degrees': protocol['degrees'],
              'target_js': {str(j): v for j, v in sorted(target_js.items())},
              'outcomes': outcomes, 'candidate_id': None, 'timing_claim': None}
    (HERE / 'result.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')

if __name__ == '__main__':
    main()
