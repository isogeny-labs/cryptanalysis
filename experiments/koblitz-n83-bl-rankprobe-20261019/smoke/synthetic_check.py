#!/usr/bin/env python3
"""Python-only check of the schedule, the runner's bookkeeping and the verifier on synthetic rows.

No binary is built or run (the cloud-agent VM had about 2 GB of disk). This
builds synthetic receipts in a temporary folder and runs `verify_receipt.py`
on each, with `--schedule` pointing at a copy of `schedule.json` in which every
cold point is replaced by [d]G for a known d (so that the oracle replay can
pass); Q0 keeps its real point and scalar. Each scenario plants a known
effect or a known fault:

* `planted_gap_20`: BL online = cP online / 20 on every point, all gates
  true; expected reading `bl_online_faster_than_ic` with G near 20;
* `no_gap`: BL online = cP online; expected `not_separated`;
* `scalar_mismatch`: one BL row recovers another scalar; expected `no_result`
  with `one_scalar_per_point_every_arm` false;
* `blaa_steps_differ`: one BLaa row takes other steps; expected `no_result`
  with `bl_and_blaa_steps_identical` false;
* `budget_mismatch`: the BL budget differs from P_IC; expected `no_result`;
* `control_rows_differ`: the positive control's rows differ from the archived
  ones; expected `no_result`.

Writes `smoke/synthetic_check.json` (readings and checks; the synthetic times
are inputs, not measurements).
"""

import base64
import json
import random
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXP = HERE.parent
sys.path.insert(0, str(EXP))
import verify_receipt as vr  # noqa: E402

IDS = json.loads((EXP / "inputs/archived_identities.json").read_text())
CONTROL_ROWS = EXP.parent / "koblitz-n83-bl-arm-20261014/smoke/control/pc69-rT770/rows.jsonl"
TABLE_ENTRIES = 15_000_000


def synthetic_schedule(curve):
    schedule = json.loads((EXP / "schedule.json").read_text())
    scalars = {}
    for segment in schedule["segments"]:
        for run in segment["runs"]:
            if run["point_id"] == "q0":
                scalars["q0"] = int(IDS["q0_scalar"])
                continue
            d = scalars.setdefault(run["point_id"], 1000003 + 7919 * int(run["point_id"][1:]))
            x, y = curve.mul(curve.g, d)
            run["point"] = [str(x), str(y)]
    return schedule, scalars


def write_row(panel, ledger, run, arm, fields_line, raw, status="valid"):
    stem = "%05d" % run["serial"]
    raw_bytes = json.dumps(raw, sort_keys=True).encode()
    (panel / "runs" / (stem + ".stdout.txt")).write_text(
        "raw_b64=" + base64.b64encode(raw_bytes).decode() + "\n" +
        " ".join("%s=%s" % kv for kv in fields_line.items()) + "\n")
    ledger.append({"serial": run["serial"], "arm": run["arm"], "point_id": run["point_id"], "seed": run["seed"],
                   "status": status, "issues": [], "contention_flags": [], "fields": fields_line,
                   "stdout_file": "runs/" + stem + ".stdout.txt", "process_wall_ms": 1e6})


