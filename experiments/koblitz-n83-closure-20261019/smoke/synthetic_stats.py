#!/usr/bin/env python3
"""Exercise the frozen statistics and decision rule on synthetic rows (local diagnostic).

Builds one synthetic row per scheduled run from the local smoke rows of the
same arm (`--templates`: smoke receipt panels holding every arm; cold arms
from point s000, rank arms from block K1; an A/A arm starts from its
partner's row, the same code), with
independent multiplicative timing noise per process (sd 0.3%) and per
attempt (sd 2%), and calls `verify_receipt.statistics_block` and `decide`
with every gate set to pass. Scenarios:

* `as_measured`: the local per-attempt costs of every arm (the candidate's
  rank stage as the local decisive test measured it);
* `null`: the candidate's attempts scaled so its END-TO-END cost equals the
  baseline's (the primary must not read improvement);
* `aa_broken`: cM38aa 5% slower (the A/A control must fail).

The gates are not exercised here (the smoke receipts are). Not timing
evidence.
"""

import argparse
import copy
import json
import random
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
import verify_receipt as vr  # noqa: E402


def templates(panels, protocol):
    out = {}
    schedule = json.loads((HERE / "schedule.json").read_text())
    for panel in panels:
        runs, _, _ = vr.load(panel, schedule, protocol, True)
        for r in runs:
            if r["status"] == "valid" and (r["panel"] == "C" or r["segment"] == "K1"):
                out.setdefault(r["arm"], r)
    # A/A arms run the same code: their synthetic rows start from the same template.
    for aa, arm in (("cM38aa", "cM38"), ("kM38aa", "kM38")):
        if arm in out:
            out[aa] = dict(copy.deepcopy(out[arm]), arm=aa)
    return out


def synth(protocol, tmpl, scenario, rng):
    schedule = json.loads((HERE / "schedule.json").read_text())
    runs = []
    base_e2e = None
    for segment in schedule["segments"]:
        for run in segment["runs"]:
            t = copy.deepcopy(tmpl[run["arm"]])
            t.update({"serial": run["serial"], "segment": segment["id"], "panel": segment["panel"],
                      "unit": run["point_id"], "point": run["point"]})
            g = rng.gauss(1.0, 0.003)
            if t["kind"] == "ic_rank":
                ns = [v * g * rng.gauss(1.0, 0.02) for v in t["rank_attempt_ns"]]
                rest = t["f"]["rank_stage_ms"] - sum(t["rank_attempt_ns"]) / 1e6
                t["rank_attempt_ns"] = ns
                t["f"]["rank_stage_ms"] = rest + sum(ns) / 1e6
            elif t["kind"] == "ic_cold":
                factor = 1.05 if scenario == "aa_broken" and run["arm"] == "cM38aa" else 1.0
                for key in ("cold_ms", "setup_ms", "online_ms"):
                    t["f"][key] = t["f"][key] * g * factor
            else:
                t["f"]["online_ms"] *= g
                t["f"]["rho_cold_ms"] *= g
            runs.append(t)
    if scenario == "null":
        base = statistics.mean(r["f"]["rank_stage_ms"] for r in runs if r["arm"] == "kP") + \
            statistics.mean(r["f"]["cold_ms"] for r in runs if r["arm"] == "cP" and r["panel"] == "C")
        cold = statistics.mean(r["f"]["cold_ms"] for r in runs if r["arm"] == "cM38" and r["panel"] == "C")
        stage = statistics.mean(r["f"]["rank_stage_ms"] for r in runs if r["arm"] == "kM38")
        scale = (base - cold) / stage
        for r in runs:
            if r["arm"] in ("kM38", "kM38aa", "kM38X"):
                rest = r["f"]["rank_stage_ms"] - sum(r["rank_attempt_ns"]) / 1e6
                r["rank_attempt_ns"] = [v * scale for v in r["rank_attempt_ns"]]
                r["f"]["rank_stage_ms"] = rest * scale + sum(r["rank_attempt_ns"]) / 1e6
    return runs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--templates", type=Path, nargs="+", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    protocol = json.loads((HERE / "protocol.json").read_text())
    tmpl = templates(args.templates, protocol)
    missing = sorted(set(protocol["arms"]) - set(tmpl))
    if missing:
        raise SystemExit("no template row for " + ", ".join(missing))
    out = {}
    for k, scenario in enumerate(("as_measured", "null", "aa_broken")):
        runs = synth(protocol, tmpl, scenario, random.Random(77 + k))
        stats = vr.statistics_block(runs, protocol)
        decision, controls = vr.decide({"all": True, "pre_timing_tables_and_closure_bases_verified": True}, stats)
        out[scenario] = {"decision": decision, "controls": controls,
                         "primary": stats["primary_e2e_kP_cP_over_kM38_cM38"],
                         "aa_e2e": stats["aa_e2e_kM38_cM38_over_kM38aa_cM38aa"],
                         "aa_cold": stats["aa_cold_cM38_over_cM38aa"],
                         "planted": stats["planted_rank_attempt_kM38X_over_kM38"],
                         "secondary_M10": stats["secondary_e2e_kP_cP_over_kM10_cM10"]}
        print(scenario, decision, round(out[scenario]["primary"]["estimate"], 4),
              [round(v, 4) for v in out[scenario]["primary"]["ci95"]], controls)
    args.out.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
