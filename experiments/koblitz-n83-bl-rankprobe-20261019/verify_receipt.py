#!/usr/bin/env python3
"""Audit a receipt of the n=83 BL-on-rank-probe run and apply the frozen decision rule.

The receipt folder (the workflow's `$RUNNER_TEMP/n83-bl-rankprobe`) holds
`control/` (the BL positive control), `ic_budget/` (P_IC), `bl/` (the BL
precompute receipt and table checks) and `panel/` (`runs.jsonl` of both
phases and the per-serial stdout files). This script

1. loads `panel/runs.jsonl` against `schedule.json` and decodes every raw
   record (IC and rho rows carry the rank-probe wrapper's `fields`; BL rows
   carry the BL-arm wrapper's final line);
2. checks the gates and controls of `protocol.json`: one scalar per point
   across every arm with an oracle replay, one relation and one probe count
   per point across every IC process, Q0's identities, the factor-log
   tables of the kP processes, BL and BLaa step identity, the BL table's
   entry count, the budget match, the table checks, the positive control
   (status and byte identity of its rows with the archived run) and the
   step-identity control;
3. computes the primary G = mean cP online / mean BL online (bootstrap over
   points) and every secondary;
4. writes `result.json` and `result_table.md` into the receipt folder.

`--correctness-only` runs steps 1-2 on whatever rows exist (the local smoke).
`--schedule` replaces `schedule.json` for the synthetic check in `smoke/` only;
the result records that it did.
"""

import argparse
import base64
import hashlib
import json
import math
import random
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RP = HERE.parent / "koblitz-n83-rankprobe-20261019"
BL = HERE.parent / "koblitz-n83-bl-arm-20261014"
SNAPSHOT = RP / "snapshots" / "r770"
DRAWS = 10000
SEED = 2026101990
NUMERIC = ("online_ms", "setup_ms", "table_load_ms", "online_ms_at_A_boundary")


