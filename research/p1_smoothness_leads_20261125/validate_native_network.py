"""Validate archived native network inputs, outputs, logs, and group laws."""

import gzip
import hashlib
import json
import re
from pathlib import Path

from sage.all import EllipticCurve, GF


HERE = Path(__file__).resolve().parent / "native"
F4_ROW = re.compile(r"^\s*(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+x\s+(\d+)\s+", re.M)
IDEAL_DEGREE = re.compile(r"degree of ideal\s+(\d+)")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def semaev3(x, y, z, a, b):
    return (
        (x - y) ** 2 * z**2
        - 2 * ((x + y) * (x * y + a) + 2 * b) * z
        + (x * y - a) ** 2
        - 4 * b * (x + y)
    )


def main():
    fixture = json.loads((HERE / "fixture.json").read_text())
    summary = json.loads((HERE / "summary.json").read_text())
    assert len(fixture["cases"]) == len(summary["results"]) == 12
    field = GF(10007)
    validations = []
    geometry = {}
    for case, result in zip(fixture["cases"], summary["results"]):
        name = case["name"]
        assert name == result["name"]
        assert sha((HERE / f"{name}.ms").read_bytes()) == case["input_sha256"]
        raw_log = gzip.decompress((HERE / f"{name}.log.gz").read_bytes())
        raw_output = gzip.decompress((HERE / f"{name}.out.gz").read_bytes())
        assert sha(raw_log) == result["log_sha256"]
        assert sha(raw_output) == result["output_sha256"]
        log = raw_log.decode()
        rounds = [tuple(map(int, m.groups())) for m in F4_ROW.finditer(log)]
        degrees = [int(x) for x in IDEAL_DEGREE.findall(log)]
        ideal_degree = degrees[-1] if degrees else 0
        if not degrees:
            assert "No solution" in log and raw_output.strip() == b"[-1]:"
        assert result["exit_code"] == 0
        assert ideal_degree == result["ideal_degree"]
        assert len(rounds) == result["f4_rounds"]
        assert max(row[0] for row in rounds) == result["max_step_degree"]
        assert max(row[3] for row in rounds) == result["max_matrix_rows"]
        assert max(row[4] for row in rounds) == result["max_matrix_columns"]

        a, b = map(field, case["curve_a4_a6"])
        curve = EllipticCurve(field, [a, b])
        target = curve(*map(field, case["target_xy"]))
        roots = case["factor_base_x"]
        points = {
            point for x in roots for point in curve.lift_x(field(x), all=True)
        }
        assert len(points) == case["factor_base_points"]
        coordinate_solutions = {
            (x, y) for x in roots for y in roots
            if semaev3(field(x), field(y), target[0], a, b) == 0
        }
        group_solutions = {
            (int(p[0]), int(q[0])) for p in points for q in points
            if p + q == target
        }
        assert coordinate_solutions == group_solutions
        assert len(group_solutions) == case["distinct_x_solutions"] == ideal_degree
        arm = case["arm"]
        geometry.setdefault(arm, {})[case["case"]] = rounds
        validations.append({
            "name": name,
            "input_hash_valid": True,
            "log_hash_valid": True,
            "output_hash_valid": True,
            "group_law_x_pairs_equal": True,
            "distinct_x_solutions": len(group_solutions),
            "ideal_degree": ideal_degree,
        })

    result = {
        "cases_checked": len(validations),
        "cases": validations,
        "within_arm_positive_negative_geometry_equal": {
            arm: cases["positive"] == cases["negative"]
            for arm, cases in geometry.items()
        },
    }
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
