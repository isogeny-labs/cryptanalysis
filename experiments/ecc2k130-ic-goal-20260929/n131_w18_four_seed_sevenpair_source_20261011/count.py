"""Exact folded-column matching count for seven four-seed W18 pairs."""

import hashlib
import itertools
import json
import math
from collections import Counter, defaultdict
from fractions import Fraction
from functools import lru_cache
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SUPPORT = ROOT / "n131_w16_w18_sixpair_width_gate_20261010" / "support_w18.tsv"
AFFINE = ROOT / "n41_n131_affine_four_seed_m16_20261011" / "support_result.json"
TERMINAL = ROOT / "n131_w18_all_fibers_inverse_20261011" / "protocol.json"
FIXED = ROOT / "n131_w18_terminal_fiber_20261011" / "source_count.json"
R = 680564733841876926932320129493409985129
SEEDS = (212, 213, 214, 215)
LIMIT = 8


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def multiply(a, b):
    out = [0] * (LIMIT + 1)
    for i, x in enumerate(a):
        if x:
            for j, y in enumerate(b[:LIMIT + 1 - i]):
                out[i + j] += x * y
    return tuple(out)


def quotient(a, b):
    assert b[0] == 1
    out = [0] * (LIMIT + 1)
    for k in range(LIMIT + 1):
        out[k] = a[k] - sum(b[j] * out[k - j] for j in range(1, k + 1))
    assert multiply(out, b) == a
    return tuple(out)


def edges_for(columns, seeds):
    edges = Counter()
    per_seed = {}
    for seed in seeds:
        count = 0
        for mask, left in columns.items():
            other = mask ^ seed
            if mask < other and other in columns:
                right = columns[other]
                if left != right:
                    edges[tuple(sorted((left, right)))] += 1
                    count += 1
        per_seed[str(seed)] = count
    return edges, per_seed


def components(edges):
    parent = {vertex: vertex for edge in edges for vertex in edge}

    def find(vertex):
        while parent[vertex] != vertex:
            parent[vertex] = parent[parent[vertex]]
            vertex = parent[vertex]
        return vertex

    for left, right in edges:
        parent[find(left)] = find(right)
    groups = defaultdict(list)
    for edge, multiplicity in edges.items():
        groups[find(edge[0])].append((*edge, multiplicity))
    by_vertex = {vertex: find(vertex) for vertex in parent}
    return list(groups.values()), by_vertex


def polynomial(edges, removed=(), limit=LIMIT):
    vertices = sorted({v for a, b, _ in edges for v in (a, b)} - set(removed))
    index = {vertex: i for i, vertex in enumerate(vertices)}
    neighbors = [dict() for _ in vertices]
    for left, right, weight in edges:
        if left in index and right in index:
            a, b = index[left], index[right]
            neighbors[a][b] = neighbors[a].get(b, 0) + weight
            neighbors[b][a] = neighbors[b].get(a, 0) + weight

    @lru_cache(None)
    def visit(mask):
        if not mask:
            return (1,) + (0,) * limit
        # A high-degree pivot keeps rare merged components small.
        pivot = max((v for v in range(len(vertices)) if mask >> v & 1),
                    key=lambda v: sum(mask >> u & 1 for u in neighbors[v]))
        rest = mask ^ (1 << pivot)
        out = list(visit(rest))
        for vertex, weight in neighbors[pivot].items():
            if rest >> vertex & 1:
                term = visit(rest ^ (1 << vertex))
                for k in range(1, limit + 1):
                    out[k] += weight * term[k - 1]
        return tuple(out)

    return visit((1 << len(vertices)) - 1)


def count_conditioned(edge_map, terminal_edges, degree):
    groups, owner = components(edge_map)
    polys = [polynomial(group) for group in groups]
    product = (1,) + (0,) * LIMIT
    for poly in polys:
        product = multiply(product, poly)
    index_by_root = {owner[vertex]: i for i, group in enumerate(groups)
                     for edge in group for vertex in edge[:2]}
    out = []
    for left, right in terminal_edges:
        touched = {index_by_root[owner[v]] for v in (left, right) if v in owner}
        old = (1,) + (0,) * LIMIT
        new = old
        for i in sorted(touched):
            old = multiply(old, polys[i])
            new = multiply(new, polynomial(groups[i], (left, right)))
        row = multiply(quotient(product, old), new)
        out.append(row[degree])
    return out, groups, product


