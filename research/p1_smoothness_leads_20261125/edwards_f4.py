"""Generate and run the frozen same-point Edwards/Weierstrass F4 panel.

Run `sage -python edwards_f4.py generate`, then
`sage -python edwards_f4.py run`.
"""

import gzip
import hashlib
import json
import re
import resource
import subprocess
import sys
import time
from itertools import product
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing


HERE = Path(__file__).resolve().parent
OUT = HERE / "edwards_f4"
F4_ROW = re.compile(r"^\s*(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+x\s+(\d+)\s+", re.M)
IDEAL_DEGREE = re.compile(r"degree of ideal\s+(\d+)")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def xy(point):
    return [int(value) for value in point.xy()]


def te_s3(x, y, z, a, d):
    return (
        d * x**2 * y**2 * z**2
        - d * (x**2 * y**2 + x**2 * z**2 + y**2 * z**2)
        + a * (x**2 + y**2 + z**2)
        - 2 * (a - d) * x * y * z - a
    )


def w_s3(x, y, z, a, b):
    return (
        (x - y) ** 2 * z**2
        - 2 * ((x + y) * (x * y + a) + 2 * b) * z
        + (x * y - a) ** 2
        - 4 * b * (x + y)
    )


def fixture():
    field = GF(10007)
    a, d = field(3), field(2)
    mont_a = 2 * (a + d) / (a - d)
    mont_b = 4 / (a - d)
    assert int(mont_a) == 10 and int(mont_b) == 4
    a_short = mont_b**2 * (1 - mont_a**2 / 3)
    b_short = mont_b**3 * (2 * mont_a**3 / 27 - mont_a / 3)
    assert [int(a_short), int(b_short)] == [6154, 1933]
    curve = EllipticCurve(field, [a_short, b_short])
    assert int(curve.order()) == 9920

    def map_point(x, y):
        assert x != 0 and y != 1
        u = (1 + y) / (1 - y)
        mapped = curve(mont_b * u + mont_a * mont_b / 3, mont_b**2 * u / x)
        assert a * x**2 + y**2 == 1 + d * x**2 * y**2
        return mapped

    roots_te = [4, 5, 10002, 10003]
    points = []
    for yi in roots_te:
        y = field(yi)
        x_squared = (1 - y**2) / (a - d * y**2)
        assert x_squared != 0 and x_squared.is_square()
        x = x_squared.sqrt()
        for ordinate in (x, -x):
            points.append((int(ordinate), yi, map_point(ordinate, y)))
    points.sort(key=lambda p: (p[1], p[0]))
    roots_w = sorted({int(p[2][0]) for p in points})
    assert roots_w == [3343, 5348, 6678, 6682]
    assert len(points) == 8 and len({p[2] for p in points}) == 8
    point_set = {p[2] for p in points}
    assert {-p for p in point_set} == point_set
    torsion = curve(mont_a * mont_b / 3, 0)
    assert 2 * torsion == curve(0)
    assert {p + torsion for p in point_set} == point_set

    positive = points[0][2] + points[2][2] + points[5][2]
    assert xy(positive) == [1393, 5697]
    assert positive not in point_set and -positive not in point_set
    negative = curve(field(4990), field(52))
    assert curve.gens()[0] == negative
    sumset = {
        p[2] + q[2] + r[2] for p, q, r in product(points, repeat=3)
    }
    assert positive in sumset and negative not in sumset

    ring = PolynomialRing(field, names=("u1", "u2", "u3", "u4", "z"))
    u1, u2, u3, u4, z = ring.gens()
    te_s4 = te_s3(u1, u2, z, a, d).resultant(te_s3(u3, u4, z, a, d), z)
    w_s4 = w_s3(u1, u2, z, a_short, b_short).resultant(
        w_s3(u3, u4, z, a_short, b_short), z
    )
    assert len(te_s4.monomials()) == 57 and len(w_s4.monomials()) == 439
    return field, curve, points, positive, negative, (te_s4, w_s4), ring


