#!/usr/bin/env python3
"""Summarize the local exactness smoke into `inputs/local_exactness.json` (correctness only, no timing).

Input: a local smoke receipt of the frozen-draft schedule (`run_schedule.py
--segments O1,P1` on the cloud-agent VM, then `verify_receipt.py
--correctness-only`), and the crate test log of the online-frame binary. It
records, per IC row, the online solve, online counters, relation (point
indices, x codes, pinned intermediates), probes, root calls, relation checks,
the recovered scalar and the layout digests, and then the identity sets per
point and base. No timing value is written: the VM is shared and its times
are not evidence.
"""

import argparse
import base64
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "inputs" / "local_exactness.json"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receipt", type=Path, required=True, help="the smoke receipt's panel directory")
    parser.add_argument("--cargo-test", type=Path, required=True, help="cargo test log of the online-frame binary")
    args = parser.parse_args()
    correctness = json.loads((args.receipt / "correctness.json").read_text())
    rows = []
    for line in (args.receipt / "runs.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row["arm"] == "rT":
            continue
        stdout = (args.receipt / row["stdout_file"]).read_text().splitlines()
        raw = json.loads(base64.b64decode(next(l[len("raw_b64="):] for l in stdout if l.startswith("raw_b64="))))
        f = raw["fields"]
        rows.append({"serial": row["serial"], "arm": row["arm"], "unit": row["point_id"], "base": f["base"],
                     "status": row["status"], "online_solve": f.get("online_solve"),
                     "online_counters": f.get("online_counters"), "relation": f.get("relation"),
                     "x_codes": f.get("x_codes"), "pinned_intermediates": f.get("pinned_intermediates"),
                     "probes": f.get("ops"), "root_calls": f.get("root_calls"),
                     "relation_checks": f.get("relation_checks"), "recovered_scalar": f.get("recovered_scalar"),
                     "layout_digest": f.get("layout_digest"), "rank_relations_blake3": f.get("rank_relations_blake3"),
                     "rank_frame": f.get("rank_frame")})
    groups = {}
    for r in rows:
        key = "%s/%s" % (r["unit"], r["base"])
        identity = json.dumps([r["relation"], r["x_codes"], r["pinned_intermediates"], r["probes"], r["root_calls"],
                               r["relation_checks"], r["recovered_scalar"]])
        groups.setdefault(key, {}).setdefault(identity, []).append(r["arm"])
    identity_sets = {k: {"distinct_identities": len(v), "arms": sorted(a for arms in v.values() for a in arms)}
                     for k, v in sorted(groups.items())}
    planted = [r["online_counters"] for r in rows if r["online_solve"] == "frame_s3plant"]
    log = args.cargo_test.read_text()
    result_line = next((l for l in log.splitlines() if l.startswith("test result:")), "")
    summary = {
        "rows": len(rows), "all_rows_valid": all(r["status"] == "valid" for r in rows),
        "one_identity_per_point_and_base": all(v["distinct_identities"] == 1 for v in identity_sets.values()),
        "planted_states_compared": sum(c["s3plant_checked_states"] for c in planted),
        "planted_candidates_compared": sum(c["s3plant_checked_candidates"] for c in planted),
        "planted_swapped_pairs": sum(c["s3plant_swapped_pairs"] for c in planted),
        "crate_tests": result_line.strip(),
        "verifier_checks": {k: v for k, v in sorted(correctness["checks"].items())},
    }
    record = {"schema": 1, "label": "LOCAL DIAGNOSTIC, cloud-agent VM, correctness only (no timing values)",
              "summary": summary, "identity_sets_per_point_and_base": identity_sets, "rows": rows}
    OUT.write_text(json.dumps(record, indent=1, sort_keys=True) + "\n")
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
