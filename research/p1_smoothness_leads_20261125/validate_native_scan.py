"""Independent replay of every archived native scan record and query identity."""

import base64
import gzip
import hashlib
import json
import math
import re
from collections import Counter
from pathlib import Path

from sage.all import EllipticCurve, GF


HERE = Path(__file__).resolve().parent
OUT = HERE / "native_scan"
ORDER = 10193
TARGET_SCALAR = 7001
F4_ROW = re.compile(r"^\s*(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+x\s+(\d+)\s+", re.M)
IDEAL_DEGREE = re.compile(r"degree of ideal\s+(\d+)")
ROUTES = {
    "base_reference": [0],
    "strongest_single_arm": [5],
    "five_arm_network": [1, 2, 3, 4, 5],
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def arms_and_generator():
    field = GF(10007)
    curve = EllipticCurve(field, [-3, 7])
    generator = curve.gens()[0]
    network = [
        (ell, phi)
        for ell in (2, 3, 5, 7, 11, 13, 17, 19)
        for phi in curve.isogenies_prime_degree(ell)
    ]
    assert [ell for ell, _ in network] == [7, 11, 11, 19, 19]
    arms = []
    for _, phi in [(None, None), *network]:
        codomain = curve if phi is None else phi.codomain()
        points = {
            p for x in range(20)
            for p in codomain.lift_x(field(x), all=True)
        }
        sum_pairs = {}
        for p in points:
            for q in points:
                sum_pairs.setdefault(p + q, set()).add((int(p[0]), int(q[0])))
        arms.append((phi, sum_pairs))
    return generator, arms


def expected_queries(name, v2):
    if name.startswith("precompute_arm"):
        index = int(name.removeprefix("precompute_arm"))
        count = v2["arms"][index]["relation"]["attempts"]
        scalars = [s for s in range(1, ORDER) if s != TARGET_SCALAR][:count]
        return [(index, s) for s in scalars]
    route = name.removeprefix("descent_")
    indices = ROUTES[route]
    count = v2[route]["target_descent"]["calls"]
    return [
        (indices[i % len(indices)], (TARGET_SCALAR + i // len(indices)) % ORDER)
        for i in range(count)
    ]


def validate_record(record, index, scalar, generator, arms):
    assert record["arm_index"] == index and record["base_scalar"] == scalar
    assert record["exit_code"] == 0 and record["valid"]
    data = {
        suffix: base64.b64decode(record[f"{suffix}_b64"], validate=True)
        for suffix in ("input", "log", "output")
    }
    for suffix, raw in data.items():
        assert sha(raw) == record[f"{suffix}_sha256"]
    assert data["input"].startswith(b"x1,x2\n10007\n")
    assert data["input"].endswith(b"\n")

    point = scalar * generator
    phi, sums = arms[index]
    if phi is not None:
        point = phi(point)
    assert record["target_x"] == int(point[0])
    expected = len(sums.get(point, set()))
    assert record["expected_x_solutions"] == expected

    log = data["log"].decode()
    rows = [tuple(map(int, m.groups())) for m in F4_ROW.finditer(log)]
    degrees = [int(s) for s in IDEAL_DEGREE.findall(log)]
    ideal_degree = degrees[-1] if degrees else 0
    if not degrees:
        assert "No solution" in log and data["output"].strip() == b"[-1]:"
    assert record["ideal_degree"] == ideal_degree == expected
    assert record["f4_rounds"] == len(rows) and rows
    assert record["max_step_degree"] == max(row[0] for row in rows)
    assert record["max_matrix_rows"] == max(row[3] for row in rows)
    assert record["max_matrix_columns"] == max(row[4] for row in rows)
    assert record["wall_seconds"] >= 0 and record["cpu_seconds"] >= 0


def main():
    v2 = json.loads((HERE / "cold_network_v2.json").read_text())
    aggregate = json.loads((OUT / "summary.json").read_text())
    generator, arms = arms_and_generator()
    counts = {}
    total = 0
    for name, shard_record in aggregate["shards"].items():
        archive = (OUT / f"{name}.jsonl.gz").read_bytes()
        summary = json.loads((OUT / f"{name}.summary.json").read_text())
        assert sha(archive) == summary["archive_sha256"] == shard_record["archive_sha256"]
        records = [json.loads(line) for line in gzip.decompress(archive).splitlines()]
        queries = expected_queries(name, v2)
        assert len(records) == len(queries) == summary["calls"] == summary["valid_calls"]
        assert records and len(records) == len(summary["records"])
        for ordinal, (record, (index, scalar), stripped) in enumerate(
            zip(records, queries, summary["records"]), 1
        ):
            assert record["ordinal"] == ordinal
            assert {k: v for k, v in record.items() if not k.endswith("_b64")} == stripped
            validate_record(record, index, scalar, generator, arms)
        assert dict(Counter(str(r["ideal_degree"]) for r in records)) == summary["ideal_degree_counts"]
        assert math.isclose(sum(r["wall_seconds"] for r in records), summary["wall_seconds"], abs_tol=1e-9)
        assert math.isclose(sum(r["cpu_seconds"] for r in records), summary["cpu_seconds"], abs_tol=1e-9)
        counts[name] = len(records)
        total += len(records)

    assert total == 7160
    for route, indices in ROUTES.items():
        expected = sum(counts[f"precompute_arm{i}"] for i in indices)
        row = aggregate["routes"][route]
        assert row["precomputation_calls"] == expected
        assert row["descent_calls"] == counts[f"descent_{route}"]
        assert row["total_native_calls"] == expected + row["descent_calls"]
        assert row["valid_calls"] == row["total_native_calls"]
    print(json.dumps({"all_valid": True, "physical_calls_checked": total,
                      "shard_calls": counts, "route_calls_checked": True}, sort_keys=True))


if __name__ == "__main__":
    main()