def jsonl(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def read_json(path):
    try:
        return json.loads(Path(path).read_text())
    except (OSError, ValueError):
        return None


def raw_record(panel, row):
    for line in (panel / row["stdout_file"]).read_text().splitlines():
        if line.startswith("raw_b64="):
            return json.loads(base64.b64decode(line[len("raw_b64="):]))
    return None


def oracle():
    sys.path.insert(0, str(SNAPSHOT / "research/sat_factor_base_review_20260908/autolab"))
    import single_target_panel as panel  # noqa: E402
    beats = json.loads((SNAPSHOT / "research/sat_factor_base_review_20260908/autolab/protocol.json")
                       .read_text())["beats"]
    return panel.cached_curve(dict(beats["koblitz.compact_orbit.n83_single_target"]["curve_fixture"]))


def number(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def load(receipt, schedule, protocol, partial):
    panel = receipt / "panel"
    rows = jsonl(panel / "runs.jsonl") if (panel / "runs.jsonl").exists() else []
    by_serial, problems = {}, []
    for row in rows:
        if row["serial"] in by_serial:
            problems.append("serial %d has two rows" % row["serial"])
        by_serial[row["serial"]] = row
    scheduled = {run["serial"]: (segment, run) for segment in schedule["segments"] for run in segment["runs"]}
    missing = sorted(set(scheduled) - set(by_serial))
    if missing and not partial:
        problems.append("%d scheduled runs have no row" % len(missing))
    runs = []
    for serial, row in sorted(by_serial.items()):
        if serial not in scheduled:
            problems.append("row %d is not scheduled" % serial)
            continue
        segment, run = scheduled[serial]
        if row["arm"] != run["arm"] or row["point_id"] != run["point_id"] or row["seed"] != run["seed"]:
            problems.append("row %d does not match the schedule" % serial)
        arm = protocol["arms"][run["arm"]]
        item = {"serial": serial, "segment": segment["id"], "panel": segment["panel"], "arm": run["arm"],
                "kind": arm["kind"], "runner": arm["runner"], "unit": run["point_id"], "point": run["point"],
                "seed": run["seed"], "status": row["status"], "issues": list(row.get("issues", [])),
                "contention": row.get("contention_flags", []), "wall_ms": row.get("process_wall_ms")}
        if row["status"] != "skipped_time_guard":
            raw = raw_record(panel, row)
            if raw is None:
                item["issues"].append("no raw producer record")
                item["status"] = "invalid"
            else:
                if raw.get("issues"):
                    item["issues"] += ["arm: " + issue for issue in raw["issues"]]
                    item["status"] = "invalid"
                if arm["runner"] == "rankprobe":
                    f = dict(raw.get("fields") or {})
                    if arm["kind"] == "rho_tuned":
                        f["rho_cold_ms"] = (f.get("setup_ms") or 0.0) + (f.get("online_ms") or 0.0)
                    else:
                        summary = next((rec for rec in raw["records"]
                                        if rec.get("kind") == "compact_orbit_dlp_summary"), {})
                        item["rank_attempt_ns"] = summary.get("rank_attempt_ns")
                        item["timing_ms"] = summary.get("timing_ms")
                else:
                    line = row.get("fields") or {}
                    f = {key: number(line.get(key)) for key in NUMERIC}
                    f.update(ops=int(line["ops"]) if str(line.get("ops", "")).isdigit() else None,
                             recovered_scalar=line.get("recovered_scalar"), solved_by=line.get("solved_by"),
                             table_entries_loaded=line.get("table_entries_loaded"))
                item["f"] = f
        runs.append(item)
    return runs, problems, missing


def by_unit(runs, panels=("C", "K", "O")):
    out = {}
    for r in runs:
        if r["status"] == "valid" and r["panel"] in panels:
            out.setdefault(r["unit"], {})[r["arm"]] = r
    return out


def sidecars(receipt, protocol, identities):
    """Checks of the controls and receipts outside the panel."""
    checks, detail = {}, {}
    control = read_json(receipt / "control" / "summary.json") or {}
    rows_path = receipt / "control" / identities["bl_positive_control"]["id"] / "rows.jsonl"
    rows_sha = hashlib.sha256(rows_path.read_bytes()).hexdigest() if rows_path.exists() else None
    ids = [c.get("id") for c in control.get("controls", [])]
    checks["bl_positive_control_pass"] = control.get("status") == "PASS" and \
        ids == [identities["bl_positive_control"]["id"]]
    checks["bl_positive_control_rows_equal_archived"] = rows_sha == identities["bl_positive_control"]["rows_jsonl_sha256"]
    budget = read_json(receipt / "ic_budget" / "precompute_receipt.json") or {}
    pre = read_json(receipt / "bl" / "precompute_receipt.json") or {}
    table_checks = read_json(receipt / "bl" / "table_checks.json") or {}
    checks["ic_budget_pass"] = budget.get("status") == "PASS" and budget.get("P_IC_ms") is not None
    checks["bl_precompute_pass_at_this_jobs_P_IC"] = (pre.get("status") == "PASS" and budget.get("P_IC_ms") is not None
                                                      and pre.get("budget_ms") == budget.get("P_IC_ms")
                                                      and pre.get("implementation") == "rT770"
                                                      and pre.get("implementation_overridden_for_smoke") is False)
    checks["bl_table_checks_pass"] = table_checks.get("status") == "PASS"
    detail.update(control=control, control_rows_sha256=rows_sha, budget=budget,
                  precompute={k: v for k, v in pre.items() if k not in ("command",)},
                  table_checks={k: table_checks.get(k) for k in ("checks", "status", "wall_s")})
    return checks, detail, budget, pre


def correctness(runs, protocol, identities, table_entries):
    checks, detail = {}, {}
    executed = [r for r in runs if r["status"] != "skipped_time_guard"]
    checks["all_executed_rows_valid"] = all(r["status"] == "valid" for r in executed)
    detail["invalid_rows"] = [{"serial": r["serial"], "arm": r["arm"], "issues": r["issues"]}
                              for r in executed if r["status"] != "valid"]
    curve = oracle()

    def replay(point, scalar):
        return curve.mul(curve.g, int(scalar)) == curve.decode([int(v) for v in point])

    units = by_unit(runs)
    scalar_ok, replay_ok, rel_ok, probe_ok, bl_aa_ok, bl_table_ok = {}, {}, {}, {}, {}, {}
    for unit, arms in sorted(units.items()):
        scalars = {str(r["f"].get("recovered_scalar")) for r in arms.values()}
        scalar_ok[unit] = len(scalars) == 1 and "None" not in scalars
        point = next(iter(arms.values()))["point"]
        replay_ok[unit] = scalar_ok[unit] and replay(point, next(iter(scalars)))
        ic = [r for r in arms.values() if r["kind"] in ("ic_cold", "ic_rank")]
        rel_ok[unit] = len({json.dumps(r["f"].get("relation")) for r in ic}) <= 1 and \
            all(r["f"].get("relation") for r in ic)
        probe_ok[unit] = len({r["f"].get("ops") for r in ic}) <= 1 and None not in {r["f"].get("ops") for r in ic}
        if "BL" in arms and "BLaa" in arms:
            bl_aa_ok[unit] = arms["BL"]["f"]["ops"] is not None and arms["BL"]["f"]["ops"] == arms["BLaa"]["f"]["ops"]
        for arm in ("BL", "BLaa"):
            if arm in arms:
                bl_table_ok["%s/%s" % (unit, arm)] = (
                    str(arms[arm]["f"].get("table_entries_loaded")) == str(table_entries) and
                    arms[arm]["f"].get("solved_by") in ("precomputed_table", "online_self_collision"))
    checks["one_scalar_per_point_every_arm"] = all(scalar_ok.values()) if scalar_ok else None
    checks["oracle_replay"] = all(replay_ok.values()) if replay_ok else None
    checks["one_relation_per_point_every_ic_process"] = all(rel_ok.values()) if rel_ok else None
    checks["one_probe_count_per_point_every_ic_process"] = all(probe_ok.values()) if probe_ok else None
    checks["bl_and_blaa_steps_identical"] = all(bl_aa_ok.values()) if bl_aa_ok else None
    checks["bl_rows_loaded_this_jobs_table"] = all(bl_table_ok.values()) if bl_table_ok else None
    q0 = units.get("q0", {})
    want = identities["q0_ic"]
    if q0:
        cp = q0.get("cP")
        checks["q0_ic_matches_archived_feistel_identity"] = cp is not None and (
            cp["f"].get("relation") == want["relation"] and str(cp["f"].get("recovered_scalar")) == want["scalar"]
            and cp["f"].get("ops") == want["probes_folded"])
        checks["q0_every_arm_recovers_the_sidecar_scalar"] = all(
            str(r["f"].get("recovered_scalar")) == identities["q0_scalar"] for r in q0.values())
        plain, rho = q0.get("BLplain"), q0.get("rT")
        steps = identities["bl_step_identity"]["walk_steps"]
        checks["bl_step_identity_q0_831000"] = (plain is not None and rho is not None and
                                                plain["f"].get("ops") == steps and
                                                int(rho["f"].get("ops") or -1) == steps)
    else:
        for key in ("q0_ic_matches_archived_feistel_identity", "q0_every_arm_recovers_the_sidecar_scalar",
                    "bl_step_identity_q0_831000"):
            checks[key] = None
    rank_rows = [r for r in executed if r["kind"] == "ic_rank"]
    checks["rank_tables_equal_archived"] = (all(r["status"] == "valid" and r["f"].get("logs_equal_archived") is True
                                                for r in rank_rows) if rank_rows else None)
    detail.update({"units_seen": len(units),
                   "scalar_failures": sorted(u for u, v in scalar_ok.items() if not v),
                   "relation_failures": sorted(u for u, v in rel_ok.items() if not v),
                   "probe_failures": sorted(u for u, v in probe_ok.items() if not v),
                   "bl_aa_failures": sorted(u for u, v in bl_aa_ok.items() if not v),
                   "bl_table_failures": sorted(u for u, v in bl_table_ok.items() if not v)})
    return checks, detail


def ratio_of_means(pairs):
    return sum(a for a, _ in pairs) / sum(b for _, b in pairs)


def geo_ratio(pairs):
    return math.exp(statistics.mean(math.log(a) - math.log(b) for a, b in pairs))


def boot(pairs, statistic, seed, draws=DRAWS):
    rng = random.Random(seed)
    n = len(pairs)
    values = sorted(statistic([pairs[rng.randrange(n)] for _ in range(n)]) for _ in range(draws))
    return [values[int(0.025 * draws)], values[int(0.975 * draws) - 1]]


def estimate(pairs, seed, statistic=ratio_of_means):
    if not pairs:
        return None
    return {"estimate": statistic(pairs), "ci95": boot(pairs, statistic, seed), "n": len(pairs)}


def paired(units, a, b, key):
    return [(arms[a]["f"][key], arms[b]["f"][key]) for _, arms in sorted(units.items())
            if a in arms and b in arms and arms[a]["f"].get(key) is not None and arms[b]["f"].get(key) is not None]


def rank_rows(runs):
    return [r for r in runs if r["status"] == "valid" and r["kind"] == "ic_rank"]


def e2e_draws(blocks, complete, cold_of, denominator_of, seed):
    """Point estimate and bootstrap of (mean rank stage + mean cold) / denominator; blocks, attempts, points."""
    def value(block_draw, attempt_draws, point_draw):
        rank = statistics.mean(rest + (sum(att) if picks is None else sum(att[i] for i in picks))
                               for (rest, att), picks in zip(block_draw, attempt_draws))
        num = rank + statistics.mean(cold_of(u) for u in point_draw)
        return num / denominator_of(point_draw)
    units = sorted(complete)
    point = value(blocks, [None] * len(blocks), units)
    rng = random.Random(seed)
    draws = []
    for _ in range(DRAWS):
        bd = [blocks[rng.randrange(len(blocks))] for _ in blocks]
        ad = [rng.choices(range(len(b[1])), k=len(b[1])) for b in bd]
        pd = [units[rng.randrange(len(units))] for _ in units]
        draws.append(value(bd, ad, pd))
    draws.sort()
    return {"estimate": point, "ci95": [draws[int(0.025 * DRAWS)], draws[int(0.975 * DRAWS) - 1]],
            "n_points": len(units), "rank_blocks": len(blocks),
            "bootstrap": "rank blocks resampled, attempts resampled within each drawn block, points resampled; "
                         "%d draws" % DRAWS}


def statistics_block(runs, protocol, pre):
    units = by_unit(runs, panels=("C",))
    cold_arms = protocol["design"]["cold_arms"]
    complete = {u: a for u, a in units.items() if all(x in a for x in cold_arms)}
    out = {"complete_points": len(complete)}
    out["primary_online_gap_cP_over_BL"] = estimate(paired(complete, "cP", "BL", "online_ms"), SEED)
    out["rho_online_over_BL"] = estimate(paired(complete, "rT", "BL", "online_ms"), SEED + 1)
    out["online_gap_cP_over_rT"] = estimate(paired(complete, "cP", "rT", "online_ms"), SEED + 2)
    out["online_gap_BL_over_rT"] = estimate(paired(complete, "BL", "rT", "online_ms"), SEED + 3)
    out["aa_ic_cold_cP_over_cPaa"] = estimate(paired(complete, "cP", "cPaa", "cold_ms"), SEED + 4)
    out["aa_ic_online_cP_over_cPaa"] = estimate(paired(complete, "cP", "cPaa", "online_ms"), SEED + 5)
    out["aa_bl_online_geo_BL_over_BLaa"] = estimate(paired(complete, "BL", "BLaa", "online_ms"), SEED + 6, geo_ratio)
    if complete:
        for arm in ("cP", "cPaa", "rT", "BL", "BLaa"):
            vals = [a[arm]["f"]["online_ms"] for a in complete.values()]
            out.setdefault("mean_online_ms", {})[arm] = statistics.mean(vals)
            out.setdefault("median_online_ms", {})[arm] = statistics.median(vals)
        out["rows_bl_faster_than_cP"] = sum(a["BL"]["f"]["online_ms"] < a["cP"]["f"]["online_ms"]
                                            for a in complete.values())
        out["bl_solved_by"] = {key: sum(a[arm]["f"].get("solved_by") == key for a in complete.values()
                                        for arm in ("BL", "BLaa"))
                               for key in ("precomputed_table", "online_self_collision")}
        out["mean_cold_ms_cP"] = statistics.mean(a["cP"]["f"]["cold_ms"] for a in complete.values())
        out["mean_setup_ms_cP"] = statistics.mean(a["cP"]["f"]["setup_ms"] for a in complete.values())
        out["median_bl_setup_ms"] = statistics.median(a["BL"]["f"]["setup_ms"] for a in complete.values())
        out["median_bl_table_load_ms"] = statistics.median(a["BL"]["f"]["table_load_ms"] for a in complete.values())
        out["mean_rho_cold_ms"] = statistics.mean(a["rT"]["f"]["rho_cold_ms"] for a in complete.values())
        out["bl_mean_steps"] = statistics.mean(a["BL"]["f"]["ops"] for a in complete.values())
    q0 = by_unit(runs, panels=("O",)).get("q0", {})
    out["q0_online_ms"] = {arm: r["f"].get("online_ms") for arm, r in q0.items()}
    ranks = rank_rows(runs)
    blocks = []
    for r in ranks:
        attempts = [v / 1e6 for v in (r.get("rank_attempt_ns") or [])]
        blocks.append((r["f"]["rank_stage_ms"] - sum(attempts), attempts))
    out["rank_stage_ms"] = {r["segment"]: r["f"]["rank_stage_ms"] for r in ranks}
    precompute_ms = ((pre or {}).get("producer") or {}).get("precompute_ms")
    if not (complete and blocks and precompute_ms):
        return out
    mean_rank = statistics.mean(r["f"]["rank_stage_ms"] for r in ranks)
    e2e_ic = mean_rank + out["mean_cold_ms_cP"]
    bl_fixed = precompute_ms + out["median_bl_setup_ms"]
    bl_cold = bl_fixed + out["mean_online_ms"]["BL"]
    rho = [a["rT"]["f"] for a in complete.values()]
    ms_per_step = sum(r["online_ms"] for r in rho) / sum(float(r["ops"]) for r in rho)
    unit = ms_per_step * protocol_sqrt_r()
    out["e2e_cold_ms"] = {"IC (kP+cP)": e2e_ic, "BL": bl_cold, "rT": out["mean_rho_cold_ms"],
                          "IC_rank_stage_mean": mean_rank, "BL_precompute": precompute_ms,
                          "BL_median_process_setup": out["median_bl_setup_ms"]}
    out["rho_ms_per_step"] = ms_per_step
    out["S_cold"] = {k: out["e2e_cold_ms"][k] / unit for k in ("IC (kP+cP)", "BL", "rT")}
    out["S_online"] = {arm: out["mean_online_ms"][arm] / unit for arm in ("cP", "rT", "BL")}
    p_ic = ((pre or {}).get("budget_ms"))
    out["matched_fraction_P_IC_over_e2e_minus_online"] = p_ic / (e2e_ic - out["mean_online_ms"]["cP"]) if p_ic else None
    out["cold_ic_over_bl_point"] = e2e_ic / bl_cold

    def cold_cp(u):
        return complete[u]["cP"]["f"]["cold_ms"]

    def rho_cold(draw):
        return statistics.mean(complete[u]["rT"]["f"]["rho_cold_ms"] for u in draw)

    def bl_cold_of(draw):
        return bl_fixed + statistics.mean(complete[u]["BL"]["f"]["online_ms"] for u in draw)

    out["e2e_cold_gap_IC_over_rT"] = e2e_draws(blocks, complete, cold_cp, rho_cold, SEED + 10)
    out["cold_ic_over_bl"] = e2e_draws(blocks, complete, cold_cp, bl_cold_of, SEED + 11)
    # sum(bl_fixed + online_i) / sum(rho_i) = (bl_fixed + mean online) / mean rho cold
    out["cold_gap_BL_over_rT"] = estimate([(bl_fixed + a["BL"]["f"]["online_ms"],
                                            a["rT"]["f"]["rho_cold_ms"]) for a in complete.values()], SEED + 12)
    producer = pre["producer"]
    sys.path.insert(0, str(BL))
    import bl_tools as bt  # noqa: E402  (the BL arm's frozen model)
    r, automorphisms = int(producer["identity"]["subgroup_order"]), int(producer["identity"]["automorphism_size"])
    model = bt.predict_online_steps(r, automorphisms, 64, 6, producer["covered_points"])
    ell = bt.classes(r, automorphisms)
    out["bl_model_check"] = {"mean_steps": out["bl_mean_steps"], "model_steps": model,
                             "measured_over_model": out["bl_mean_steps"] / model, "class": "model check, secondary"}
    out["bl_table"] = {"entries": producer["table_entries"], "alpha": producer["table_entries"] * 2 ** 6 / ell,
                       "covered_points": producer["covered_points"], "steps": producer["steps"],
                       "duplicate_points": producer.get("duplicate_points"), "ns_per_step": producer.get("ns_per_step"),
                       "rounds": producer["rounds"], "precompute_ms": precompute_ms, "budget_ms": pre.get("budget_ms")}
    return out


def protocol_sqrt_r():
    return json.loads((RP / "protocol.json").read_text())["online"]["sqrt_r"]


def decide(checks, stats):
    gates_ok = all(v is True for v in checks.values())
    aa_cold, aa_online = stats.get("aa_ic_cold_cP_over_cPaa"), stats.get("aa_ic_online_cP_over_cPaa")
    aa_bl, primary = stats.get("aa_bl_online_geo_BL_over_BLaa"), stats.get("primary_online_gap_cP_over_BL")
    controls = {"ic_aa_cold_inside_0.97_1.03": aa_cold is not None and 0.97 <= aa_cold["estimate"] <= 1.03,
                "ic_aa_online_inside_0.95_1.05": aa_online is not None and 0.95 <= aa_online["estimate"] <= 1.05,
                "bl_aa_interval_inside_0.9_1.1": aa_bl is not None and 0.9 <= aa_bl["ci95"][0] and
                aa_bl["ci95"][1] <= 1.1}
    if not gates_ok or not all(controls.values()) or primary is None:
        return "no_result", controls
    lo, hi = primary["ci95"]
    return ("bl_online_faster_than_ic" if lo > 1 else "ic_online_faster_than_bl" if hi < 1 else "not_separated"), controls


def fmt(e):
    if not e:
        return "n/a"
    n = e.get("n", e.get("n_points"))
    return "%.4g [%.4g, %.4g] (n=%s)" % (e["estimate"], e["ci95"][0], e["ci95"][1], n)


def table(result):
    s = result["statistics"]
    lines = ["# n=83 Bernstein-Lange gap on the rank-probe producer: frozen result (a measurement)", "",
             "Reading: **%s**" % result["decision"], "", "| statistic | estimate [95%] |", "| --- | --- |"]
    for key in ("primary_online_gap_cP_over_BL", "rho_online_over_BL", "online_gap_cP_over_rT",
                "online_gap_BL_over_rT", "e2e_cold_gap_IC_over_rT", "cold_gap_BL_over_rT", "cold_ic_over_bl",
                "aa_ic_cold_cP_over_cPaa", "aa_ic_online_cP_over_cPaa", "aa_bl_online_geo_BL_over_BLaa"):
        lines.append("| %s | %s |" % (key, fmt(s.get(key))))
    lines += ["", "End-to-end cold (ms): " + json.dumps(s.get("e2e_cold_ms")),
              "", "S cold: " + json.dumps(s.get("S_cold")), "", "S online: " + json.dumps(s.get("S_online")),
              "", "Mean online (ms): " + json.dumps(s.get("mean_online_ms")),
              "", "BL table: " + json.dumps(s.get("bl_table")), "", "BL model check: " + json.dumps(s.get("bl_model_check")),
              "", "Matched fraction: " + json.dumps(s.get("matched_fraction_P_IC_over_e2e_minus_online")),
              "", "Host class: " + json.dumps(result.get("host_class")),
              "", "Checks: " + json.dumps(result["checks"]), "", "Controls: " + json.dumps(result["controls"])]
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("receipt", type=Path)
    parser.add_argument("--correctness-only", action="store_true")
    parser.add_argument("--schedule", type=Path, help="smoke only: a synthetic schedule")
    args = parser.parse_args()
    protocol = json.loads((HERE / "protocol.json").read_text())
    identities = json.loads((HERE / "inputs" / "archived_identities.json").read_text())
    schedule = json.loads((args.schedule or HERE / "schedule.json").read_text())
    runs, problems, missing = load(args.receipt, schedule, protocol, args.correctness_only)
    side, side_detail, budget, pre = sidecars(args.receipt, protocol, identities)
    checks, detail = correctness(runs, protocol, identities, ((pre or {}).get("producer") or {}).get("table_entries"))
    checks.update(side)
    checks["receipt_matches_schedule"] = not problems
    detail["sidecars"] = side_detail
    start = read_json(args.receipt / "panel" / "runner_start_panel.json") or \
        read_json(args.receipt / "panel" / "runner_start_budget.json") or {}
    host_class = (start.get("host_cpu_record") or {}).get("host_class")
    if args.correctness_only:
        out = {"checks": checks, "detail": detail, "problems": problems, "rows": len(runs),
               "schedule_override": str(args.schedule) if args.schedule else None}
        (args.receipt / "correctness.json").write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
        print(json.dumps(out, sort_keys=True))
        return
    stats = statistics_block(runs, protocol, pre)
    checks["every_scheduled_row_present"] = not missing
    checks["all_points_complete"] = stats["complete_points"] == protocol["design"]["cold_points"]
    checks["all_rank_blocks_complete"] = len(rank_rows(runs)) == len(protocol["design"]["rank_blocks"])
    decision, controls = decide(checks, stats)
    result = {"kind": protocol["kind"], "classification": protocol["classification"], "decision": decision,
              "checks": checks, "controls": controls, "detail": detail, "problems": problems,
              "host_class": host_class, "host_cpu_record": start.get("host_cpu_record"),
              "schedule_override": str(args.schedule) if args.schedule else None,
              "skipped_time_guard": sum(1 for r in runs if r["status"] == "skipped_time_guard"),
              "contention_flags": [{"serial": r["serial"], "arm": r["arm"], "flags": r["contention"]}
                                   for r in runs if r.get("contention")],
              "statistics": stats}
    (args.receipt / "result.json").write_text(json.dumps(result, indent=1, sort_keys=True) + "\n")
    (args.receipt / "result_table.md").write_text(table(result))
    print(json.dumps({"decision": decision, "primary": stats.get("primary_online_gap_cP_over_BL"),
                      "controls": controls, "checks": checks}, sort_keys=True))


if __name__ == "__main__":
    main()