def build(folder, schedule, scalars, gap, fault=None):
    rng = random.Random(7)
    panel = folder / "panel"
    (panel / "runs").mkdir(parents=True)
    ledger = []
    p_ic = 163000.0
    ic_online = {}
    for segment in schedule["segments"]:
        for run in segment["runs"]:
            unit, arm = run["point_id"], run["arm"]
            d = scalars[unit]
            base = ic_online.setdefault(unit, round(rng.uniform(20, 900), 3))
            scalar = str(d)
            if arm in ("cP", "cPaa", "kP"):
                online = base * (1 + rng.uniform(-0.01, 0.01)) if arm == "cPaa" else base
                relation = list(IDS["q0_ic"]["relation"]) if unit == "q0" else [1, 2, 3, int(unit[1:]) + 4]
                probes = IDS["q0_ic"]["probes_folded"] if unit == "q0" else 1000 + int(unit[1:])
                f = {"online_ms": online, "setup_ms": 22000.0, "cold_ms": 22000.0 + online,
                     "recovered_scalar": d, "relation": relation, "ops": probes}
                records = []
                if arm == "kP":
                    attempts = [rng.uniform(200e6, 300e6) for _ in range(600)]
                    stage = sum(attempts) / 1e6 + 500.0
                    f.update(rank_stage_ms=stage, logs_equal_archived=True, cold_ms=stage + 22000.0 + online)
                    records = [{"kind": "compact_orbit_dlp_summary", "rank_attempt_ns": attempts,
                                "timing_ms": {"rank_stage": stage, "setup_total": 20000.0}}]
                write_row(panel, ledger, run, arm, {"online_ms": "%.6f" % online, "verified": "1"},
                          {"fields": f, "records": records, "issues": []})
            elif arm == "rT":
                steps = IDS["bl_step_identity"]["walk_steps"] if unit == "q0" else rng.randint(4_000_000, 20_000_000)
                online = steps * 1.8e-4
                f = {"online_ms": online, "setup_ms": 300.0, "ops": steps, "recovered_scalar": d}
                write_row(panel, ledger, run, arm, {"online_ms": "%.6f" % online, "verified": "1"},
                          {"fields": f, "records": [], "issues": []})
            else:
                steps = IDS["bl_step_identity"]["walk_steps"] if arm == "BLplain" else 90000 + int(
                    unit[1:] if unit != "q0" else 0)
                online = (base / gap) if arm != "BLplain" else steps * 1.8e-4
                if arm == "BLaa":
                    online *= 1 + rng.uniform(-0.01, 0.01)
                    if fault == "blaa_steps_differ" and unit == "s005":
                        steps += 1
                if fault == "scalar_mismatch" and arm == "BL" and unit == "s010":
                    scalar = str(d + 1)
                line = {"online_ms": "%.6f" % online, "verified": "1", "setup_ms": "2600.0",
                        "table_load_ms": "2500.0", "ops": str(steps), "recovered_scalar": scalar,
                        "solved_by": "precomputed_table" if arm != "BLplain" else "online_self_collision",
                        "table_entries_loaded": str(TABLE_ENTRIES if arm != "BLplain" else 0)}
                write_row(panel, ledger, run, arm, line, {"records": [], "issues": []})
    (panel / "runs.jsonl").write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in ledger))
    (folder / "control" / "pc69-rT770").mkdir(parents=True)
    rows = CONTROL_ROWS.read_bytes()
    if fault == "control_rows_differ":
        rows = rows.replace(b'"steps": 39948', b'"steps": 39949', 1)
    (folder / "control" / "pc69-rT770" / "rows.jsonl").write_bytes(rows)
    (folder / "control" / "summary.json").write_text(json.dumps(
        {"status": "PASS", "controls": [{"id": "pc69-rT770", "status": "PASS"}]}))
    (folder / "ic_budget").mkdir()
    (folder / "ic_budget" / "precompute_receipt.json").write_text(json.dumps({"status": "PASS", "P_IC_ms": p_ic}))
    (folder / "bl").mkdir()
    producer = {"precompute_ms": p_ic + 20, "table_entries": TABLE_ENTRIES, "covered_points": 9.0e8,
                "steps": 9.1e8, "rounds": 1, "duplicate_points": 0, "ns_per_step": 180.0,
                "identity": {"subgroup_order": "8569786107849059", "automorphism_size": 166}}
    (folder / "bl" / "precompute_receipt.json").write_text(json.dumps(
        {"status": "PASS", "budget_ms": p_ic + (1 if fault == "budget_mismatch" else 0), "implementation": "rT770",
         "implementation_overridden_for_smoke": False, "producer": producer}))
    (folder / "bl" / "table_checks.json").write_text(json.dumps({"status": "PASS", "checks": {}}))


def main():
    curve = vr.oracle()
    schedule, scalars = synthetic_schedule(curve)
    expected = {"planted_gap_20": (20.0, None, "bl_online_faster_than_ic"),
                "no_gap": (1.0, None, "not_separated"),
                "scalar_mismatch": (20.0, "scalar_mismatch", "no_result"),
                "blaa_steps_differ": (20.0, "blaa_steps_differ", "no_result"),
                "budget_mismatch": (20.0, "budget_mismatch", "no_result"),
                "control_rows_differ": (20.0, "control_rows_differ", "no_result")}
    results = {}
    with tempfile.TemporaryDirectory(prefix="n83-blrp-synthetic-") as tmp:
        sched_path = Path(tmp) / "schedule.json"
        sched_path.write_text(json.dumps(schedule))
        for name, (gap, fault, want) in expected.items():
            folder = Path(tmp) / name
            build(folder, schedule, scalars, gap, fault)
            subprocess.run([sys.executable, str(EXP / "verify_receipt.py"), str(folder), "--schedule",
                            str(sched_path)], check=True, capture_output=True)
            result = json.loads((folder / "result.json").read_text())
            primary = result["statistics"].get("primary_online_gap_cP_over_BL")
            results[name] = {"expected": want, "reading": result["decision"],
                             "as_expected": result["decision"] == want,
                             "primary": primary, "failed_checks": sorted(k for k, v in result["checks"].items()
                                                                         if v is not True),
                             "controls": result["controls"]}
            shutil.rmtree(folder)
    out = {"what": "synthetic receipts through verify_receipt.py (inputs, not measurements)",
           "all_as_expected": all(r["as_expected"] for r in results.values()), "scenarios": results}
    (HERE / "synthetic_check.json").write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
    print(json.dumps({k: (v["reading"], v["as_expected"], v["failed_checks"]) for k, v in results.items()},
                     sort_keys=True))
    if not out["all_as_expected"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
