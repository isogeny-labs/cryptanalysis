"""Run with lake env python3 replay.py inside a Lean/mathlib environment."""
import csv
import hashlib
import json
from decimal import Decimal
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
PANEL = "experiments/prime-field-auxiliary-ic/m34-and-3arm-20261119"


def archived(name):
    return subprocess.check_output(["git", "show", f"HEAD:{PANEL}/{name}.json"], cwd=HERE)


def ns(value, scale):
    scaled = value * scale
    if int(scaled) != scaled:
        raise ValueError("Archived time cannot be represented in integral nanoseconds")
    return int(scaled)


def main():
    protocol = archived("protocol_and_targets")
    summary = archived("end_to_end_solves_summary")
    if hashlib.sha256(summary).hexdigest() != "69a866b277b9fd480cd3347f772fdcd5d2bc98843023d75245a370dc3b57da15":
        raise ValueError("Timing record digest mismatch")
    data = json.loads(summary, parse_float=Decimal)
    if hashlib.sha256(protocol).hexdigest() != data["protocol_sha256"]:
        raise ValueError("Protocol digest mismatch")
    curve = json.loads(protocol)["curves"]["E1_primary_31bit"]
    targets = {record["id"]: record["Q"] for record in curve["targets"]}
    panels = []
    for record in data["e1_m2_5target_solves"]:
        target = record["target_id"]
        if record["Q"] != targets[target]:
            raise ValueError("Target point mismatch")
        panels.append((2, target, record["arms"]))
    for key, arms in data["e1_m3_m4_solves_T0"].items():
        panels.append((int(key[1:]), "E1_T0", arms))

    proofs = ["import Mathlib.Tactic"]
    rows = []
    for arity, target, arms in panels:
        baseline, = [arm["rho"] for arm in arms.values() if arm.get("rho")]
        rho = ns(baseline["online_ms"], 10**6)
        for name, arm in arms.items():
            if (arm["status"], arm["summands"], arm["scalar"]) != ("solved", arity, baseline["scalar"]):
                raise ValueError("Unmatched arm")
            residual = ns(arm["online_s"] - arm["decomposition_s"], 10**9)
            walk = ns(arm["target_walk_s"], 10**9)
            # Each seconds field is rounded to 0.0001 s; rho to 0.0001 ms.
            lo, hi = residual - 100_000, residual + 100_000
            wlo, whi = walk - 50_000, walk + 50_000
            rlo, rhi = rho - 50, rho + 50
            checks = [f"{lo} > {80 if arity == 2 else 1} * {rhi}"]
            if arity == 4:
                checks.append(f"{whi} < {rlo}")
            else:
                checks.append(f"{wlo} > {22 if arity == 2 else 1} * {rhi}")
            proofs.append("example : " + " ∧ ".join(checks) + " := by decide +kernel")
            rows.append((arity, target, name, lo, hi, wlo, whi, rlo, rhi))
    if [sum(row[0] == k for row in rows) for k in (2, 3, 4)] != [37, 5, 4]:
        raise ValueError("Unexpected panel sizes")
    subprocess.run(["lean", "--stdin"], input="\n".join(proofs), text=True, check=True)
    writer = csv.writer(sys.stdout)
    writer.writerow(("summands", "target", "arm", "residual_low_ns", "residual_high_ns",
                     "walk_low_ns", "walk_high_ns", "rho_low_ns", "rho_high_ns"))
    writer.writerows(rows)


if __name__ == "__main__":
    main()
