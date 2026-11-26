"""Independently validate the same-point Edwards F4 archive and group laws."""

import gzip
import hashlib
import json
import re
from itertools import product
from pathlib import Path

from sage.all import EllipticCurve, GF


OUT = Path(__file__).resolve().parent / "edwards_f4"
F4_ROW = re.compile(r"^\s*(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+x\s+(\d+)\s+", re.M)
IDEAL_DEGREE = re.compile(r"degree of ideal\s+(\d+)")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    fixture = json.loads((OUT / "fixture.json").read_text())
    summary = json.loads((OUT / "summary.json").read_text())
    assert len(fixture["cases"]) == len(summary["results"]) == 4
    field = GF(10007)
    curve = EllipticCurve(field, [6154, 1933])
    assert int(curve.order()) == 9920
    A, B = field(10), field(4)
    points = []
    for yi in [4, 5, 10002, 10003]:
        y = field(yi)
        x2 = (1 - y**2) / (field(3) - field(2) * y**2)
        assert x2 != 0 and x2.is_square()
        x = x2.sqrt()
        for xx in (x, -x):
            u = (1 + y) / (1 - y)
            mapped = curve(B * u + A * B / 3, B**2 * u / xx)
            points.append((int(xx), yi, mapped))
    points.sort(key=lambda p: (p[1], p[0]))
    assert len({p[2] for p in points}) == 8
    positive = sum((points[i][2] for i in (0, 2, 5)), curve(0))
    negative = curve(field(4990), field(52))
    assert tuple(map(int, positive.xy())) == (1393, 5697)
    assert negative == curve.gens()[0]
    targets = {"positive": positive, "negative": negative}

    validated = []
    for case, result in zip(fixture["cases"], summary["results"]):
        name = case["name"]
        assert name == result["name"]
        assert sha((OUT / f"{name}.ms").read_bytes()) == case["input_sha256"]
        log = gzip.decompress((OUT / f"{name}.log.gz").read_bytes())
        output = gzip.decompress((OUT / f"{name}.out.gz").read_bytes())
        assert sha(log) == result["log_sha256"]
        assert sha(output) == result["output_sha256"]
        decoded = log.decode()
        rows = [tuple(map(int, m.groups())) for m in F4_ROW.finditer(decoded)]
        degrees = [int(value) for value in IDEAL_DEGREE.findall(decoded)]
        degree = degrees[-1] if degrees else 0
        if not degrees:
            assert "No solution" in decoded and output.strip() == b"[-1]:"
        assert result["exit_code"] == 0 and result["valid_output"]
        assert rows and len(rows) == result["f4_rounds"]
        assert max(row[0] for row in rows) == result["max_step_degree"]
        assert max(row[3] for row in rows) == result["max_matrix_rows"]
        assert max(row[4] for row in rows) == result["max_matrix_columns"]
        assert degree == result["ideal_degree"]

        target = targets[case["control"]]
        assert list(map(int, target.xy())) == case["target_xy_weierstrass"]
        triples = {
            (p[1], q[1], r[1]) if case["model"] == "edwards" else
            (int(p[2][0]), int(q[2][0]), int(r[2][0]))
            for p, q, r in product(points, repeat=3)
            if p[2] + q[2] + r[2] == target
        }
        assert len(triples) == case["distinct_coordinate_solutions"] == degree
        validated.append({
            "name": name,
            "ideal_degree": degree,
            "f4_rounds": len(rows),
            "max_step_degree": max(row[0] for row in rows),
            "sum_matrix_cells": sum(row[3] * row[4] for row in rows),
            "max_matrix_cells": max(row[3] * row[4] for row in rows),
            "group_law_solutions_equal_degree": True,
            "raw_hashes_valid": True,
        })
    print(json.dumps({"all_valid": True, "cases": validated}, sort_keys=True))


if __name__ == "__main__":
    main()
