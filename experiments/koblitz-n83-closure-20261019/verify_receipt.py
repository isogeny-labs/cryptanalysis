#!/usr/bin/env python3
"""Audit a receipt of the n=83 closure run and apply the frozen decision rule.

1. loads `runs.jsonl` against `schedule.json` and decodes every raw record;
2. checks the gates of `protocol.json` (per-process base, layout, fold, index
   digests and counters are checked by `arm.py`; here: the pre-timing
   table and closure check of the receipt, one scalar per point across every
   IC arm and the tuned rho with an oracle replay, one relation and one
   probe count per point and base, Q0 against the archived and frozen
   identities, the rank tables, per block the relation digests, per-attempt
   probes, root calls and counters of kM38, kM38aa and kM38X, and the probe
   law band of the primary kM38; the secondary kM10's band is reported);
3. checks the controls (A/A, planted) and computes the primary and every
   secondary statistic with bootstrap intervals;
4. writes `result.json` and `result_table.md` into the receipt directory.

E2E(k, c) = mean rank stage of rank arm k over its blocks + mean cold(c)
over the cold points. Primary R = E2E(kP, cP) / E2E(kM38, cM38); its
bootstrap resamples each rank arm's blocks and the attempts within each
drawn block on their own (the baseline's and the candidate's attempts are
different targets on different bases; each stage's non-attempt time is
kept), and the cold points (paired across cP and cM38), 10,000 draws. The
A/A ratio pairs kM38 with kM38aa block by block and attempt by attempt (the
gates make them the same targets with the same probes).

`--correctness-only` (local smoke) runs steps 1-2 on whatever rows exist and
writes `correctness.json` with no timing values in it.

`koblitz-n83-rankprobe-20261019`'s `verify_receipt.py` with this
experiment's bases and arms, the independent bootstrap of the primary, the
probe-law gate and the closure pre-timing check.
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
IC_COLD = ("cP", "cM38", "cM38aa", "cM10")
RANK = ("kP", "kM38", "kM38aa", "kM38X", "kM10")
SAME_TARGETS = ("kM38", "kM38aa", "kM38X")
LAW_ARMS = ("kP", "kM38", "kM10")
GATED_LAW_ARMS = ("kM38",)  # the primary; kM10's band is reported, never a gate
REPORTED_LAW_ARMS = ("kM10",)
DRAWS = 10000
SEED = 20261019


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
                item["base"] = protocol["arms"][run["arm"]].get("base")
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


def rank_blocks(runs):
    """{segment id: {rank arm: row}} over valid rank rows."""
    out = {}
    for r in runs:
        if r["status"] == "valid" and r["kind"] == "ic_rank":
            out.setdefault(r["segment"], {})[r["arm"]] = r
    return out


def law_ratio(runs, protocol, arm):
    rows = [r for r in runs if r["status"] == "valid" and r["kind"] == "ic_rank" and r["arm"] == arm]
    if not rows:
        return None
    law = protocol["online"]["bases"][protocol["arms"][arm]["base"]]
    law = int(protocol["online"]["subgroup_order"]) / (166 * law["root_table_entries"])
    blocks = [[v for v in r["rank_attempt_probes"]] for r in rows]
    flat = [v for b in blocks for v in b]
    est = statistics.mean(flat) / law
    rng = random.Random(SEED + 90 + RANK.index(arm))
    draws = []
    for _ in range(2000):
        pick = [blocks[rng.randrange(len(blocks))] for _ in blocks]
        sample = [b[rng.randrange(len(b))] for b in pick for _ in b]
        draws.append(statistics.mean(sample) / law)
    draws.sort()
    return {"estimate": est, "ci95": [draws[50], draws[1949]], "attempts": len(flat), "blocks": len(blocks),
            "law_probes_per_relation": law, "mean_probes_per_relation": statistics.mean(flat)}


def correctness(runs, protocol, receipt):
    checks, detail = {}, {}
    executed = [r for r in runs if r["status"] != "skipped_time_guard"]
    checks["all_executed_rows_valid"] = all(r["status"] == "valid" for r in executed)
    detail["invalid_rows"] = [{"serial": r["serial"], "arm": r["arm"], "issues": r["issues"]}
                              for r in executed if r["status"] != "valid"]
    pre = receipt.parent / "log-table-check.json"
    if pre.exists():
        record = json.loads(pre.read_text())
        checks["pre_timing_tables_and_closure_bases_verified"] = (
            record.get("status") == "PASS" and all(record.get(b, {}).get("status") == "PASS"
                                                   for b in ("K600", "M38", "M10")))
    else:
        checks["pre_timing_tables_and_closure_bases_verified"] = None
    curve = oracle()

    def replay(point, scalar):
        return curve.mul(curve.g, int(scalar)) == curve.decode([int(v) for v in point])

    units = by_unit(runs, ("ic_cold", "rho_tuned", "ic_rank"))
    scalar_ok, replay_ok, rel_ok, probe_ok = {}, {}, {}, {}
    for unit, arms in sorted(units.items()):
        scalars = {str(r["f"].get("recovered_scalar")) for r in arms.values()}
        scalar_ok[unit] = len(scalars) == 1 and "None" not in scalars
        point = next(iter(arms.values()))["point"]
        replay_ok[unit] = scalar_ok[unit] and replay(point, next(iter(scalars)))
        per_base = {}
        for r in arms.values():
            if r["kind"] != "rho_tuned":
                per_base.setdefault(r["base"], []).append(r)
        rel_ok[unit] = all(len({json.dumps(r["f"]["relation"]) for r in rows}) == 1 for rows in per_base.values())
        probe_ok[unit] = all(len({r["f"].get("ops") for r in rows}) == 1 and None not in {r["f"].get("ops") for r in rows}
                             for rows in per_base.values())
    checks["one_scalar_per_point_ic_and_rho"] = all(scalar_ok.values()) if scalar_ok else None
    checks["oracle_replay"] = all(replay_ok.values()) if replay_ok else None
    checks["one_relation_per_point_and_base"] = all(rel_ok.values()) if rel_ok else None
    checks["one_probe_count_per_point_and_base"] = all(probe_ok.values()) if probe_ok else None
    q0 = units.get("q0", {})
    if q0:
        ok = True
        for r in q0.values():
            want = protocol["online"]["bases"][r["base"]]["q0_identity"]
            ok &= (r["f"].get("relation") == want["relation"] and str(r["f"].get("recovered_scalar")) == want["scalar"]
                   and r["f"].get("ops") == want["probes_folded"])
        checks["q0_matches_archived_and_frozen_identities"] = ok
    else:
        checks["q0_matches_archived_and_frozen_identities"] = None
    rank_rows = [r for r in executed if r["kind"] == "ic_rank"]
    checks["rank_tables_equal_frozen_verified_tables"] = (
        all(r["status"] == "valid" and r["f"].get("logs_equal_archived") is True for r in rank_rows)
        if rank_rows else None)
    rank_ok = {}
    for block, arms in rank_blocks(runs).items():
        rows = [arms[a] for a in SAME_TARGETS if a in arms]
        if not rows:
            continue
        digests = {r["f"].get("rank_relations_blake3") for r in rows}
        probes = {json.dumps(r["rank_attempt_probes"]) for r in rows}
        calls = {r["f"].get("rank_root_calls_total") for r in rows}
        counters = {json.dumps([(r["f"].get("rank_padd") or {}).get(key) for key in
                                ("fallback_states", "irregular_inputs", "resolved_hits", "swapped_pairs")])
                    for r in rows}
        rank_ok[block] = (len(digests) == 1 and None not in digests and len(probes) == 1 and
                          len(calls) == 1 and None not in calls and len(counters) == 1 and
                          "null" not in next(iter(counters)) and
                          all(len(r["rank_attempt_probes"] or []) == len(r["rank_attempt_ns"] or []) for r in rows))
    checks["rank_relations_probes_root_calls_and_counters_identical_per_block"] = (
        all(rank_ok.values()) if rank_ok else None)
    law = {}
    for arm in GATED_LAW_ARMS + REPORTED_LAW_ARMS:
        ratio = law_ratio(runs, protocol, arm)
        band = protocol["online"]["bases"][protocol["arms"][arm]["base"]]["law_band"]
        law[arm] = None if ratio is None else band[0] <= ratio["estimate"] <= band[1]
    gated = [law[arm] for arm in GATED_LAW_ARMS if law[arm] is not None]
    checks["primary_probe_law_inside_frozen_band"] = all(gated) if gated else None
    detail.update({"units_seen": len(units),
                   "scalar_failures": sorted(u for u, v in scalar_ok.items() if not v),
                   "relation_failures": sorted(u for u, v in rel_ok.items() if not v),
                   "probe_failures": sorted(u for u, v in probe_ok.items() if not v),
                   "rank_failures": sorted(u for u, v in rank_ok.items() if not v),
                   "probe_law_gate": law,
                   "rows_without_gain": {"%s/%s" % (b, a): r["f"].get("rank_rows_without_gain")
                                         for b, arms in sorted(rank_blocks(runs).items())
                                         for a, r in sorted(arms.items())},
                   "rank_padd_counters": {"%s/%s" % (b, a): r["f"].get("rank_padd")
                                          for b, arms in sorted(rank_blocks(runs).items())
                                          for a, r in sorted(arms.items())},
                   "rank_frame_counters": {"%s/%s" % (b, a): r["f"].get("rank_frame")
                                           for b, arms in sorted(rank_blocks(runs).items())
                                           for a, r in sorted(arms.items())}})
    return checks, detail


def ratio_of_means(pairs):
    return sum(a for a, _ in pairs) / sum(b for _, b in pairs)


def boot(pairs, statistic, seed):
    rng = random.Random(seed)
    n = len(pairs)
    values = sorted(statistic([pairs[rng.randrange(n)] for _ in range(n)]) for _ in range(DRAWS))
    return [values[int(0.025 * DRAWS)], values[int(0.975 * DRAWS) - 1]]


def paired(units, a, b, key):
    return [(arms[a]["f"][key], arms[b]["f"][key]) for _, arms in sorted(units.items())
            if a in arms and b in arms and arms[a]["f"].get(key) is not None and arms[b]["f"].get(key) is not None]


def estimate(pairs, seed, statistic=ratio_of_means):
    if not pairs:
        return None
    return {"estimate": statistic(pairs), "ci95": boot(pairs, statistic, seed), "n": len(pairs)}


def process(row):
    attempts = [v / 1e6 for v in row["rank_attempt_ns"]]
    return row["f"]["rank_stage_ms"] - sum(attempts), attempts


def arm_blocks(runs, arm):
    return [process(arms[arm]) for _, arms in sorted(rank_blocks(runs).items()) if arm in arms]


def stage_value(blocks, rng):
    """Mean rank stage over the blocks; resampled when rng is given."""
    if rng is None:
        return statistics.mean(rest + sum(att) for rest, att in blocks)
    draw = [blocks[rng.randrange(len(blocks))] for _ in blocks]
    return statistics.mean(rest + sum(rng.choices(att, k=len(att))) for rest, att in draw)


def e2e_independent(runs, complete, rank_a, cold_a, rank_b, cold_b, seed, draws=DRAWS):
    """E2E(rank_a, cold_a) / E2E(rank_b, cold_b) (rank_b None: over mean rho cold); each rank arm resampled on its own."""
    blocks_a = arm_blocks(runs, rank_a)
    blocks_b = arm_blocks(runs, rank_b) if rank_b else None
    units = sorted(complete)
    if not blocks_a or (rank_b and not blocks_b) or not units:
        return None

    def value(rng):
        pts = units if rng is None else [units[rng.randrange(len(units))] for _ in units]
        num = stage_value(blocks_a, rng) + statistics.mean(complete[u][cold_a]["f"]["cold_ms"] for u in pts)
        if rank_b is None:
            return num / statistics.mean(complete[u]["rT"]["f"]["rho_cold_ms"] for u in pts)
        return num / (stage_value(blocks_b, rng) + statistics.mean(complete[u][cold_b]["f"]["cold_ms"] for u in pts))

    rng = random.Random(seed)
    values = sorted(value(rng) for _ in range(draws))
    return {"estimate": value(None), "ci95": [values[int(0.025 * draws)], values[int(0.975 * draws) - 1]],
            "n_points": len(units), "rank_blocks": [len(blocks_a), len(blocks_b) if blocks_b else 0],
            "bootstrap": ("each rank arm's blocks resampled, then its attempts within each drawn block, on its own; "
                          "points resampled, paired; %d draws" % draws)}


def paired_blocks(runs, a, b):
    out = []
    for _, arms in sorted(rank_blocks(runs).items()):
        if a in arms and b in arms:
            ra, xa = process(arms[a])
            rb, xb = process(arms[b])
            if len(xa) == len(xb):
                out.append((ra, xa, rb, xb))
    return out


def e2e_paired(runs, complete, rank_a, cold_a, rank_b, cold_b, seed):
    """E2E ratio of two rank arms with the same targets: blocks and attempts paired."""
    blocks = paired_blocks(runs, rank_a, rank_b)
    units = sorted(complete)
    if not blocks or not units:
        return None

    def value(block_draw, attempt_draws, point_draw):
        num = den = 0.0
        for (ra, xa, rb, xb), picks in zip(block_draw, attempt_draws):
            num += ra + (sum(xa) if picks is None else sum(xa[i] for i in picks))
            den += rb + (sum(xb) if picks is None else sum(xb[i] for i in picks))
        k = len(block_draw)
        return ((num / k + statistics.mean(complete[u][cold_a]["f"]["cold_ms"] for u in point_draw)) /
                (den / k + statistics.mean(complete[u][cold_b]["f"]["cold_ms"] for u in point_draw)))

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
            "bootstrap": ("blocks resampled; attempts resampled within each drawn block, paired across the two "
                          "rank arms; points resampled, paired; %d draws" % DRAWS)}


def attempt_ratio(runs, a, b, seed):
    """Per-attempt cost a / b, attempts paired within blocks."""
    blocks = paired_blocks(runs, a, b)
    if not blocks:
        return None
    pairs = [list(zip(xa, xb)) for _, xa, _, xb in blocks]
    rng = random.Random(seed)

    def value(sample):
        return sum(x for blk in sample for x, _ in blk) / sum(y for blk in sample for _, y in blk)

    est = value(pairs)
    draws = []
    for _ in range(2000):
        bd = [pairs[rng.randrange(len(pairs))] for _ in pairs]
        draws.append(value([[blk[rng.randrange(len(blk))] for _ in blk] for blk in bd]))
    draws.sort()
    return {"estimate": est, "ci95": [draws[50], draws[1949]], "attempts": sum(len(b) for b in pairs),
            "bootstrap": "blocks then attempts resampled, paired across arms, 2,000 draws"}


def statistics_block(runs, protocol):
    units = by_unit(runs, ("ic_cold", "rho_tuned"), panels=("C",))
    complete = {u: a for u, a in units.items() if all(x in a for x in protocol["design"]["cold_arms"])}
    out = {"complete_points": len(complete)}
    out["primary_e2e_kP_cP_over_kM38_cM38"] = e2e_independent(runs, complete, "kP", "cP", "kM38", "cM38", SEED)
    out["aa_e2e_kM38_cM38_over_kM38aa_cM38aa"] = e2e_paired(runs, complete, "kM38", "cM38", "kM38aa", "cM38aa",
                                                            SEED + 1)
    out["aa_cold_cM38_over_cM38aa"] = estimate(paired(complete, "cM38", "cM38aa", "cold_ms"), SEED + 2)
    out["planted_rank_attempt_kM38X_over_kM38"] = attempt_ratio(runs, "kM38X", "kM38", SEED + 3)
    out["rank_attempt_kM38_over_kM38aa"] = attempt_ratio(runs, "kM38", "kM38aa", SEED + 4)
    out["secondary_e2e_kP_cP_over_kM10_cM10"] = e2e_independent(runs, complete, "kP", "cP", "kM10", "cM10", SEED + 10)
    out["secondary_e2e_kM10_cM10_over_kM38_cM38"] = e2e_independent(runs, complete, "kM10", "cM10", "kM38", "cM38",
                                                                    SEED + 11)
    out["probe_law"] = {arm: law_ratio(runs, protocol, arm) for arm in LAW_ARMS}
    for other, seed in (("cM38", 20), ("cM10", 30)):
        for key, name in (("cold_ms", "cold_without_rank"), ("setup_ms", "setup"), ("online_ms", "online"),
                          ("index_ms", "index_build"), ("peak_rss_bytes", "peak_rss")):
            out["%s_cP_over_%s" % (name, other)] = estimate(paired(complete, "cP", other, key), SEED + seed)
            seed += 1
    for key in ("cold_ms", "setup_ms", "online_ms", "index_ms", "peak_rss_bytes", "ops"):
        out["mean_" + key] = ({arm: statistics.mean(float(a[arm]["f"][key]) for a in complete.values())
                               for arm in IC_COLD} if complete else {})
    rank_out = {}
    for arm in RANK:
        rows = [r for r in runs if r["kind"] == "ic_rank" and r["arm"] == arm and r["status"] == "valid"]
        if rows:
            probes = sum(v for r in rows for v in r["rank_attempt_probes"] if v is not None)
            ns = sum(v for r in rows for v in r["rank_attempt_ns"])
            rank_out[arm] = {"rank_stage_ms": [r["f"]["rank_stage_ms"] for r in rows],
                             "mean_rank_stage_ms": statistics.mean(r["f"]["rank_stage_ms"] for r in rows),
                             "attempts": [len(r["rank_attempt_ns"] or []) for r in rows],
                             "mean_attempt_ms": ns / 1e6 / sum(len(r["rank_attempt_ns"]) for r in rows),
                             "ns_per_probe": ns / probes if probes else None,
                             "mean_attempt_probes": probes / sum(len(r["rank_attempt_probes"]) for r in rows)}
    for a, b in (("kP", "kM38"), ("kP", "kM10"), ("kM10", "kM38"), ("kM38X", "kM38"), ("kM38", "kM38aa")):
        if a in rank_out and b in rank_out:
            rank_out["rank_stage_%s_over_%s" % (a, b)] = (rank_out[a]["mean_rank_stage_ms"] /
                                                          rank_out[b]["mean_rank_stage_ms"])
    out["rank_stage"] = rank_out
    if complete and all(k in rank_out for k in ("kP", "kM38", "kM10")):
        cold = out["mean_cold_ms"]
        e2e = {"kP+cP": rank_out["kP"]["mean_rank_stage_ms"] + cold["cP"],
               "kM38+cM38": rank_out["kM38"]["mean_rank_stage_ms"] + cold["cM38"],
               "kM10+cM10": rank_out["kM10"]["mean_rank_stage_ms"] + cold["cM10"]}
        e2e["rank_share"] = {"kP": rank_out["kP"]["mean_rank_stage_ms"] / e2e["kP+cP"],
                             "kM38": rank_out["kM38"]["mean_rank_stage_ms"] / e2e["kM38+cM38"],
                             "kM10": rank_out["kM10"]["mean_rank_stage_ms"] / e2e["kM10+cM10"]}
        out["e2e_ms"] = e2e
    rho = [a["rT"]["f"] for a in complete.values()]
    if rho and "e2e_ms" in out:
        steps = sum(float(r["ops"]) for r in rho)
        ms_per_step = sum(r["online_ms"] for r in rho) / steps
        unit = ms_per_step * protocol["online"]["sqrt_r"]
        out["rho_ms_per_step"] = ms_per_step
        out["rho_mean_online_ms"] = statistics.mean(r["online_ms"] for r in rho)
        out["rho_mean_cold_ms"] = statistics.mean(r["rho_cold_ms"] for r in rho)
        out["S_rho_cold"] = out["rho_mean_cold_ms"] / unit
        out["S_rho_online"] = out["rho_mean_online_ms"] / unit
        out["S_e2e_cold"] = {k: out["e2e_ms"][k] / unit for k in ("kP+cP", "kM38+cM38", "kM10+cM10")}
        out["S_cold_without_rank"] = {arm: out["mean_cold_ms"][arm] / unit for arm in IC_COLD}
        out["S_online"] = {arm: out["mean_online_ms"][arm] / unit for arm in IC_COLD}
        out["delta_S_e2e_cold_cP_to_cM38"] = out["S_e2e_cold"]["kM38+cM38"] - out["S_e2e_cold"]["kP+cP"]
        for rank_arm, cold_arm, seed in (("kP", "cP", 50), ("kM38", "cM38", 51), ("kM10", "cM10", 52)):
            out["e2e_cold_gap_%s_%s_over_rT" % (rank_arm, cold_arm)] = e2e_independent(
                runs, complete, rank_arm, cold_arm, None, None, SEED + seed, draws=2000)
        for arm, seed in (("cP", 60), ("cM38", 61), ("cM10", 62)):
            out["online_gap_%s_over_rT" % arm] = estimate(
                [(a[arm]["f"]["online_ms"], a["rT"]["f"]["online_ms"]) for a in complete.values()], SEED + seed)
    return out


def decide(checks, stats):
    gates_ok = all(v is not False for v in checks.values())
    aa_e2e, aa_cold = stats.get("aa_e2e_kM38_cM38_over_kM38aa_cM38aa"), stats.get("aa_cold_cM38_over_cM38aa")
    planted = stats.get("planted_rank_attempt_kM38X_over_kM38")
    primary = stats.get("primary_e2e_kP_cP_over_kM38_cM38")
    controls = {"aa_e2e_inside_0.97_1.03": aa_e2e is not None and 0.97 <= aa_e2e["estimate"] <= 1.03,
                "aa_cold_inside_0.97_1.03": aa_cold is not None and 0.97 <= aa_cold["estimate"] <= 1.03,
                "planted_lower_bound_above_1": planted is not None and planted["ci95"][0] > 1.0,
                "planted_exactness_corruptions_rejected": checks.get(
                    "pre_timing_tables_and_closure_bases_verified") is True}
    if not gates_ok or not all(controls.values()) or primary is None:
        return "invalid", controls
    lo, hi = primary["ci95"]
    return ("improvement" if lo > 1 else "regression" if hi < 1 else "not_separated"), controls


def fmt(e):
    if not e:
        return "n/a"
    n = e.get("n", e.get("n_points", e.get("attempts")))
    return "%.4f [%.4f, %.4f] (n=%s)" % (e["estimate"], e["ci95"][0], e["ci95"][1], n)


def table(result):
    s = result["statistics"]
    lines = ["# n=83 Z[tau]-multiplier closure (M38 primary, M10 secondary): frozen result", "",
             "Verdict: **%s**" % result["decision"], "", "| statistic | estimate [95%] |", "| --- | --- |"]
    for key in ("primary_e2e_kP_cP_over_kM38_cM38", "aa_e2e_kM38_cM38_over_kM38aa_cM38aa", "aa_cold_cM38_over_cM38aa",
                "planted_rank_attempt_kM38X_over_kM38", "rank_attempt_kM38_over_kM38aa",
                "secondary_e2e_kP_cP_over_kM10_cM10", "secondary_e2e_kM10_cM10_over_kM38_cM38",
                "cold_without_rank_cP_over_cM38", "setup_cP_over_cM38", "online_cP_over_cM38",
                "index_build_cP_over_cM38", "peak_rss_cP_over_cM38", "cold_without_rank_cP_over_cM10",
                "online_cP_over_cM10", "e2e_cold_gap_kP_cP_over_rT", "e2e_cold_gap_kM38_cM38_over_rT",
                "e2e_cold_gap_kM10_cM10_over_rT", "online_gap_cP_over_rT", "online_gap_cM38_over_rT",
                "online_gap_cM10_over_rT"):
        lines.append("| %s | %s |" % (key, fmt(s.get(key))))
    for arm, law in (s.get("probe_law") or {}).items():
        lines.append("| probe law %s (mean probes per relation / law) | %s |" % (arm, fmt(law)))
    rank = {k: v for k, v in s.get("rank_stage", {}).items() if not k.startswith("k")}
    lines += ["", "End-to-end means (ms): " + json.dumps(s.get("e2e_ms")),
              "", "Mean cold without rank (ms): " + json.dumps({k: round(v, 1) for k, v in s.get("mean_cold_ms", {}).items()}),
              "", "S end-to-end cold: " + json.dumps(s.get("S_e2e_cold")),
              "", "S online: " + json.dumps(s.get("S_online")),
              "", "Rank stage: " + json.dumps(rank),
              "", "Mean rank stage (ms): " + json.dumps({k: v.get("mean_rank_stage_ms") for k, v in s.get("rank_stage", {}).items()
                                                        if k.startswith("k")}),
              "", "ns per probe: " + json.dumps({k: v.get("ns_per_probe") for k, v in s.get("rank_stage", {}).items()
                                                 if k.startswith("k")}),
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
    checks, detail = correctness(runs, protocol, args.receipt)
    checks["receipt_matches_schedule"] = not problems
    if args.correctness_only:
        out = {"checks": checks, "detail": detail, "problems": problems, "rows": len(runs)}
        (args.receipt / "correctness.json").write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
        print(json.dumps(out, sort_keys=True))
        return
    stats = statistics_block(runs, protocol)
    checks["every_scheduled_row_present"] = not missing
    checks["all_points_complete"] = stats["complete_points"] == protocol["design"]["cold_points"]
    blocks = rank_blocks(runs)
    checks["all_rank_blocks_complete"] = all(
        set(b["arms"]) <= set(blocks.get(b["id"], {})) for b in protocol["design"]["rank_blocks"])
    decision, controls = decide(checks, stats)
    result = {"kind": protocol["kind"], "decision": decision, "checks": checks, "controls": controls,
              "detail": detail, "problems": problems,
              "skipped_time_guard": sum(1 for r in runs if r["status"] == "skipped_time_guard"),
              "contention_flags": [{"serial": r["serial"], "arm": r["arm"], "flags": r["contention"]}
                                   for r in runs if r.get("contention")],
              "statistics": stats}
    (args.receipt / "result.json").write_text(json.dumps(result, indent=1, sort_keys=True) + "\n")
    (args.receipt / "result_table.md").write_text(table(result))
    print(json.dumps({"decision": decision, "primary": stats.get("primary_e2e_kP_cP_over_kM38_cM38"),
                      "controls": controls, "checks": checks}, sort_keys=True))


if __name__ == "__main__":
    main()
