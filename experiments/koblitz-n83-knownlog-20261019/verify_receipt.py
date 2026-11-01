#!/usr/bin/env python3
"""Audit a receipt of the n=83 known-log reference run and apply the frozen reading rule.

1. loads `runs.jsonl` against `schedule.json` and decodes every raw record;
2. checks the gates of `protocol.json` (per-process layout, base, index and
   log-table checks are in the two arm wrappers; here: the independent
   verification of both known-log bases and its planted cases, every
   known-log process's generated files equal to the verified ones, one
   scalar per point across every IC process and the tuned rho with an
   oracle replay, one relation and probe count per point within each base,
   Q0 against the archived and the frozen identities, the planted row
   refused, kP's factor-log tables equal to B's, and the probe counts inside
   the law band);
3. checks the controls (A/A, planted) and computes the primary and every
   secondary statistic with bootstrap intervals;
4. writes `result.json` and `result_table.md` into the receipt directory.

This is a REFERENCE measurement (owner's ruling, 2026-10-19: "Measure both,
decide later"). There is no "improvement" outcome: the primary is the gap of
the known-log arm at K_opt to the tuned rho rT770, and the reading says only
where that interval lies relative to 1. The paired ratio
E2E(kP+cP) / E2E(cL_opt) is a secondary, labelled "reference, not an IC
improvement".

`--correctness-only` (local smoke) runs steps 1-2 on whatever rows exist and
writes `correctness.json` with no timing values in it.

Built on `koblitz-n83-rankprobe-20261019`'s `verify_receipt.py` (loader,
oracle, block bootstrap).
"""

import argparse
import base64
import json
import math
import random
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SNAPSHOT = HERE.parent / "koblitz-n83-rankprobe-20261019" / "snapshots" / "r770"
DRAWS = 10000
SEED = 20261019
R = 8569786107849059


