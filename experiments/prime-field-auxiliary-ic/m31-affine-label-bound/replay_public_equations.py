"""Check public equations from retained M31 records without running a search."""
import hashlib
import json
from pathlib import Path
import subprocess

from archived_loops import HERE, observations, read

PANEL = "experiments/prime-field-auxiliary-ic/m34-and-3arm-20261119"


def panel(filename):
    return subprocess.check_output(["git", "show", f"HEAD:{PANEL}/{filename}.json"], cwd=HERE)


def point(pair):
    x, y = pair
    return f"(some ({x},{y}))"


def main():
    protocol_bytes = panel("protocol_and_targets")
    summary = json.loads(panel("end_to_end_solves_summary"))
    assert hashlib.sha256(protocol_bytes).hexdigest() == summary["protocol_sha256"]
    curves = json.loads(protocol_bytes)["curves"]
    e1, e2 = curves["E1_primary_31bit"], curves["E2_secondary_31bit"]
    lines = [(HERE / "PublicEquations.lean").read_text(), "open M31PublicEquations"]
    checks = []
    arms_verified = 0

    def public_checks(curve, target, arms):
        nonlocal arms_verified
        assert curve["p"] == 2147483647 and curve["a"] == 2
        for arm in arms.values():
            assert arm["status"] == "solved"
            k = arm["scalar"]
            checks.append(f'publicEquation {curve["b"]} {curve["n"]} {point(curve["P"])} {point(target["Q"])} {k}')
            arms_verified += 1

    for curve, records in ((e1, summary["e1_m2_5target_solves"]), (e2, [summary["e2_m2_solve_T0"]])):
        for record in records:
            target, = [t for t in curve["targets"] if t["id"] == record["target_id"]]
            assert record["Q"] == target["Q"]
            public_checks(curve, target, record["arms"])
    for arms in summary["e1_m3_m4_solves_T0"].values():
        public_checks(e1, e1["targets"][0], arms)
    assert arms_verified == 49

    manifest = json.loads(read("public", "json"))
    base = ",".join(f"({x},{y})" for x, y in manifest["factor_base"])
    lines.append(f"def base : Array (Nat × Nat) := #[{base}]")
    params = manifest["public"]
    count = 0
    for arm in ("v2_chain", "v2_batch"):
        for seed in range(3):
            _, rows = observations(arm, seed)
            for r in rows:
                checks.append(f'rowEquation {point(params["P"])} {point(params["Q"])} base '
                              f'{r["a"]} {r["b"]} {r["i"]} {r["j"]} ({r["si"]}) ({r["sj"]})')
                count += 1
    assert count == 78
    # Use separate declarations to localize a failure to its exact input.
    for i, check in enumerate(checks):
        lines.append(f"theorem receipt_{i} : {check} = true := by native_decide")
    subprocess.run(["lean", "--stdin"], input="\n".join(lines), text=True, check=True)
    print(f"Verified {arms_verified} panel scalar equations and {count} archived signed rows.")


if __name__ == "__main__":
    main()