def validate_small_components(groups):
    checks = 0
    for group in groups:
        vertices = {v for a, b, _ in group for v in (a, b)}
        if len(vertices) > 8:
            continue
        # Direct edge-subset enumeration independently checks the recursion.
        choices = []
        for left, right, weight in group:
            choices.extend([(left, right)] * weight)
        if len(choices) > 15:
            continue
        direct = [0] * (LIMIT + 1)
        for k in range(min(LIMIT, len(choices)) + 1):
            for selected in itertools.combinations(choices, k):
                used = [v for edge in selected for v in edge]
                direct[k] += len(set(used)) == len(used)
        assert tuple(direct) == polynomial(group)
        checks += 1
    return checks


def main():
    columns = {int(a): int(b) for a, b in
               (line.split() for line in SUPPORT.read_text().splitlines())}
    affine = json.loads(AFFINE.read_text())
    terminal = json.loads(TERMINAL.read_text())
    fixed = json.loads(FIXED.read_text())
    assert len(columns) == 131307
    assert terminal["terminal_state_count"] == 32
    assert terminal["residual_choices"] == 128
    edge_map, per_seed = edges_for(columns, SEEDS)
    assert per_seed == affine["n131"]["per_seed_unordered_pairs"]
    terminal_edges = [tuple(row["folded_columns"])
                      for row in terminal["terminal_pool"]]
    assert len(terminal_edges) == 32
    counts, groups, all_poly = count_conditioned(edge_map, terminal_edges, 7)
    checked = validate_small_components(groups)
    assert checked > 25000

    fixed_map, fixed_per_seed = edges_for(columns, (212,))
    assert fixed_per_seed["212"] == 33191
    fixed_edges = [tuple(row["folded_columns"])
                   for row in fixed["conditional_edge_rows"]]
    original, _, _ = count_conditioned(fixed_map, fixed_edges, 8)
    assert original == [row["eight_pair_matchings"]
                        for row in fixed["conditional_edge_rows"]]

    labeled = sum(counts) * math.factorial(7) * 4**7
    four_fiber_mean = Fraction(4 * labeled, R)
    naive = Fraction(4 * 32 * (4 * sum(per_seed.values()))**7, R)
    result = {
        "status": "PASS_EXACT_FOUR_SEED_SEVENPAIR_MATCHING_COUNT",
        "candidate_id": None,
        "curve_id": terminal["curve_id"],
        "seeds": list(SEEDS),
        "free_pair_slots": 7,
        "terminal_states": 32,
        "raw_fibers": 4,
        "per_seed_unordered_pairs": per_seed,
        "folded_column_edges_with_multiplicity": sum(edge_map.values()),
        "distinct_folded_column_edges": len(edge_map),
        "component_count": len(groups),
        "max_component_vertices": max(len({v for a, b, _ in group for v in (a, b)})
                                      for group in groups),
        "directly_enumerated_component_checks": checked,
        "full_graph_matching_polynomial_through_degree_8": [str(v) for v in all_poly],
        "terminal_conditioned_unordered_seven_edge_matchings": [str(v) for v in counts],
        "distinct_column_ordered_signed_tuples": str(labeled),
        "uniform_public_point_mean_upper_exact":
            f"{four_fiber_mean.numerator}/{four_fiber_mean.denominator}",
        "uniform_public_point_mean_upper_decimal": format(float(four_fiber_mean), ".12g"),
        "naive_without_column_exclusions_exact":
            f"{naive.numerator}/{naive.denominator}",
        "source_sha256": {"counter": sha(Path(__file__)),
                          "support": sha(SUPPORT), "affine_census": sha(AFFINE),
                          "terminal_protocol": sha(TERMINAL),
                          "fixed_seed_reference": sha(FIXED)},
    }
    with (HERE / "result.json").open("x") as stream:
        json.dump(result, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(json.dumps({"status": result["status"],
                      "mean_upper": result["uniform_public_point_mean_upper_decimal"],
                      "components_checked": checked}))


if __name__ == "__main__":
    main()