def jsonl(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def raw_record(receipt, row):
    for line in (receipt / row["stdout_file"]).read_text().splitlines():
        if line.startswith("raw_b64="):
            return json.loads(base64.b64decode(line[len("raw_b64="):]))
    return None


def oracle():
    sys.path.insert(0, str(SNAPSHOT / "research/sat_factor_base_review_20260908/autolab"))
    import single_target_panel as panel  # noqa: E402
    beats = json.loads((SNAPSHOT / "research/sat_factor_base_review_20260908/autolab/protocol.json")
                       .read_text())["beats"]
    return panel.cached_curve(dict(beats["koblitz.compact_orbit.n83_single_target"]["curve_fixture"]))


def law(k):
    return R / (166 * 83 * k * k)


def load(receipt, schedule, protocol, partial):
    rows = jsonl(receipt / "runs.jsonl")
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
        segment, run = scheduled[serial]
        if row["arm"] != run["arm"] or row["point_id"] != run["point_id"] or row["seed"] != run["seed"]:
            problems.append("row %d does not match the schedule" % serial)
        item = {"serial": serial, "segment": segment["id"], "panel": segment["panel"], "arm": run["arm"],
                "kind": protocol["arms"][run["arm"]]["kind"], "unit": run["point_id"], "point": run["point"],
                "status": row["status"], "issues": list(row.get("issues", [])),
                "contention": row.get("contention_flags", [])}
        if row["status"] != "skipped_time_guard":
            raw = raw_record(receipt, row)
            if raw is None:
                item["issues"].append("no raw producer record")
                item["status"] = "invalid"
            else:
                if raw.get("issues"):
                    item["issues"] += ["arm: " + issue for issue in raw["issues"]]
                    item["status"] = "invalid"
                item["f"] = raw.get("fields") or {}
                if item["kind"] == "rho_tuned":
                    item["f"]["rho_cold_ms"] = (item["f"].get("setup_ms") or 0.0) + (item["f"].get("online_ms") or 0.0)
                elif item["kind"] in ("ic_cold", "ic_rank"):
                    summary = next((rec for rec in raw["records"]
                                    if rec.get("kind") == "compact_orbit_dlp_summary"), {})
                    item["rank_attempt_ns"] = summary.get("rank_attempt_ns")
                    item["rank_attempt_probes"] = summary.get("rank_attempt_probes")
        runs.append(item)
    return runs, problems, missing


def by_unit(runs, kinds, panels=("C", "K", "O")):
    out = {}
    for r in runs:
        if r["status"] == "valid" and r["kind"] in kinds and r["panel"] in panels:
            out.setdefault(r["unit"], {})[r["arm"]] = r
    return out


def correctness(runs, protocol, knownlog_check):
    checks, detail = {}, {}
    executed = [r for r in runs if r["status"] != "skipped_time_guard"]
    checks["all_executed_rows_valid"] = all(r["status"] == "valid" for r in executed)
    detail["invalid_rows"] = [{"serial": r["serial"], "arm": r["arm"], "issues": r["issues"]}
                              for r in executed if r["status"] != "valid"]
    bases = protocol["knownlog"]["bases"]
    if knownlog_check is not None:
        results = {str(b["orbit_columns"]): b for b in knownlog_check.get("bases", [])}
        checks["independent_verification_of_every_base_log"] = (
            knownlog_check.get("status") == "PASS" and knownlog_check.get("every_frozen_base_checked") is True and
            all(results.get(k, {}).get("status") == "PASS" and
                results[k].get("checks", {}).get("frozen_digests") is True for k in bases))
        checks["independent_verifier_planted_cases_detected"] = (
            (knownlog_check.get("planted") or {}).get("status") == "PASS")
    curve = oracle()

    def replay(point, scalar):
        return curve.mul(curve.g, int(scalar)) == curve.decode([int(v) for v in point])

    known = [r for r in executed if r["kind"] == "ic_knownlog"]
    checks["every_knownlog_process_ran_the_verified_files"] = all(
        r["status"] == "valid" and r["f"].get("base_sha256") == bases[str(r["f"].get("orbit_columns"))]["base_sha256"]
        and r["f"].get("log_table_sha256") == bases[str(r["f"]["orbit_columns"])]["log_table_sha256"]
        for r in known) if known else None
    units = by_unit(runs, ("ic_cold", "ic_rank", "ic_knownlog", "rho_tuned"))
    scalar_ok, replay_ok, rel_ok, probe_ok = {}, {}, {}, {}
    groups = protocol["design"]["same_base_groups"]
    for unit, arms in sorted(units.items()):
        scalars = {str(r["f"].get("recovered_scalar")) for r in arms.values()}
        scalar_ok[unit] = len(scalars) == 1 and "None" not in scalars
        point = next(iter(arms.values()))["point"]
        replay_ok[unit] = scalar_ok[unit] and replay(point, next(iter(scalars)))
        rel, probe = True, True
        for group in groups:
            rows = [arms[a] for a in group if a in arms]
            rel &= len({json.dumps(r["f"].get("relation")) for r in rows}) <= 1
            probe &= len({r["f"].get("ops") for r in rows}) <= 1 and None not in {r["f"].get("ops") for r in rows}
        rel_ok[unit], probe_ok[unit] = rel, probe
    checks["one_scalar_per_point_every_ic_process_and_rho"] = all(scalar_ok.values()) if scalar_ok else None
    checks["oracle_replay"] = all(replay_ok.values()) if replay_ok else None
    checks["one_relation_per_point_within_each_base"] = all(rel_ok.values()) if rel_ok else None
    checks["one_probe_count_per_point_within_each_base"] = all(probe_ok.values()) if probe_ok else None
    q0 = units.get("q0", {})
    if q0:
        want = protocol["online"]["q0_identity"]
        ok = True
        for arm, r in q0.items():
            spec = protocol["arms"][arm]
            if spec["kind"] == "ic_knownlog":
                ident = bases[str(spec["columns"])]["q0_identity"]
                ok &= (r["f"].get("relation") == ident["relation"] and r["f"].get("ops") == ident["probes"] and
                       str(r["f"].get("recovered_scalar")) == ident["scalar"])
            else:
                ok &= (r["f"].get("relation") == want["relation"] and r["f"].get("ops") == want["probes_folded"] and
                       str(r["f"].get("recovered_scalar")) == want["scalar"])
        checks["q0_matches_archived_and_frozen_identities"] = ok
    else:
        checks["q0_matches_archived_and_frozen_identities"] = None
    planted = [r for r in executed if r["kind"] == "ic_knownlog_planted"]
    checks["planted_table_refused_by_the_producer"] = (all(r["status"] == "valid" and
                                                           r["f"].get("planted_refused") is True for r in planted)
                                                       if planted else None)
    rank_rows = [r for r in executed if r["kind"] == "ic_rank"]
    checks["rank_tables_equal_archived"] = (all(r["status"] == "valid" and r["f"].get("logs_equal_archived") is True
                                                for r in rank_rows) if rank_rows else None)
    band = protocol["design"]["probe_law_band"]
    cold = by_unit(runs, ("ic_cold", "ic_knownlog"), panels=("C",))
    law_ratio = {}
    for arm, k in protocol["design"]["probe_law_arms"].items():
        probes = [a[arm]["f"]["ops"] for a in cold.values() if arm in a and a[arm]["f"].get("ops") is not None]
        if probes:
            law_ratio[arm] = {"orbit_columns": k, "law_probes": law(k), "points": len(probes),
                              "mean_over_law": statistics.mean(probes) / law(k),
                              "max_over_law": max(probes) / law(k)}
    checks["probes_inside_the_law_band"] = (all(band["mean_low"] <= v["mean_over_law"] <= band["mean_high"] and
                                                v["max_over_law"] <= band["max_per_point"]
                                                for v in law_ratio.values()) if law_ratio else None)
    detail.update({"units_seen": len(units), "probe_law": law_ratio,
                   "scalar_failures": sorted(u for u, v in scalar_ok.items() if not v),
                   "relation_failures": sorted(u for u, v in rel_ok.items() if not v),
                   "probe_failures": sorted(u for u, v in probe_ok.items() if not v)})
    return checks, detail


def ratio_of_means(pairs):
    return sum(a for a, _ in pairs) / sum(b for _, b in pairs)


def boot(pairs, statistic, seed):
    rng = random.Random(seed)
    n = len(pairs)
    values = sorted(statistic([pairs[rng.randrange(n)] for _ in range(n)]) for _ in range(DRAWS))
    return [values[int(0.025 * DRAWS)], values[int(0.975 * DRAWS) - 1]]


def estimate(pairs, seed, statistic=ratio_of_means):
    if not pairs:
        return None
    return {"estimate": statistic(pairs), "ci95": boot(pairs, statistic, seed), "n": len(pairs)}


def cost(row):
    """End-to-end cold ms of one cold row: e2e for known-log, cold for cP, cold for rho."""
    f = row["f"]
    if row["kind"] == "ic_knownlog":
        return f["e2e_ms"]
    if row["kind"] == "rho_tuned":
        return f["rho_cold_ms"]
    return f["cold_ms"]


def rank_blocks(runs, arm):
    out = []
    for r in runs:
        if r["status"] == "valid" and r["kind"] == "ic_rank" and r["arm"] == arm:
            attempts = [v / 1e6 for v in r["rank_attempt_ns"]]
            out.append((r["f"]["rank_stage_ms"] - sum(attempts), attempts))
    return out


def baseline_over(runs, complete, rank_arm, cold_arm, other, seed):
    """E2E(rank_arm + cold_arm) / mean cost(other): blocks, attempts within blocks, and points resampled."""
    blocks = rank_blocks(runs, rank_arm)
    units = sorted(complete)
    if not blocks or not units:
        return None

    def value(block_draw, attempt_draws, point_draw):
        rank = statistics.mean(rest + (sum(att) if picks is None else sum(att[i] for i in picks))
                               for (rest, att), picks in zip(block_draw, attempt_draws))
        num = rank + statistics.mean(cost(complete[u][cold_arm]) for u in point_draw)
        return num / statistics.mean(cost(complete[u][other]) for u in point_draw)

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
            "bootstrap": "blocks resampled; attempts resampled within each drawn block; points resampled, "
                         "paired across the two cold arms; %d draws" % DRAWS}


