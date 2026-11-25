"""Check rounding-aware phase comparisons on the archived higher-arity E1_T0 runs."""
from decimal import Decimal
import hashlib
import json
import subprocess

from replay_public_equations import panel


def main():
    data = json.loads(panel("end_to_end_solves_summary"), parse_float=Decimal)
    protocol = panel("protocol_and_targets")
    assert hashlib.sha256(protocol).hexdigest() == data["protocol_sha256"]
    primary = data["e1_m2_5target_solves"][0]
    target = json.loads(protocol)["curves"]["E1_primary_31bit"]["targets"][0]
    assert primary["target_id"] == target["id"] == "E1_T0" and primary["Q"] == target["Q"]
    theorems = ["import Std"]
    for key, arm_count, floor_percent in (("m3", 5, 757), ("m4", 4, 133)):
        arms = data["e1_m3_m4_solves_T0"][key]
        assert len(arms) == arm_count
        rho = arms["arm_A_auxiliary"]["rho"]
        assert rho["scalar"] == primary["recovered_scalar"]
        rho_ns = int(rho["online_ms"] * 10**6)
        for index, (name, row) in enumerate(arms.items()):
            assert row["scalar"] == rho["scalar"] and row["summands"] == int(key[1:])
            assert row["columns_blake3"] == primary["arms"][name]["columns_blake3"]
            total, decomposition, walk = (
                int(row[field] * 10**9)
                for field in ("ic_observed_total_s", "decomposition_s", "target_walk_s")
            )
            # Each IC timer is rounded to 50,000 ns either way; rho to 50 ns.
            residual = f"100*({total}-{decomposition}-100000) > {floor_percent}*({rho_ns}+50)"
            walk_test = (f"{walk}-50000 > {rho_ns}+50" if key == "m3"
                         else f"{walk}+50000 < {rho_ns}-50")
            theorems.append(f"theorem {key}_{index} : ({residual}) ∧ ({walk_test}) := by decide")
    subprocess.run(["lean", "--stdin"], input="\n".join(theorems), text=True, check=True)
    print("Verified nine fixed-work comparisons against the corresponding online rho clock.")


if __name__ == "__main__":
    main()
