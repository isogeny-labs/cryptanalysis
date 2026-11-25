"""Replay the frozen partial cold-work panel in COLD_NETWORK_PROTOCOL.md."""

import json

from sage.all import EllipticCurve, GF, matrix, vector

from network_hits import BOUND, DEGREES, ORDER, PRIME, bounded_points


TARGET_SCALAR = 137


def key(point):
    return tuple(int(coordinate) for coordinate in point.xy())


def sign_variables(points):
    assert all(point != point.curve()(0) for point in points)
    assert {-point for point in points} == points
    canonical = sorted(
        {min((point, -point), key=key) for point in points}, key=key
    )
    columns = {point: index for index, point in enumerate(canonical)}
    assert len(canonical) * 2 == len(points)
    return canonical, columns


def build_table(points):
    ordered = sorted(points, key=key)
    table = {}
    additions = 0
    for i, p in enumerate(ordered):
        for q in ordered[i:]:
            total = p + q
            additions += 1
            table.setdefault(total, (p, q))
    assert additions == len(points) * (len(points) + 1) // 2
    return table, additions


def equation(pair, columns):
    row = [0] * len(columns)
    for point in pair:
        canonical = min((point, -point), key=key)
        row[columns[canonical]] += 1 if point == canonical else -1
    return row


def collect_relations(table, columns, generator):
    field = GF(ORDER)
    independent_rows = []
    independent_rhs = []
    hit_equations = 0
    attempts = 0
    for scalar in range(1, ORDER):
        if scalar == TARGET_SCALAR:
            continue
        attempts += 1
        pair = table.get(scalar * generator)
        if pair is None:
            continue
        assert scalar * generator == pair[0] + pair[1]
        hit_equations += 1
        row = equation(pair, columns)
        candidate = matrix(field, [*independent_rows, row])
        if candidate.rank() > len(independent_rows):
            independent_rows.append(row)
            independent_rhs.append(scalar)
        if len(independent_rows) == len(columns):
            break

    full_rank = len(independent_rows) == len(columns)
    logs = None
    if full_rank:
        system = matrix(field, independent_rows)
        logs = system.solve_right(vector(field, independent_rhs))
        for point, index in columns.items():
            assert int(logs[index]) * generator == point
    return {
        "attempts": attempts,
        "hit_equations": hit_equations,
        "rank": len(independent_rows),
        "full_rank": full_rank,
        "target_excluded": True,
    }, logs


def descend(arms, target, generator):
    calls = 0
    for offset in range(ORDER):
        trial = target + offset * generator
        for index, arm in arms:
            calls += 1
            pair = arm["table"].get(trial)
            if pair is None:
                continue
            logs = arm["logs"]
            columns = arm["columns"]
            row = equation(pair, columns)
            recovered = int(
                sum(coefficient * logs[j] for j, coefficient in enumerate(row))
                - offset
            ) % ORDER
            assert recovered * generator == target
            assert recovered == TARGET_SCALAR
            return {
                "arm_index": index,
                "offset": offset,
                "calls": calls,
                "recovered_scalar": recovered,
            }
    raise AssertionError("Full-rank arms failed to descend the target")


def main():
    field = GF(PRIME)
    curve = EllipticCurve(field, [-3, 7])
    assert int(curve.order()) == ORDER and curve.order().is_prime()
    generator = curve.gens()[0]
    assert generator.order() == ORDER
    target = TARGET_SCALAR * generator
    network = [
        (degree, phi)
        for degree in DEGREES
        for phi in curve.isogenies_prime_degree(degree)
    ]
    assert [degree for degree, _ in network] == [7, 11, 11, 19, 19]
    sets = [bounded_points(curve, field)]
    for degree, phi in network:
        points = bounded_points(phi.codomain(), field)
        inverse = pow(degree, -1, ORDER)
        pulled = {inverse * phi.dual()(q) for q in points}
        assert len(pulled) == len(points)
        assert all(phi(p) in points for p in pulled)
        sets.append(pulled)

    arms = []
    for index, points in enumerate(sets):
        canonical, columns = sign_variables(points)
        table, additions = build_table(points)
        relation, logs = collect_relations(table, columns, generator)
        arms.append({
            "index": index,
            "label": "base" if index == 0 else f"isogeny_{index}",
            "degree": None if index == 0 else network[index - 1][0],
            "factor_base_points": len(points),
            "sign_variables": len(canonical),
            "table_additions": additions,
            "distinct_hits": len(table),
            "relation": relation,
            "table": table,
            "columns": columns,
            "logs": logs,
        })

    def selected(indices):
        available = [(i, arms[i]) for i in indices if arms[i]["logs"] is not None]
        assert len(available) == len(indices)
        return {
            "table_additions": sum(arms[i]["table_additions"] for i in indices),
            "relation_queries": sum(arms[i]["relation"]["attempts"] for i in indices),
            "target_descent": descend(available, target, generator),
        }

    result = {
        "field_prime": PRIME,
        "curve_a4_a6": [-3, 7],
        "curve_order": ORDER,
        "coordinate_bound": BOUND,
        "target_scalar_verification_only": TARGET_SCALAR,
        "generator_xy": key(generator),
        "target_xy": key(target),
        "network_degrees": [degree for degree, _ in network],
        "arms": [
            {k: v for k, v in arm.items() if k not in ("table", "columns", "logs")}
            for arm in arms
        ],
        "base_reference": selected([0]),
        "strongest_single_arm": selected([5]),
        "five_arm_network": selected([1, 2, 3, 4, 5]),
    }
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