def statistics_block(runs, protocol):
    design = protocol["design"]
    units = by_unit(runs, ("ic_cold", "ic_knownlog", "rho_tuned"), panels=("C",))
    complete = {u: a for u, a in units.items() if all(x in a for x in design["cold_arms"])}
    out = {"complete_points": len(complete)}
    opt = protocol["knownlog"]["primary_arm"]
    rho = [a["rT"]["f"] for a in complete.values()]
    if not complete:
        return out
    steps = sum(float(r["ops"]) for r in rho)
    ms_per_step = sum(r["online_ms"] for r in rho) / steps
    unit = ms_per_step * protocol["online"]["sqrt_r"]
    out.update({"rho_ms_per_step": ms_per_step, "S_unit_ms": unit,
                "rho_mean_cold_ms": statistics.mean(r["rho_cold_ms"] for r in rho),
                "rho_mean_online_ms": statistics.mean(r["online_ms"] for r in rho)})
    out["S_rho_cold"] = out["rho_mean_cold_ms"] / unit
    out["S_rho_online"] = out["rho_mean_online_ms"] / unit

    def pairs(a, b, key=None):
        return [((cost(x[a]) if key is None else x[a]["f"][key]), (cost(x[b]) if key is None else x[b]["f"][key]))
                for x in complete.values()]

    # primary: the reference measurement itself
    out["primary_gap_%s_over_rT" % opt] = estimate(pairs(opt, "rT"), SEED)
    e2e = [cost(a[opt]) for a in complete.values()]
    rng = random.Random(SEED + 1)
    means = sorted(statistics.mean(e2e[rng.randrange(len(e2e))] for _ in e2e) for _ in range(DRAWS))
    out["primary_S_e2e_cold_%s" % opt] = {"estimate": statistics.mean(e2e) / unit,
                                         "ci95": [means[int(0.025 * DRAWS)] / unit, means[int(0.975 * DRAWS) - 1] / unit],
                                         "n": len(e2e), "unit_ms": unit,
                                         "note": "rho step unit of this run held fixed; points resampled"}
    out["primary_mean_e2e_ms_%s" % opt] = statistics.mean(e2e)
    # secondary, labelled: reference, not an IC improvement
    out["secondary_reference_not_ic_improvement_e2e_kP_cP_over_%s" % opt] = baseline_over(
        runs, complete, "kP", "cP", opt, SEED + 2)
    out["secondary_reference_not_ic_improvement_e2e_kP_cP_over_cL600"] = baseline_over(
        runs, complete, "kP", "cP", "cL600", SEED + 3)
    out["e2e_cold_gap_kP_cP_over_rT"] = baseline_over(runs, complete, "kP", "cP", "rT", SEED + 4)
    out["e2e_cold_gap_cL600_over_rT"] = estimate(pairs("cL600", "rT"), SEED + 5)
    out["e2e_cL600_over_%s" % opt] = estimate(pairs("cL600", opt), SEED + 6)
    out["online_gap_%s_over_rT" % opt] = estimate(pairs(opt, "rT", "online_ms"), SEED + 7)
    out["online_gap_cL600_over_rT"] = estimate(pairs("cL600", "rT", "online_ms"), SEED + 8)
    out["online_gap_cP_over_rT"] = estimate(pairs("cP", "rT", "online_ms"), SEED + 9)
    out["cold_cP_over_cL600"] = estimate(pairs("cP", "cL600"), SEED + 10)
    # controls
    out["aa_e2e_%s_over_cLaa" % opt] = estimate(pairs(opt, "cLaa"), SEED + 11)
    # phases
    phases = {}
    for arm in ("cL600", opt, "cLaa"):
        phases[arm] = {key: statistics.mean(a[arm]["f"][key] for a in complete.values()) for key in
                       ("gen_ms", "base_load_ms", "index_ms", "scan_selftest_ms", "log_verify_ms", "setup_ms",
                        "online_ms", "cold_ms", "e2e_ms", "ops", "peak_rss_bytes")}
    phases["cP"] = {key: statistics.mean(a["cP"]["f"][key] for a in complete.values())
                    for key in ("cold_ms", "setup_ms", "online_ms", "index_ms", "ops", "peak_rss_bytes")}
    out["mean_phases"] = phases
    blocks = [r for r in runs if r["status"] == "valid" and r["kind"] == "ic_rank" and r["arm"] == "kP"]
    if blocks:
        probes = sum(v for r in blocks for v in r["rank_attempt_probes"])
        ns = sum(v for r in blocks for v in r["rank_attempt_ns"])
        out["rank_kP"] = {"rank_stage_ms": [r["f"]["rank_stage_ms"] for r in blocks],
                          "mean_rank_stage_ms": statistics.mean(r["f"]["rank_stage_ms"] for r in blocks),
                          "mean_attempt_probes": probes / sum(len(r["rank_attempt_probes"]) for r in blocks),
                          "rank_attempt_probes_over_law_K600": probes / sum(len(r["rank_attempt_probes"])
                                                                             for r in blocks) / law(600),
                          "ns_per_probe": ns / probes}
        out["e2e_ms"] = {"kP+cP": out["rank_kP"]["mean_rank_stage_ms"] + phases["cP"]["cold_ms"],
                         "cL600": phases["cL600"]["e2e_ms"], opt: phases[opt]["e2e_ms"]}
        out["S_e2e_cold"] = {k: v / unit for k, v in out["e2e_ms"].items()}
    out["S_online"] = {arm: phases[arm]["online_ms"] / unit for arm in ("cP", "cL600", opt)}
    out["ns_per_probe_online"] = {arm: phases[arm]["online_ms"] * 1e6 / phases[arm]["ops"]
                                  for arm in ("cP", "cL600", opt)}
    model = json.loads((HERE / "analysis" / "cost_model.json").read_text())
    out["cost_model_prediction_not_a_measurement"] = {
        "K_opt": model["K_opt"],
        "A_e2e_ms_K_opt": model["models"]["A"]["cost_ms_at_K_opt"],
        "B_e2e_ms_K_opt": model["models"]["B"]["cost_ms_at_K_opt"],
        "A_e2e_ms_K600": model["models"]["A"]["cost_ms_at_K600"]}
    return out