def build_cases():
    field, curve, points, positive, negative, s4s, ring = fixture()
    u1, u2, u3, _, _ = ring.gens()
    roots = {
        "edwards": sorted({p[1] for p in points}),
        "weierstrass": sorted({int(p[2][0]) for p in points}),
    }
    target_points = {"positive": positive, "negative": negative}
    for model, s4 in zip(("edwards", "weierstrass"), s4s):
        for control, target in target_points.items():
            if model == "edwards":
                mont_a, mont_b = field(10), field(4)
                u = (target[0] - mont_a * mont_b / 3) / mont_b
                assert u != -1 and target[1] != 0
                target_coord = (u - 1) / (u + 1)
                x_te = mont_b**2 * u / target[1]
                assert field(3) * x_te**2 + target_coord**2 == 1 + field(2) * x_te**2 * target_coord**2
                target_roots = [p[1] for p in points]
            else:
                target_coord = target[0]
                target_roots = [int(p[2][0]) for p in points]
            polynomial = s4(u1, u2, u3, target_coord, 0)
            base = [ring.prod(var - field(root) for root in roots[model]) for var in (u1, u2, u3)]
            system = [polynomial, *base]
            input_data = ("u1,u2,u3\n10007\n" + ",\n".join(str(p) for p in system) + "\n").encode()
            coordinate_solutions = {
                (x, y, z) for x, y, z in product(roots[model], repeat=3)
                if polynomial(field(x), field(y), field(z), 0, 0) == 0
            }
            group_solutions = {
                (p[1], q[1], r[1]) if model == "edwards" else
                (int(p[2][0]), int(q[2][0]), int(r[2][0]))
                for p, q, r in product(points, repeat=3)
                if p[2] + q[2] + r[2] == target
            }
            assert coordinate_solutions == group_solutions
            assert len(group_solutions) == (12 if control == "positive" else 0)
            yield {
                "name": f"{model}_{control}",
                "model": model,
                "control": control,
                "target_xy_weierstrass": xy(target),
                "target_coordinate": int(target_coord),
                "factor_base_roots": roots[model],
                "factor_base_points": len(points),
                "s4_monomials": len(s4.monomials()),
                "distinct_coordinate_solutions": len(coordinate_solutions),
                "group_law_triples_equal": True,
                "input_sha256": sha(input_data),
                "input_data": input_data,
            }


def generate():
    OUT.mkdir(exist_ok=True)
    cases = []
    for case in build_cases():
        (OUT / f"{case['name']}.ms").write_bytes(case.pop("input_data"))
        cases.append(case)
    record = {
        "field_prime": 10007,
        "curve_order": 9920,
        "edwards_a_d": [3, 2],
        "weierstrass_a_b": [6154, 1933],
        "cases": cases,
    }
    (OUT / "fixture.json").write_text(json.dumps(record, sort_keys=True) + "\n")
    print(json.dumps(record, sort_keys=True))


def run():
    fixture_data = json.loads((OUT / "fixture.json").read_text())
    results = []
    for case in fixture_data["cases"]:
        name = case["name"]
        input_path = OUT / f"{name}.ms"
        assert sha(input_path.read_bytes()) == case["input_sha256"]
        output_path = OUT / f"{name}.out"
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
        decoded = log.decode(errors="replace")
        rows = [tuple(map(int, m.groups())) for m in F4_ROW.finditer(decoded)]
        degrees = [int(s) for s in IDEAL_DEGREE.findall(decoded)]
        ideal_degree = degrees[-1] if degrees else 0
        valid_zero = bool(degrees) or ("No solution" in decoded and output.strip() == b"[-1]:")
        for suffix, data in (("log", log), ("out", output)):
            with (OUT / f"{name}.{suffix}.gz").open("wb") as raw:
                with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0, compresslevel=9) as zipped:
                    zipped.write(data)
        output_path.unlink(missing_ok=True)
        results.append({
            "name": name,
            "exit_code": proc.returncode,
            "valid_output": valid_zero,
            "wall_seconds": wall,
            "cpu_seconds": cpu,
            "f4_rounds": len(rows),
            "max_step_degree": max((row[0] for row in rows), default=None),
            "max_matrix_rows": max((row[3] for row in rows), default=None),
            "max_matrix_columns": max((row[4] for row in rows), default=None),
            "ideal_degree": ideal_degree,
            "matches_group_law": ideal_degree == case["distinct_coordinate_solutions"],
            "log_sha256": sha(log),
            "output_sha256": sha(output),
        })
    summary = {"msolve_version": "0.11.0", "results": results}
    (OUT / "summary.json").write_text(json.dumps(summary, sort_keys=True) + "\n")
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    assert len(sys.argv) == 2 and sys.argv[1] in ("generate", "run")
    globals()[sys.argv[1]]()
