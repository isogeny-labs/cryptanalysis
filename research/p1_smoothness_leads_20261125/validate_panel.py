"""Validate the frozen msolve panel with separate curve group-law enumeration."""

import gzip
import hashlib
import json
import re
from itertools import product

from generate_msolve_pilot import CURVE, FIELD, HERE


ROUND = re.compile(r"^\s*(\d+)\s+(\d+)\s+(\d+)\s+(\d+) x (\d+)\s", re.M)


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def count_decompositions(roots, target_x):
    options = []
    for x_integer in roots:
        x = FIELD(x_integer)
        y = (x**3 + CURVE.a4() * x + CURVE.a6()).sqrt()
        options.append((x_integer, CURVE(x, y), CURVE(x, -y)))
    solutions = set()
    for left, middle, right in product(options, repeat=3):
        for signs in product((1, 2), repeat=3):
            p1, p2, p3 = left[signs[0]], middle[signs[1]], right[signs[2]]
            w = p1 + p2
            if w.is_zero():
                continue
            total = w + p3
            if not total.is_zero() and total[0] == FIELD(target_x):
                solutions.add((left[0], middle[0], right[0], int(w[0])))
    return len(solutions)


def main():
    fixture = json.loads((HERE / "pilot_fixture.json").read_text())
    records = json.loads((HERE / "panel" / "summary.json").read_text())
    assert len(records) == 16
    validation = []
    for record in records:
        stem = f"{record['case']}_{record['arm']}"
        folder = HERE / "panel"
        raw_log = gzip.decompress((folder / f"{stem}.log.gz").read_bytes())
        input_bytes = (folder / f"{stem}.ms").read_bytes()
        output_bytes = gzip.decompress((folder / f"{stem}.out.gz").read_bytes())
        assert sha256(raw_log) == record["log_sha256"]
        assert sha256(input_bytes) == record["input_sha256"]
        assert sha256(output_bytes) == record["output_sha256"]
        rounds = [tuple(map(int, match.groups())) for match in ROUND.finditer(raw_log.decode(errors="replace"))]
        assert len(rounds) == record["round_count"]
        assert sha256(json.dumps(rounds).encode()) == record["round_geometry_sha256"]
        relation_count = count_decompositions(
            fixture[f"{record['arm']}_roots"], record["target_xy"][0]
        )
        assert record["exit_code"] == 0
        assert record["has_solution"] == (relation_count > 0)
        if relation_count:
            assert record["ideal_degree"] == relation_count
        validation.append({
            "case": record["case"],
            "arm": record["arm"],
            "group_law_decompositions": relation_count,
            "msolve_ideal_degree": record["ideal_degree"],
            "max_step_degree": record["max_step_degree"],
        })
    print(json.dumps(validation, sort_keys=True))


if __name__ == "__main__":
    main()
