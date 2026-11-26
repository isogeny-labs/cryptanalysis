"""Run checkpointed native msolve calls from NATIVE_SCAN_PROTOCOL.md.

Usage: sage -python native_scan.py precompute ARM_INDEX
       sage -python native_scan.py descent ROUTE_NAME
       sage -python native_scan.py summarize
"""

import base64
import gzip
import hashlib
import json
import re
import resource
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

from network_hits import BOUND, DEGREES, ORDER, PRIME, bounded_points


HERE = Path(__file__).resolve().parent
OUT = HERE / "native_scan"
V2 = json.loads((HERE / "cold_network_v2.json").read_text())
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


def semaev3(x, y, z, a, b):
    return (
        (x - y) ** 2 * z**2
        - 2 * ((x + y) * (x * y + a) + 2 * b) * z
        + (x * y - a) ** 2
        - 4 * b * (x + y)
    )


def make_arms():
    field = GF(PRIME)
    base = EllipticCurve(field, [-3, 7])
    assert int(base.order()) == ORDER
    generator = base.gens()[0]
    target = TARGET_SCALAR * generator
    assert [int(v) for v in target.xy()] == V2["target_xy"]
    network = [
        (degree, phi)
        for degree in DEGREES
        for phi in base.isogenies_prime_degree(degree)
    ]
    assert [degree for degree, _ in network] == [7, 11, 11, 19, 19]
    result = []
    for index, (degree, phi) in enumerate([(None, None), *network]):
        curve = base if phi is None else phi.codomain()
        points = bounded_points(curve, field)
        roots = sorted({int(p[0]) for p in points})
        assert len(points) == 2 * len(roots)
        sums = {}
        for p in points:
            for q in points:
                sums.setdefault(p + q, set()).add((int(p[0]), int(q[0])))
        ring = PolynomialRing(field, names=("x1", "x2"))
        x1, x2 = ring.gens()
        result.append({
            "index": index,
            "curve": curve,
            "phi": phi,
            "degree": degree,
            "roots": roots,
            "sums": sums,
            "ring": ring,
            "x1": x1,
            "x2": x2,
            "base_polynomial_x1": ring.prod(x1 - field(x) for x in roots),
            "base_polynomial_x2": ring.prod(x2 - field(x) for x in roots),
        })
    return generator, target, result


def input_for(arm, point):
    curve = arm["curve"]
    x1, x2 = arm["x1"], arm["x2"]
    a, b = curve.a4(), curve.a6()
    z = point[0]
    polynomials = [
        semaev3(x1, x2, z, a, b),
        arm["base_polynomial_x1"],
        arm["base_polynomial_x2"],
    ]
    return ("x1,x2\n10007\n" + ",\n".join(str(f) for f in polynomials) + "\n").encode()


def run_call(arm, scalar, generator, scratch_input, scratch_output):
    base_point = scalar * generator
    point = base_point if arm["phi"] is None else arm["phi"](base_point)
    expected = len(arm["sums"].get(point, set()))
    input_bytes = input_for(arm, point)
    scratch_input.write_bytes(input_bytes)
    scratch_output.unlink(missing_ok=True)
    before = resource.getrusage(resource.RUSAGE_CHILDREN)
    start = time.monotonic()
    proc = subprocess.run(
        ["msolve", "-f", str(scratch_input), "-o", str(scratch_output), "-t", "1", "-v", "2"],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False,
    )
    wall = time.monotonic() - start
    after = resource.getrusage(resource.RUSAGE_CHILDREN)
    cpu = after.ru_utime + after.ru_stime - before.ru_utime - before.ru_stime
    log = proc.stdout
    output = scratch_output.read_bytes() if scratch_output.exists() else b""
    decoded = log.decode(errors="replace")
    rows = [tuple(map(int, m.groups())) for m in F4_ROW.finditer(decoded)]
    degrees = [int(x) for x in IDEAL_DEGREE.findall(decoded)]
    ideal_degree = degrees[-1] if degrees else 0
    valid_zero = bool(degrees) or ("No solution" in decoded and output.strip() == b"[-1]:")
    valid = proc.returncode == 0 and valid_zero and ideal_degree == expected
    record = {
        "arm_index": arm["index"],
        "base_scalar": scalar,
        "target_x": int(point[0]),
        "expected_x_solutions": expected,
        "ideal_degree": ideal_degree,
        "exit_code": proc.returncode,
        "valid": valid,
        "wall_seconds": wall,
        "cpu_seconds": cpu,
        "f4_rounds": len(rows),
        "max_step_degree": max((row[0] for row in rows), default=None),
        "max_matrix_rows": max((row[3] for row in rows), default=None),
        "max_matrix_columns": max((row[4] for row in rows), default=None),
        "input_sha256": sha(input_bytes),
        "log_sha256": sha(log),
        "output_sha256": sha(output),
        "input_b64": base64.b64encode(input_bytes).decode(),
        "log_b64": base64.b64encode(log).decode(),
        "output_b64": base64.b64encode(output).decode(),
    }
    return record


