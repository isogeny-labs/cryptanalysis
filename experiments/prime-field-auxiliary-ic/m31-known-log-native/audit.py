"""Replay all public equations and the known-log pair witness from saved reports."""
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
public = json.loads(subprocess.check_output([
    "git", "show", "HEAD:experiments/prime-field-auxiliary-ic/m31-integrated-local-screen/fresh-public.json"], cwd=ROOT))
curve = api["Curve"](public["p"], a4=public["a"], a6=public["b"])
g = tuple(public["G"])
n = public["n"]
rows = list(csv.DictReader((HERE / "validation-raw.csv").open()))
assert len(rows) == 60
assert Counter((r["target"], r["seed"], r["arm"]) for r in rows) == Counter(
    (str(t), str(s), arm) for t in range(5) for s in range(3)
    for arm in ("known256", "ic384", "rho", "bsgs"))
for row in rows:
    assert row["status"] == "solved" and row["exit_code"] == "0"
    target, seed, arm = int(row["target"]), int(row["seed"]), row["arm"]
    q = tuple(public["targets"][target]["Q"])
    report_bytes = (HERE / f"val-t{target}-s{seed}-{arm}.stdout").read_bytes()
    assert hashlib.sha256(report_bytes).hexdigest() == row["report_sha256"]
    if arm == "rho":
        report = json.loads((HERE / f"val-t{target}-s{seed}-rho.metrics.json").read_text())
        k = report["recovered"]
    else:
        report = json.loads(report_bytes)
        k = report.get("scalar", report.get("result_scalar"))
    assert k == int(row["scalar"]) and curve.mul(k, g) == q
    if arm == "known256":
        points = [tuple(p) for p in report["base_points"]]
        labels = report["base_labels"]
        assert len(points) == len(labels) == 256
        assert all(curve.mul(label, g) == p for p, label in zip(points, labels))
        r = None
        coefficient = 0
        for index, negative in report["terms"]:
            point = points[index]
            r = curve.add(r, curve.neg(point) if negative else point)
            coefficient += -labels[index] if negative else labels[index]
        assert r == curve.add(q, curve.mul(report["offset"], g))
        assert (coefficient - report["offset"]) % n == k
print(json.dumps({"rows": len(rows), "public_equations": len(rows),
                  "known_log_full_witnesses": 15,
                  "validation_csv_sha256": hashlib.sha256((HERE / "validation-raw.csv").read_bytes()).hexdigest()},
                 sort_keys=True))
