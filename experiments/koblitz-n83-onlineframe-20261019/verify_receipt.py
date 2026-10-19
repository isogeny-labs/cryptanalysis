#!/usr/bin/env python3
"""Audit a receipt of the n=83 online-frame run and apply the frozen decision rule.

1. loads `runs.jsonl` against `schedule.json` and decodes every raw record;
2. checks the gates of `protocol.json` (per-process layout, fold, index
   digests, online_solve and the online counters are checked by `arm.py`;
   here: one scalar per point across every IC process and the tuned rho
   with an oracle replay; one relation (point indices, x codes, pinned
   intermediates), one probe count, one root-call count and one
   relation-check count per point across every IC process; Q0 against the
   archived Feistel identity; the shared rank process's factor-log table);
3. checks the controls (A/A, planted) and computes the primary and every
   secondary statistic with bootstrap intervals;
4. writes `result.json` and `result_table.md` into the receipt directory.

Primary R_on = mean online(cS) / mean online(cF) over the points, paired
point bootstrap, 10,000 draws. End-to-end secondary R_e2e = E2E(cS) /
E2E(cF) with E2E(c) = K + mean cold(c) and the same shared rank stage K
(the one kP process) on both sides; its bootstrap resamples kP's attempts
and the points (paired).

`--correctness-only` (local smoke) runs steps 1-2 on whatever rows exist and
writes `correctness.json` with no timing values in it.

`koblitz-n83-rankprobe-20261019`'s `verify_receipt.py` restructured for an
online primary (same loading, oracle replay, gate and bootstrap helpers).
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
SNAPSHOT = HERE / "snapshots" / "r770"
IC_COLD = ("cS", "cF", "cFaa", "cFX")
DRAWS = 10000
SEED = 20261020
SEED_E2E = 20261021
IDENTITY = ("relation", "x_codes", "intermediates", "ops", "root_calls", "relation_checks")


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
                else:
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


def correctness(runs, protocol):
    checks, detail = {}, {}
    executed = [r for r in runs if r["status"] != "skipped_time_guard"]
    checks["all_executed_rows_valid"] = all(r["status"] == "valid" for r in executed)
    detail["invalid_rows"] = [{"serial": r["serial"], "arm": r["arm"], "issues": r["issues"]}
                              for r in executed if r["status"] != "valid"]
    curve = oracle()

    def replay(point, scalar):
        return curve.mul(curve.g, int(scalar)) == curve.decode([int(v) for v in point])

    units = by_unit(runs, ("ic_cold", "rho_tuned", "ic_rank"))
    scalar_ok, replay_ok, identity_ok = {}, {}, {}
    for unit, arms in sorted(units.items()):
        scalars = {str(r["f"].get("recovered_scalar")) for r in arms.values()}
        scalar_ok[unit] = len(scalars) == 1 and "None" not in scalars
        point = next(iter(arms.values()))["point"]
        replay_ok[unit] = scalar_ok[unit] and replay(point, next(iter(scalars)))
        ic = [r for r in arms.values() if r["kind"] != "rho_tuned"]
        identity_ok[unit] = all(len({json.dumps(r["f"].get(key)) for r in ic}) <= 1 and
                                all(r["f"].get(key) is not None for r in ic) for key in IDENTITY)
    checks["one_scalar_per_point_ic_and_rho"] = all(scalar_ok.values()) if scalar_ok else None
    checks["oracle_replay"] = all(replay_ok.values()) if replay_ok else None
    checks["one_relation_probe_count_root_calls_and_relation_checks_per_point_every_ic_process"] = (
        all(identity_ok.values()) if identity_ok else None)
    q0 = units.get("q0", {})
    want = protocol["online"]["q0_identity"]
    if q0:
        checks["q0_matches_archived_feistel_identity"] = all(
            r["f"].get("relation") == want["relation"] and str(r["f"].get("recovered_scalar")) == want["scalar"] and
            r["f"].get("ops") == want["probes_folded"] for r in q0.values())
    else:
        checks["q0_matches_archived_feistel_identity"] = None
    rank_rows = [r for r in executed if r["kind"] == "ic_rank"]
    checks["rank_table_equal_archived"] = (all(r["status"] == "valid" and r["f"].get("logs_equal_archived") is True
                                               for r in rank_rows) if rank_rows else None)
    detail.update({"units_seen": len(units),
                   "scalar_failures": sorted(u for u, v in scalar_ok.items() if not v),
                   "identity_failures": sorted(u for u, v in identity_ok.items() if not v),
                   "online_counters": {"%s/%s" % (r["unit"], r["arm"]): r["f"].get("online_counters")
                                       for r in executed if r.get("f") and r["kind"] != "rho_tuned"},
                   "rank_frame_counters": {r["arm"]: r["f"].get("rank_frame") for r in rank_rows if r.get("f")},
                   "rank_padd_counters": {r["arm"]: r["f"].get("rank_padd") for r in rank_rows if r.get("f")}})
    return checks, detail


def ratio_of_means(pairs):
    return sum(a for a, _ in pairs) / sum(b for _, b in pairs)


def boot(pairs, statistic, seed, draws=DRAWS):
    rng = random.Random(seed)
    n = len(pairs)
    values = sorted(statistic([pairs[rng.randrange(n)] for _ in range(n)]) for _ in range(draws))
    return [values[int(0.025 * draws)], values[int(0.975 * draws) - 1]]


def paired(units, a, b, key):
    return [(arms[a]["f"][key], arms[b]["f"][key]) for _, arms in sorted(units.items())
            if a in arms and b in arms and arms[a]["f"].get(key) is not None and arms[b]["f"].get(key) is not None]


def estimate(pairs, seed, statistic=ratio_of_means, draws=DRAWS):
    if not pairs:
        return None
    return {"estimate": statistic(pairs), "ci95": boot(pairs, statistic, seed, draws), "n": len(pairs)}


def shared_rank(runs):
    rows = [r for r in runs if r["kind"] == "ic_rank" and r["status"] == "valid"]
    if not rows:
        return None
    row = rows[0]
    attempts = [v / 1e6 for v in row["rank_attempt_ns"]]
    return {"rest_ms": row["f"]["rank_stage_ms"] - sum(attempts), "attempts_ms": attempts,
            "rank_stage_ms": row["f"]["rank_stage_ms"], "cold_ms": row["f"]["cold_ms"],
            "probes": row["rank_attempt_probes"]}


def e2e(complete, rank, a, b, seed, rho_denominator=False):
    """(K + mean cold(a)) / (K + mean cold(b)) with the shared K, or / mean rho cold."""
    if rank is None or not complete:
        return None
    units = sorted(complete)
    rest, attempts = rank["rest_ms"], rank["attempts_ms"]

    def value(picks, point_draw):
        k = rest + (sum(attempts) if picks is None else sum(attempts[i] for i in picks))
        num = k + statistics.mean(complete[u][a]["f"]["cold_ms"] for u in point_draw)
        if rho_denominator:
            return num / statistics.mean(complete[u]["rT"]["f"]["rho_cold_ms"] for u in point_draw)
        return num / (k + statistics.mean(complete[u][b]["f"]["cold_ms"] for u in point_draw))

    point = value(None, units)
    rng = random.Random(seed)
    draws = []
    for _ in range(DRAWS):
        picks = rng.choices(range(len(attempts)), k=len(attempts))
        pd = [units[rng.randrange(len(units))] for _ in units]
        draws.append(value(picks, pd))
    draws.sort()
    return {"estimate": point, "ci95": [draws[int(0.025 * DRAWS)], draws[int(0.975 * DRAWS) - 1]],
            "n_points": len(units), "rank_attempts": len(attempts),
            "bootstrap": ("the shared rank process's attempts resampled (its non-attempt time kept; the same K on "
                          "both sides); points resampled, paired; %d draws" % DRAWS)}


def tercile_pairs(complete, a, b, k):
    units = sorted(complete, key=lambda u: complete[u][a]["f"]["ops"])
    third = len(units) // 3
    chosen = units[k * third:(k + 1) * third] if k < 2 else units[2 * third:]
    return [(complete[u][a]["f"]["online_ms"], complete[u][b]["f"]["online_ms"]) for u in chosen]


def statistics_block(runs, protocol):
    units = by_unit(runs, ("ic_cold", "rho_tuned"), panels=("C",))
    complete = {u: a for u, a in units.items() if all(x in a for x in protocol["design"]["cold_arms"])}
    out = {"complete_points": len(complete)}
    out["primary_online_cS_over_cF"] = estimate(paired(complete, "cS", "cF", "online_ms"), SEED)
    out["aa_online_cF_over_cFaa"] = estimate(paired(complete, "cF", "cFaa", "online_ms"), SEED + 1)
    out["aa_cold_cF_over_cFaa"] = estimate(paired(complete, "cF", "cFaa", "cold_ms"), SEED + 2)
    out["planted_online_cFX_over_cF"] = estimate(paired(complete, "cFX", "cF", "online_ms"), SEED + 3)
    out["online_cS_over_cFaa"] = estimate(paired(complete, "cS", "cFaa", "online_ms"), SEED + 4)
    out["online_cS_over_cF_geometric"] = estimate(
        paired(complete, "cS", "cF", "online_ms"), SEED + 5,
        statistic=lambda p: math.exp(statistics.mean(math.log(x) - math.log(y) for x, y in p)))
    for k, name in enumerate(("short", "middle", "long")):
        out["online_cS_over_cF_%s_tercile" % name] = estimate(tercile_pairs(complete, "cS", "cF", k), SEED + 6 + k)
    for key, name in (("cold_ms", "cold"), ("setup_ms", "setup"), ("index_ms", "index_build"),
                      ("peak_rss_bytes", "peak_rss")):
        out[name + "_cS_over_cF"] = estimate(paired(complete, "cS", "cF", key), SEED + 20)
    for key in ("cold_ms", "setup_ms", "online_ms", "index_ms", "peak_rss_bytes"):
        out["mean_" + key] = ({arm: statistics.mean(a[arm]["f"][key] for a in complete.values()) for arm in IC_COLD}
                              if complete else {})
    if complete:
        probes = statistics.mean(a["cS"]["f"]["ops"] for a in complete.values())
        out["mean_online_probes"] = probes
        out["online_ns_per_probe"] = {arm: 1e6 * sum(a[arm]["f"]["online_ms"] for a in complete.values()) /
                                      sum(a[arm]["f"]["ops"] for a in complete.values()) for arm in IC_COLD}
    rank = shared_rank(runs)
    if rank is not None:
        probes = sum(v for v in rank["probes"] if v is not None)
        out["shared_rank_stage"] = {"rank_stage_ms": rank["rank_stage_ms"], "attempts": len(rank["attempts_ms"]),
                                    "ns_per_probe": 1e6 * sum(rank["attempts_ms"]) / probes if probes else None,
                                    "mean_attempt_probes": probes / len(rank["probes"]),
                                    "process_cold_ms": rank["cold_ms"]}
    out["secondary_e2e_cS_over_cF"] = e2e(complete, rank, "cS", "cF", SEED_E2E)
    if complete and rank is not None:
        k = rank["rank_stage_ms"]
        out["e2e_ms"] = {arm: k + out["mean_cold_ms"][arm] for arm in ("cS", "cF")}
        out["e2e_ms"]["rank_stage_K"] = k
    rho = [a["rT"]["f"] for a in complete.values()]
    if rho:
        steps = sum(float(r["ops"]) for r in rho)
        ms_per_step = sum(r["online_ms"] for r in rho) / steps
        unit = ms_per_step * protocol["online"]["sqrt_r"]
        out["rho_ms_per_step"] = ms_per_step
        out["rho_mean_online_ms"] = statistics.mean(r["online_ms"] for r in rho)
        out["rho_mean_cold_ms"] = statistics.mean(r["rho_cold_ms"] for r in rho)
        out["S_rho_cold"] = out["rho_mean_cold_ms"] / unit
        out["S_rho_online"] = out["rho_mean_online_ms"] / unit
        out["S_online"] = {arm: out["mean_online_ms"][arm] / unit for arm in IC_COLD}
        out["S_cold_without_rank"] = {arm: out["mean_cold_ms"][arm] / unit for arm in IC_COLD}
        out["delta_S_online_cS_to_cF"] = out["S_online"]["cF"] - out["S_online"]["cS"]
        for arm, seed in (("cS", 60), ("cF", 61)):
            out["online_gap_%s_over_rT" % arm] = estimate(
                [(a[arm]["f"]["online_ms"], a["rT"]["f"]["online_ms"]) for a in complete.values()], SEED + seed)
        if "e2e_ms" in out:
            out["S_e2e_cold"] = {arm: out["e2e_ms"][arm] / unit for arm in ("cS", "cF")}
            out["delta_S_e2e_cold_cS_to_cF"] = out["S_e2e_cold"]["cF"] - out["S_e2e_cold"]["cS"]
            for arm, seed in (("cS", 70), ("cF", 71)):
                out["e2e_cold_gap_%s_over_rT" % arm] = e2e(complete, rank, arm, None, SEED + seed,
                                                           rho_denominator=True)
    return out


def decide(checks, stats):
    gates_ok = all(v is not False for v in checks.values())
    aa_on, aa_cold = stats.get("aa_online_cF_over_cFaa"), stats.get("aa_cold_cF_over_cFaa")
    planted, primary = stats.get("planted_online_cFX_over_cF"), stats.get("primary_online_cS_over_cF")
    controls = {"aa_online_inside_0.97_1.03": aa_on is not None and 0.97 <= aa_on["estimate"] <= 1.03,
                "aa_cold_inside_0.97_1.03": aa_cold is not None and 0.97 <= aa_cold["estimate"] <= 1.03,
                "planted_lower_bound_above_1": planted is not None and planted["ci95"][0] > 1.0}
    if not gates_ok or not all(controls.values()) or primary is None:
        return "invalid", controls, None
    lo, hi = primary["ci95"]
    decision = "improvement" if lo > 1 else "regression" if hi < 1 else "not_separated"
    e2e = stats.get("secondary_e2e_cS_over_cF")
    classification = None
    if decision == "improvement" and e2e is not None:
        if e2e["ci95"][0] > 1:
            classification = "pipeline improvement (end-to-end lower bound above 1)"
        elif e2e["ci95"][1] < 1:
            classification = "online stage improvement with an end-to-end regression: not promoted"
        else:
            classification = ("online stage improvement, no end-to-end regression (end-to-end not separated): "
                              "a stage improvement under AGENTS.md 'Success criterion'")
    return decision, controls, classification


def fmt(e):
    if not e:
        return "n/a"
    n = e.get("n", e.get("n_points"))
    return "%.4f [%.4f, %.4f] (n=%s)" % (e["estimate"], e["ci95"][0], e["ci95"][1], n)


def table(result):
    s = result["statistics"]
    lines = ["# n=83 online frame (the rank stage's frame loop in the one-target online scan): frozen result", "",
             "Verdict: **%s**" % result["decision"], "", "Classification: %s" % result["classification"], "",
             "| statistic | estimate [95%] |", "| --- | --- |"]
    for key in ("primary_online_cS_over_cF", "aa_online_cF_over_cFaa", "aa_cold_cF_over_cFaa",
                "planted_online_cFX_over_cF", "online_cS_over_cFaa", "online_cS_over_cF_geometric",
                "online_cS_over_cF_short_tercile", "online_cS_over_cF_middle_tercile",
                "online_cS_over_cF_long_tercile", "secondary_e2e_cS_over_cF", "cold_cS_over_cF",
                "setup_cS_over_cF", "index_build_cS_over_cF", "peak_rss_cS_over_cF",
                "online_gap_cS_over_rT", "online_gap_cF_over_rT", "e2e_cold_gap_cS_over_rT",
                "e2e_cold_gap_cF_over_rT"):
        lines.append("| %s | %s |" % (key, fmt(s.get(key))))
    lines += ["", "Mean online (ms): " + json.dumps({k: round(v, 3) for k, v in s.get("mean_online_ms", {}).items()}),
              "", "Online ns per probe: " + json.dumps({k: round(v, 2) for k, v in s.get("online_ns_per_probe", {}).items()}),
              "", "Mean cold (ms): " + json.dumps({k: round(v, 1) for k, v in s.get("mean_cold_ms", {}).items()}),
              "", "End-to-end (ms): " + json.dumps(s.get("e2e_ms")),
              "", "Shared rank stage: " + json.dumps(s.get("shared_rank_stage")),
              "", "S online: " + json.dumps(s.get("S_online")),
              "", "S end-to-end cold: " + json.dumps(s.get("S_e2e_cold")),
              "", "Checks: " + json.dumps(result["checks"]), "", "Controls: " + json.dumps(result["controls"])]
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("receipt", type=Path)
    parser.add_argument("--correctness-only", action="store_true")
    args = parser.parse_args()
    protocol = json.loads((HERE / "protocol.json").read_text())
    schedule = json.loads((HERE / "schedule.json").read_text())
    runs, problems, missing = load(args.receipt, schedule, protocol, args.correctness_only)
    checks, detail = correctness(runs, protocol)
    checks["receipt_matches_schedule"] = not problems
    if args.correctness_only:
        out = {"checks": checks, "detail": detail, "problems": problems, "rows": len(runs)}
        (args.receipt / "correctness.json").write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
        print(json.dumps(out, sort_keys=True))
        return
    stats = statistics_block(runs, protocol)
    checks["every_scheduled_row_present"] = not missing
    checks["all_points_complete"] = stats["complete_points"] == protocol["design"]["cold_points"]
    checks["shared_rank_process_present"] = stats.get("shared_rank_stage") is not None
    decision, controls, classification = decide(checks, stats)
    result = {"kind": protocol["kind"], "decision": decision, "classification": classification,
              "checks": checks, "controls": controls, "detail": detail, "problems": problems,
              "skipped_time_guard": sum(1 for r in runs if r["status"] == "skipped_time_guard"),
              "contention_flags": [{"serial": r["serial"], "arm": r["arm"], "flags": r["contention"]}
                                   for r in runs if r.get("contention")],
              "statistics": stats}
    (args.receipt / "result.json").write_text(json.dumps(result, indent=1, sort_keys=True) + "\n")
    (args.receipt / "result_table.md").write_text(table(result))
    print(json.dumps({"decision": decision, "classification": classification,
                      "primary": stats.get("primary_online_cS_over_cF"), "controls": controls,
                      "checks": checks}, sort_keys=True))


if __name__ == "__main__":
    main()
