"""Generate and run the frozen native network F4 panel.

Use `sage -python native_network.py generate`, then
`sage -python native_network.py run`. The commands write only beneath the
research directory and never alter the frozen protocol.
"""

import gzip
import hashlib
import json
import re
import resource
import subprocess
import sys
import time
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

from network_hits import BOUND, DEGREES, ORDER, PRIME, bounded_points, hit_set


HERE = Path(__file__).resolve().parent
OUTPUT_DIR = HERE / "native"
TARGET_SCALAR = 137
F4_ROW = re.compile(r"^\s*(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+x\s+(\d+)\s+", re.M)
IDEAL_DEGREE = re.compile(r"degree of ideal\s+(\d+)")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def xy(point):
    return [int(value) for value in point.xy()]


def semaev3(x, y, z, a, b):
    return (
        (x - y) ** 2 * z**2
        - 2 * ((x + y) * (x * y + a) + 2 * b) * z
        + (x * y - a) ** 2
        - 4 * b * (x + y)
    )


def arms():
    field = GF(PRIME)
    base = EllipticCurve(field, [-3, 7])
    assert int(base.order()) == ORDER and base.order().is_prime()
    generator = base.gens()[0]
    target = TARGET_SCALAR * generator
    network = [
        (degree, phi)
        for degree in DEGREES
        for phi in base.isogenies_prime_degree(degree)
    ]
    assert [degree for degree, _ in network] == [7, 11, 11, 19, 19]
    for index, pair in enumerate([(None, None), *network]):
        degree, phi = pair
        curve = base if phi is None else phi.codomain()
        point_base = bounded_points(curve, field)
        normalized = (
            point_base if phi is None else
            {pow(degree, -1, ORDER) * phi.dual()(q) for q in point_base}
        )
        assert len(normalized) == len(point_base)
        hits = hit_set(normalized)
        positive = next(
            s for s in range(1, ORDER)
            if s != TARGET_SCALAR and s * generator in hits
        )
        assert target not in hits
        yield {
            "name": "base" if index == 0 else f"isogeny_{index}",
            "degree": degree,
            "curve": curve,
            "point_base": point_base,
            "positive_scalar": positive,
            "positive_target": positive * generator if phi is None else phi(positive * generator),
            "negative_target": target if phi is None else phi(target),
        }


def build_case(arm, case):
    curve = arm["curve"]
    field = curve.base_field()
    target = arm[f"{case}_target"]
    xroots = sorted({int(p[0]) for p in arm["point_base"]})
    assert len(xroots) * 2 == len(arm["point_base"])
    ring = PolynomialRing(field, names=("x1", "x2"))
    x1, x2 = ring.gens()
    a, b = curve.a4(), curve.a6()
    assert curve.a1() == curve.a2() == curve.a3() == 0
    z = target[0]
    polys = [
        semaev3(x1, x2, z, a, b),
        ring.prod(x1 - field(root) for root in xroots),
        ring.prod(x2 - field(root) for root in xroots),
    ]
    input_data = ("x1,x2\n10007\n" + ",\n".join(str(p) for p in polys) + "\n").encode()
    coordinate_pairs = {
        (u, v) for u in xroots for v in xroots
        if semaev3(field(u), field(v), z, a, b) == 0
    }
    group_pairs = {
        (int(p[0]), int(q[0])) for p in arm["point_base"]
        for q in arm["point_base"] if p + q == target
    }
    assert coordinate_pairs == group_pairs
    assert bool(group_pairs) == (case == "positive")
    return input_data, {
        "arm": arm["name"],
        "degree": arm["degree"],
        "case": case,
        "positive_scalar": arm["positive_scalar"],
        "curve_a4_a6": [int(a), int(b)],
        "target_xy": xy(target),
        "factor_base_x": xroots,
        "factor_base_points": len(arm["point_base"]),
        "distinct_x_solutions": len(coordinate_pairs),
        "group_law_x_pairs_equal": True,
        "input_sha256": digest(input_data),
    }


def generate():
    OUTPUT_DIR.mkdir(exist_ok=True)
    cases = []
    for arm in arms():
        for case in ("negative", "positive"):
            input_data, metadata = build_case(arm, case)
            name = f"{arm['name']}_{case}"
            (OUTPUT_DIR / f"{name}.ms").write_bytes(input_data)
            cases.append({"name": name, **metadata})
    record = {
        "field_prime": PRIME,
        "curve_order": ORDER,
        "target_scalar_verification_only": TARGET_SCALAR,
        "msolve_version": subprocess.check_output(["msolve", "-h"], text=True).splitlines()[1],
        "cases": cases,
    }
    (OUTPUT_DIR / "fixture.json").write_text(json.dumps(record, sort_keys=True) + "\n")
    print(json.dumps(record, sort_keys=True))


def run():
    fixture = json.loads((OUTPUT_DIR / "fixture.json").read_text())
    results = []
    for metadata in fixture["cases"]:
        name = metadata["name"]
        input_path = OUTPUT_DIR / f"{name}.ms"
        assert digest(input_path.read_bytes()) == metadata["input_sha256"]
        output_path = OUTPUT_DIR / f"{name}.out"
        before = resource.getrusage(resource.RUSAGE_CHILDREN)
        start = time.monotonic()
        proc = subprocess.run(
            ["msolve", "-f", str(input_path), "-o", str(output_path), "-t", "1", "-v", "2"],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False,
        )
        wall = time.monotonic() - start
        after = resource.getrusage(resource.RUSAGE_CHILDREN)
        cpu = after.ru_utime + after.ru_stime - before.ru_utime - before.ru_stime
        log = proc.stdout
        output = output_path.read_bytes() if output_path.exists() else b""
        rows = [tuple(map(int, match.groups())) for match in F4_ROW.finditer(log.decode(errors="replace"))]
        degrees = [int(x) for x in IDEAL_DEGREE.findall(log.decode(errors="replace"))]
        if degrees:
            ideal_degree = degrees[-1]
        else:
            assert b"No solution" in log and output.strip() == b"[-1]:"
            ideal_degree = 0
        assert proc.returncode == 0 and rows
        assert ideal_degree == metadata["distinct_x_solutions"]
        for suffix, data in (("log", log), ("out", output)):
            with (OUTPUT_DIR / f"{name}.{suffix}.gz").open("wb") as file:
                with gzip.GzipFile(filename="", mode="wb", fileobj=file, mtime=0, compresslevel=9) as zipped:
                    zipped.write(data)
        output_path.unlink()
        results.append({
            "name": name,
            "exit_code": proc.returncode,
            "wall_seconds": round(wall, 6),
            "cpu_seconds": round(cpu, 6),
            "f4_rounds": len(rows),
            "max_step_degree": max(row[0] for row in rows),
            "max_matrix_rows": max(row[3] for row in rows),
            "max_matrix_columns": max(row[4] for row in rows),
            "ideal_degree": ideal_degree,
            "log_sha256": digest(log),
            "output_sha256": digest(output),
        })
    summary = {"solver_version": fixture["msolve_version"], "results": results}
    (OUTPUT_DIR / "summary.json").write_text(json.dumps(summary, sort_keys=True) + "\n")
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    assert len(sys.argv) == 2 and sys.argv[1] in ("generate", "run")
    globals()[sys.argv[1]]()
