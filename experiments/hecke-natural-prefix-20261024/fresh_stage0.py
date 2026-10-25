"""Rebuild the first p20023 trace-64 Hecke frontier from source mathematics."""
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import sys
import time
from sage.all import EllipticCurve_from_j, classical_modular_polynomial

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
MODULE = ROOT / 'hecke-two-sheet-small-order-20261023/tools/hecke11.py'
sys.path.insert(0, str(MODULE.parent))
import hecke11 as H  # noqa: E402


def sha(path):
    return sha256(path.read_bytes()).hexdigest()


def key(point):
    return (-1, -1) if point.is_zero() else (int(point[0]), int(point[1]))


def main():
    protocol_path = HERE / 'fresh_protocol.json'
    protocol = json.loads(protocol_path.read_text())
    assert protocol['status'] == 'FROZEN_BEFORE_STAGE0_FRESH_REBUILD'
    paths = {
        'hecke11': MODULE,
        'saved_frontier': ROOT / 'hecke-torsion-frontiers-20261024/p20023.result.json',
        'saved_seed': ROOT / 'hecke-torsion-frontiers-20261024/p20023.seed.result.json',
    }
    t0 = time.monotonic_ns()
    funcs, jfun = H.build([2, 3])
    reduced = H.Reduced(20023, funcs, jfun, [2, 3])
    torsion = reduced.E([5, 5, 1])
    assert 5 * torsion == reduced.E(0)
    t1 = time.monotonic_ns()
    def orbit(point):
        return min(key(point + k * torsion) for k in range(5))
    traces = {}
    sources = []
    for point in reduced.E:
        j = reduced.j(point)
        if j is None:
            continue
        jvalue = int(j)
        if jvalue not in traces:
            traces[jvalue] = abs(int(EllipticCurve_from_j(j).trace_of_frobenius()))
        if traces[jvalue] == 64:
            sources.append(point)
    seed_orbits = sorted({orbit(point) for point in sources})
    assert len(sources) == protocol['expected_seed_sources']
    assert len(seed_orbits) == 564
    t2 = time.monotonic_ns()
    phi = {degree: classical_modular_polynomial(degree) for degree in (2, 3)}
    def evaluate(points):
        counts = Counter()
        accepted = []
        for point in points:
            j = reduced.j(point)
            if j is None:
                counts['SOURCE_UNDEFINED_J'] += 1
                continue
            for degree in (2, 3):
                roots = reduced.neighbour_x(degree, point).roots()
                if sum(int(multiplicity) for _, multiplicity in roots) != degree + 1:
                    counts[f'L{degree}_NOT_ALL_RATIONAL'] += 1
                    continue
                neighbors = reduced.neighbours_all(degree, point)
                if neighbors is None or len(neighbors) != degree + 1:
                    counts[f'L{degree}_UNRESOLVED_NEIGHBOURS'] += 1
                    continue
                if any(reduced.j(q) is None for q in neighbors):
                    counts[f'L{degree}_CUSP_NEIGHBOUR'] += 1
                    continue
                assert sum(neighbors, reduced.E(0)) == reduced.a_l[degree] * point
                assert all(phi[degree](j, reduced.j(q)) == 0 for q in neighbors)
                coefficients = Counter(orbit(q) for q in neighbors)
                coefficients[orbit(point)] -= int(reduced.a_l[degree])
                accepted.append({
                    'source': key(point), 'degree': degree,
                    'neighbours': [key(q) for q in neighbors],
                    'coefficients_keyed': {rep: value for rep, value in coefficients.items() if value},
                })
                counts[f'L{degree}_ACCEPTED'] += 1
        return counts, accepted
    seed_counts, seed_records = evaluate(sorted(sources, key=key))
    assert len(seed_records) == protocol['expected_seed_rows']
    t3 = time.monotonic_ns()
    def point(rep):
        return reduced.E(0) if rep == (-1, -1) else reduced.E([*rep, 1])
    frontier_sources = [point(rep) + k * torsion for rep in seed_orbits for k in range(5)]
    assert len(frontier_sources) == len({key(point) for point in frontier_sources}) == protocol['expected_frontier_sources']
    frontier_counts, frontier_records = evaluate(frontier_sources)
    assert len(frontier_records) == protocol['expected_frontier_rows']
    t4 = time.monotonic_ns()
    new_orbits = sorted({rep for record in frontier_records for rep in record['coefficients_keyed']} - set(seed_orbits))
    columns = sorted(set(seed_orbits) | set(new_orbits))
    assert len(columns) == protocol['expected_columns']
    local = {rep: i for i, rep in enumerate(columns)}
    def encode(records):
        return [{
            'source': record['source'], 'degree': record['degree'],
            'neighbours': record['neighbours'],
            'coefficients': {str(local[rep]): value for rep, value in record['coefficients_keyed'].items()},
        } for record in records]
    seed_encoded, frontier_encoded = encode(seed_records), encode(frontier_records)
    saved_frontier = json.loads(paths['saved_frontier'].read_text())
    saved_seed = json.loads(paths['saved_seed'].read_text())
    full_keys = [tuple(rep) for rep in saved_frontier['column_representatives']]
    def canonical(records, saved=False):
        values = []
        for record in records:
            coeff = record['coefficients']
            if saved:
                coeff = {str(local[full_keys[int(j)]]): v for j, v in coeff.items()}
            values.append((tuple(record['source']), int(record['degree']),
                           tuple(sorted(tuple(q) for q in record['neighbours'])),
                           tuple(sorted((int(j), int(v)) for j, v in coeff.items()))))
        return sorted(values)
    assert seed_orbits == [tuple(rep) for rep in saved_frontier['boundary_representatives']['seed']]
    assert new_orbits == [tuple(rep) for rep in saved_frontier['stages'][0]['new_representatives']]
    assert dict(seed_counts) == saved_seed['status_counts']
    assert dict(frontier_counts) == saved_frontier['stages'][0]['status_counts']
    assert canonical(seed_encoded) == canonical(saved_seed['accepted_rows'], saved=True)
    assert canonical(frontier_encoded) == canonical(saved_frontier['stages'][0]['accepted_rows'], saved=True)
    t5 = time.monotonic_ns()
    output = {
        'status': 'PASS_FRESH_STAGE0_SOURCE_REBUILD',
        'protocol_sha256': sha(protocol_path),
        'source_sha256': {label: sha(path) for label, path in paths.items()},
        'seed_source_points': len(sources), 'seed_orbits': len(seed_orbits),
        'seed_status_counts': dict(seed_counts), 'seed_rows': seed_encoded,
        'frontier_source_points': len(frontier_sources),
        'frontier_status_counts': dict(frontier_counts), 'frontier_rows': frontier_encoded,
        'new_orbits': new_orbits, 'column_representatives': columns,
        'phase_wall_ns_diagnostic': {
            'hecke_function_setup': t1 - t0,
            'trace_seed_enumeration': t2 - t1,
            'seed_relation_queries': t3 - t2,
            'frontier_relation_queries': t4 - t3,
            'assembly_and_saved_ledger_comparison': t5 - t4,
        },
        'candidate_id': None, 'timing_claim': None,
    }
    (HERE / 'fresh_result.json').write_text(json.dumps(output, indent=2, sort_keys=True) + '\n')
    print(json.dumps({k: output[k] for k in ('status', 'seed_source_points', 'seed_orbits',
                                            'frontier_source_points')}, sort_keys=True), flush=True)


if __name__ == '__main__':
    main()