def decide(checks, stats, protocol):
    gates_ok = all(v is not False for v in checks.values())
    opt = protocol["knownlog"]["primary_arm"]
    aa = stats.get("aa_e2e_%s_over_cLaa" % opt)
    controls = {"aa_e2e_inside_0.97_1.03": aa is not None and 0.97 <= aa["estimate"] <= 1.03,
                "planted_table_refused": checks.get("planted_table_refused_by_the_producer") is True,
                "independent_verifier_planted_detected":
                    checks.get("independent_verifier_planted_cases_detected") is True}
    primary = stats.get("primary_gap_%s_over_rT" % opt)
    if not gates_ok or not all(controls.values()) or primary is None:
        return "invalid", controls
    lo, hi = primary["ci95"]
    return ("measured_above_rho" if lo > 1 else "measured_below_rho" if hi < 1 else "measured_not_separated_from_rho"), \
        controls


def fmt(e):
    if not e:
        return "n/a"
    n = e.get("n", e.get("n_points"))
    return "%.4f [%.4f, %.4f] (n=%s)" % (e["estimate"], e["ci95"][0], e["ci95"][1], n)


def table(result, protocol):
    s = result["statistics"]
    opt = protocol["knownlog"]["primary_arm"]
    lines = ["# n=83 known-log K%s reference row (seeded scalar orbits, LAnone): frozen result" %
             protocol["arms"][opt]["columns"], "",
             "REFERENCE ROW, not the IC baseline and not an IC improvement. Without relations this is generic "
             "BSGS on the Frobenius quotient, bounded by the DKM non-adaptive line: it can never beat rho.", "",
             "Reading: **%s**" % result["decision"], "", "| statistic | estimate [95%] |", "| --- | --- |"]
    for key in ("primary_gap_%s_over_rT" % opt, "primary_S_e2e_cold_%s" % opt,
                "secondary_reference_not_ic_improvement_e2e_kP_cP_over_%s" % opt,
                "secondary_reference_not_ic_improvement_e2e_kP_cP_over_cL600",
                "e2e_cold_gap_kP_cP_over_rT", "e2e_cold_gap_cL600_over_rT", "e2e_cL600_over_%s" % opt,
                "online_gap_%s_over_rT" % opt, "online_gap_cL600_over_rT", "online_gap_cP_over_rT",
                "cold_cP_over_cL600", "aa_e2e_%s_over_cLaa" % opt):
        lines.append("| %s | %s |" % (key, fmt(s.get(key))))
    lines += ["", "End-to-end means (ms): " + json.dumps(s.get("e2e_ms")),
              "", "S end-to-end cold: " + json.dumps(s.get("S_e2e_cold")),
              "", "S online: " + json.dumps(s.get("S_online")),
              "", "Mean phases: " + json.dumps(s.get("mean_phases")),
              "", "Rank stage kP: " + json.dumps({k: v for k, v in (s.get("rank_kP") or {}).items()
                                                   if k != "rank_stage_ms"}),
              "", "Probe law: " + json.dumps(result["detail"].get("probe_law")),
              "", "Checks: " + json.dumps(result["checks"]), "", "Controls: " + json.dumps(result["controls"])]
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("receipt", type=Path)
    parser.add_argument("--knownlog-check", type=Path, help="check_knownlog.py output of this job")
    parser.add_argument("--correctness-only", action="store_true")
    args = parser.parse_args()
    protocol = json.loads((HERE / "protocol.json").read_text())
    schedule = json.loads((HERE / "schedule.json").read_text())
    knownlog_check = json.loads(args.knownlog_check.read_text()) if args.knownlog_check else None
    runs, problems, missing = load(args.receipt, schedule, protocol, args.correctness_only)
    checks, detail = correctness(runs, protocol, knownlog_check)
    checks["receipt_matches_schedule"] = not problems
    if args.correctness_only:
        out = {"checks": checks, "detail": detail, "problems": problems, "rows": len(runs)}
        (args.receipt / "correctness.json").write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
        print(json.dumps(out, sort_keys=True))
        return
    if knownlog_check is None:
        checks["independent_verification_of_every_base_log"] = False
    stats = statistics_block(runs, protocol)
    checks["every_scheduled_row_present"] = not missing
    checks["all_points_complete"] = stats["complete_points"] == protocol["design"]["cold_points"]
    checks["all_rank_blocks_complete"] = len(rank_blocks(runs, "kP")) == len(protocol["design"]["rank_blocks"])
    decision, controls = decide(checks, stats, protocol)
    result = {"kind": protocol["kind"], "decision": decision, "checks": checks, "controls": controls,
              "row_label": protocol["row_label"], "detail": detail, "problems": problems,
              "skipped_time_guard": sum(1 for r in runs if r["status"] == "skipped_time_guard"),
              "contention_flags": [{"serial": r["serial"], "arm": r["arm"], "flags": r["contention"]}
                                   for r in runs if r.get("contention")],
              "statistics": stats}
    (args.receipt / "result.json").write_text(json.dumps(result, indent=1, sort_keys=True) + "\n")
    (args.receipt / "result_table.md").write_text(table(result, protocol))
    opt = protocol["knownlog"]["primary_arm"]
    print(json.dumps({"decision": decision, "primary": stats.get("primary_gap_%s_over_rT" % opt),
                      "controls": controls, "checks": checks}, sort_keys=True))


if __name__ == "__main__":
    main()
