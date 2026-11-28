"""Retrospective exact rank replay with the public generator as one known column."""
import csv
import hashlib
import json
import runpy
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
INPUT = HERE.parent / "m31-known-log-native"
EXPECTED_CSV_SHA256 = "5c7028c05f308c0396c4edc93491040926011ff9c0bb0a1a41e60859baa94585"
N = 2_147_505_293


def first_recovery(rows, anchored):
    """Incremental exact elimination over F_N, returning the first useful Q row."""
    pivots = {}
    for prefix, row in enumerate(rows, 1):
        coeff = {}
        for term in row["terms"]:
            j = term["column"]
            coeff[j] = (coeff.get(j, 0) + term["sign"]) % N
        a, b = row["a"], row["b"]
        if anchored:
            a = (a - coeff.pop(0, 0)) % N  # F_0 = G, checked in main.
        coeff = {j: value for j, value in coeff.items() if value}
        while coeff:
            column = min(coeff)
            value = coeff[column]
            if column not in pivots:
                inverse = pow(value, -1, N)
                pivots[column] = (
                    {j: c * inverse % N for j, c in coeff.items()},
                    a * inverse % N, b * inverse % N)
                break
            pivot, pivot_a, pivot_b = pivots[column]
            for j, c in pivot.items():
                new = (coeff.get(j, 0) - value * c) % N
                if new:
                    coeff[j] = new
                else:
                    coeff.pop(j, None)
            a, b = (a - value * pivot_a) % N, (b - value * pivot_b) % N
        else:
            if b:
                return prefix, (-a * pow(b, -1, N)) % N
    raise AssertionError("saved stream contains no useful dependency")


def main():
    records = (INPUT / "validation-raw.csv").read_bytes()
    assert hashlib.sha256(records).hexdigest() == EXPECTED_CSV_SHA256
    rows = list(csv.DictReader(records.decode().splitlines()))
    public = json.loads(subprocess.check_output([
        "git", "show", "HEAD:experiments/prime-field-auxiliary-ic/m31-integrated-local-screen/fresh-public.json"], cwd=ROOT))
    api = runpy.run_path(str(HERE.parent / "m31-full-rust-comparison/replay.py"))
    curve = api["Curve"](public["p"], a4=public["a"], a6=public["b"])
    g = tuple(public["G"])
    assert public["n"] == N
    result = []
    for record in rows:
        if record["arm"] != "ic384":
            continue
        target, seed = int(record["target"]), int(record["seed"])
        raw = (INPUT / f"val-t{target}-s{seed}-ic384.stdout").read_bytes()
        assert hashlib.sha256(raw).hexdigest() == record["report_sha256"]
        report = json.loads(raw)
        q = tuple(public["targets"][target]["Q"])
        base = [tuple(p) for p in report["base_points"]]
        assert base[0] == g and report["Q"] == list(q)
        relations = report["certificate"]["relations"]
        for row in relations:
            lhs = None
            for term in row["terms"]:
                p = base[term["column"]]
                lhs = curve.add(lhs, p if term["sign"] == 1 else curve.neg(p))
            rhs = curve.add(curve.mul(row["a"], g), curve.mul(row["b"], q))
            assert lhs == rhs
        control_prefix, control_scalar = first_recovery(relations, False)
        anchor_prefix, anchor_scalar = first_recovery(relations, True)
        assert control_prefix == len(relations)
        assert control_scalar == anchor_scalar == report["scalar"]
        assert curve.mul(anchor_scalar, g) == q
        result.append((target, seed, len(relations), anchor_prefix,
                       len(relations) - anchor_prefix))
    assert len(result) == 15
    print("target,seed,control_rows,anchored_rows,saved_rows")
    for row in result:
        print(",".join(map(str, row)))


if __name__ == "__main__":
    main()