def write_shard(name, queries, generator, arms):
    OUT.mkdir(exist_ok=True)
    archive = OUT / f"{name}.jsonl.gz"
    summary_file = OUT / f"{name}.summary.json"
    assert not archive.exists() and not summary_file.exists()
    temporary = OUT / f"{name}.jsonl.gz.partial"
    scratch_input = OUT / "scratch.ms"
    scratch_output = OUT / "scratch.out"
    assert not temporary.exists()
    summaries = []
    with temporary.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0, compresslevel=9) as zipped:
            for ordinal, (index, scalar) in enumerate(queries, 1):
                record = run_call(arms[index], scalar, generator, scratch_input, scratch_output)
                record["ordinal"] = ordinal
                zipped.write((json.dumps(record, sort_keys=True) + "\n").encode())
                summaries.append({k: v for k, v in record.items() if not k.endswith("_b64")})
                if ordinal % 250 == 0:
                    print(f"{name}: {ordinal}/{len(queries)} calls", flush=True)
    scratch_input.unlink(missing_ok=True)
    scratch_output.unlink(missing_ok=True)
    temporary.rename(archive)
    summary = {
        "name": name,
        "calls": len(summaries),
        "valid_calls": sum(entry["valid"] for entry in summaries),
        "wall_seconds": sum(entry["wall_seconds"] for entry in summaries),
        "cpu_seconds": sum(entry["cpu_seconds"] for entry in summaries),
        "ideal_degree_counts": dict(Counter(str(entry["ideal_degree"]) for entry in summaries)),
        "max_step_degree": max((entry["max_step_degree"] or 0 for entry in summaries), default=0),
        "archive_sha256": sha(archive.read_bytes()),
        "records": summaries,
    }
    summary_file.write_text(json.dumps(summary, sort_keys=True) + "\n")
    print(json.dumps({k: v for k, v in summary.items() if k != "records"}, sort_keys=True), flush=True)


def summarize():
    names = [f"precompute_arm{i}" for i in range(6)] + [
        f"descent_{name}" for name in ROUTES
    ]
    shards = {
        name: json.loads((OUT / f"{name}.summary.json").read_text())
        for name in names
    }
    for name, shard in shards.items():
        assert shard["name"] == name
        assert shard["calls"] == len(shard["records"])
        assert shard["valid_calls"] == shard["calls"]
        assert sha((OUT / f"{name}.jsonl.gz").read_bytes()) == shard["archive_sha256"]

    routes = {}
    for route_name, indices in ROUTES.items():
        selected = [shards[f"precompute_arm{i}"] for i in indices]
        descent = shards[f"descent_{route_name}"]
        routes[route_name] = {
            "precomputation_calls": sum(s["calls"] for s in selected),
            "descent_calls": descent["calls"],
            "total_native_calls": sum(s["calls"] for s in selected) + descent["calls"],
            "precomputation_wall_seconds": sum(s["wall_seconds"] for s in selected),
            "descent_wall_seconds": descent["wall_seconds"],
            "precomputation_cpu_seconds": sum(s["cpu_seconds"] for s in selected),
            "descent_cpu_seconds": descent["cpu_seconds"],
            "valid_calls": sum(s["valid_calls"] for s in selected) + descent["valid_calls"],
            "table_build_additions_separate_unit": V2[route_name]["table_additions"],
        }
        routes[route_name]["total_wall_seconds"] = (
            routes[route_name]["precomputation_wall_seconds"]
            + routes[route_name]["descent_wall_seconds"]
        )
        routes[route_name]["total_cpu_seconds"] = (
            routes[route_name]["precomputation_cpu_seconds"]
            + routes[route_name]["descent_cpu_seconds"]
        )
        assert routes[route_name]["precomputation_calls"] == V2[route_name]["relation_queries"]
        assert routes[route_name]["descent_calls"] == V2[route_name]["target_descent"]["calls"]
    result = {
        "field_prime": PRIME,
        "curve_order": ORDER,
        "target_scalar_verification_only": TARGET_SCALAR,
        "msolve_version": "0.11.0",
        "shards": {
            name: {k: v for k, v in shard.items() if k != "records"}
            for name, shard in shards.items()
        },
        "routes": routes,
    }
    (OUT / "summary.json").write_text(json.dumps(result, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))


def main():
    mode = sys.argv[1]
    if mode == "summarize":
        assert len(sys.argv) == 2
        summarize()
        return
    assert len(sys.argv) == 3
    generator, target, arms = make_arms()
    argument = sys.argv[2]
    if mode == "precompute":
        index = int(argument)
        attempts = V2["arms"][index]["relation"]["attempts"]
        scalars = [s for s in range(1, ORDER) if s != TARGET_SCALAR][:attempts]
        assert len(scalars) == attempts
        write_shard(f"precompute_arm{index}", [(index, s) for s in scalars], generator, arms)
    elif mode == "descent":
        indices = ROUTES[argument]
        count = V2[argument]["target_descent"]["calls"]
        queries = [
            (indices[call % len(indices)], (TARGET_SCALAR + call // len(indices)) % ORDER)
            for call in range(count)
        ]
        assert queries[-1][0] == V2[argument]["target_descent"]["arm_index"]
        write_shard(f"descent_{argument}", queries, generator, arms)
    else:
        raise ValueError(mode)


if __name__ == "__main__":
    main()
