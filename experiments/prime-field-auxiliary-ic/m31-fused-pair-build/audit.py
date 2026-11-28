"""Independently replay native fused/bitmap certificates and rho answers."""
import csv
import hashlib
import json
import runpy
import subprocess
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
api = runpy.run_path(str(HERE.parent / "m31-full-rust-comparison/replay.py"))
public_bytes = subprocess.check_output([
    "git", "show", "HEAD:experiments/prime-field-auxiliary-ic/m31-integrated-local-screen/fresh-public.json"], cwd=ROOT)
assert hashlib.sha256(public_bytes).hexdigest() == "dc724fc613d9c2b824b90d59c876f1f7f84b3273d8d607c648e1ba3fbc089252"
public = json.loads(public_bytes)
curve = api["Curve"](public["p"], a4=public["a"], a6=public["b"])
g = tuple(public["G"])
n = public["n"]
rows = list(csv.DictReader((HERE / "raw.csv").open()))
seeds = json.loads((HERE / "SEEDS.json").read_text())["walk_seeds"]
assert len(rows) == 90
assert Counter((r["target"], r["seed"], r["arm"]) for r in rows) == Counter(
    (str(t), str(s), arm) for t in range(5) for s in seeds
    for arm in ("current384", "current768", "fused768", "bitmap768", "combined768", "rho"))
relation_count = 0
for row in rows:
    assert row["status"] == "solved" and row["exit_code"] == "0"
    target, seed, arm = int(row["target"]), int(row["seed"]), row["arm"]
    seed_index = seeds.index(seed)
    q = tuple(public["targets"][target]["Q"])
    raw = (HERE / f"t{target}-s{seed_index}-{arm}.stdout").read_bytes()
    assert hashlib.sha256(raw).hexdigest() == row["report_sha256"]
    if arm == "rho":
        report = json.loads((HERE / f"t{target}-s{seed_index}-rho.metrics.json").read_text())
        scalar = report["recovered"]
    else:
        report = json.loads(raw)
        assert report["Q"] == list(q) and report["G"] == list(g)
        scalar = report["scalar"]
        certificate = report["certificate"]
        assert certificate["scalar"] == scalar and certificate["summands"] == 2
        base = [tuple(p) for p in report["base_points"]]
        assert len(base) == int(arm[-3:])
        columns = [0] * len(base)
        a = b = 0
        assert len(certificate["relations"]) == len(certificate["weights"])
        for rel, weight in zip(certificate["relations"], certificate["weights"]):
            relation_count += 1
            lhs = None
            for term in rel["terms"]:
                index, sign = term["column"], term["sign"]
                p = base[index]
                lhs = curve.add(lhs, p if sign == 1 else curve.neg(p))
                columns[index] = (columns[index] + weight * sign) % n
            rhs = curve.add(curve.mul(rel["a"], g), curve.mul(rel["b"], q))
            assert lhs == rhs
            a = (a - weight * rel["a"]) % n
            b = (b - weight * rel["b"]) % n
        assert all(value == 0 for value in columns)
        assert b != 0 and (a + b * scalar) % n == 0
    assert scalar == int(row["scalar"]) and curve.mul(scalar, g) == q
print(json.dumps({"arms": len(rows), "ic_relations_replayed": relation_count,
                  "raw_csv_sha256": hashlib.sha256((HERE / "raw.csv").read_bytes()).hexdigest()}, sort_keys=True))
