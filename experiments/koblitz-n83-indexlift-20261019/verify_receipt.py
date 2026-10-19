#!/usr/bin/env python3
"""Audit a receipt of the n=83 index-lift run and apply the frozen decision rule.

1. loads `runs.jsonl` against `schedule.json` and decodes every raw record;
2. checks the gates of `protocol.json` (per-process layout, fold, B's index
   digests, the frozen layout digests, the index canonicalizer, the planted
   index check, the scan self-test mode and the rank counters are checked
   by `arm.py`; here: one scalar per point across every IC arm and the
   tuned rho with an oracle replay, one relation and one probe count per
   point across every IC process, Q0 against the archived Feistel identity
   in every Q0 arm, one index digest set across every IC process, and per
   rank block the factor-log tables, relation digests, per-attempt probes,
   root calls and point-addition counters of kP and kPI);
3. checks the controls (A/A, sharing, planted) and computes the primary and
   every secondary statistic with bootstrap intervals;
4. writes `result.json` and `result_table.md` into the receipt directory.

The rank stage is shared: K = the mean over the rank blocks of each block's
mean rank stage over its rank processes (kP, index built with the selected
canonicalizer; kPI, index built with lift_scan: the same rank code over the
same index, gated byte for byte). E2E(c) = K + mean cold(c) over the cold
points. Primary R = E2E(cP) / E2E(cPI); its bootstrap resamples the rank
blocks, then attempt indices within each drawn block (used for both rank
processes of the block; the stage's non-attempt time is kept), and the
cold points (paired across cP and cPI), 10,000 draws.

`--correctness-only` (local smoke) runs steps 1-2 on whatever rows exist and
writes `correctness.json` with no timing values in it.

`koblitz-n83-rankprobe-20261019`'s `verify_receipt.py` with this
experiment's arms (baseline cP, A/A cPaa, candidate cPI, secondary cPIT,
planted cPIX; rank kP and kPI), the shared rank stage and new seeds.
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
SNAPSHOT = HERE / "snapshots" / "r770"
IC_COLD = ("cP", "cPaa", "cPI", "cPIT", "cPIX")
RANK = ("kP", "kPI")
DRAWS = 10000
SEED = 20261119


def jsonl(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def raw_record(receipt, row, scheduled, kind):
    lines = (receipt / row["stdout_file"]).read_text().splitlines()
    encoded = next((line[len("raw_b64="):]
                    for line in lines if line.startswith("raw_b64=")), None)
    if encoded is None:
        return None, ["no raw producer record"]
    try:
        raw_bytes = base64.b64decode(encoded, validate=True)
        raw = json.loads(raw_bytes)
    except (ValueError, json.JSONDecodeError) as error:
        return None, ["raw producer record is not valid base64 JSON: %s" % error]

    receipt_line = next((line for line in reversed(lines) if "raw_result_sha256=" in line), None)
    if receipt_line is None:
        return raw, ["producer summary has no raw-result digest"]
    summary = dict(word.split("=", 1) for word in receipt_line.split() if "=" in word)
    actual_sha256 = hashlib.sha256(raw_bytes).hexdigest()
    issues = []
    if summary.get("raw_result_sha256") != actual_sha256:
        issues.append("raw producer record digest differs from wrapper summary")

    expected = {"arm": scheduled["arm"], "kind": kind, "panel": scheduled["point_id"],
                "point": [str(value) for value in scheduled["point"]], "seed": scheduled["seed"]}
    for key, value in expected.items():
        if raw.get(key) != value:
            issues.append("raw producer record %s differs from the frozen schedule" % key)
    return raw, issues


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
            expected_kind = protocol["arms"][run["arm"]]["kind"]
            raw, raw_issues = raw_record(receipt, row, run, expected_kind)
            if raw is None:
                item["issues"] += raw_issues
                item["status"] = "invalid"
            else:
                if raw_issues:
                    item["issues"] += raw_issues
                    item["status"] = "invalid"
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
                    item["index_digest"] = {k: v for k, v in (summary.get("index_digest") or {}).items()
                                            if k != "accounting"} or None
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
    scalar_ok, replay_ok, rel_ok, probe_ok = {}, {}, {}, {}
    for unit, arms in sorted(units.items()):
        scalars = {str(r["f"].get("recovered_scalar")) for r in arms.values()}
        scalar_ok[unit] = len(scalars) == 1 and "None" not in scalars
        point = next(iter(arms.values()))["point"]
        replay_ok[unit] = scalar_ok[unit] and replay(point, next(iter(scalars)))
        ic = [r for r in arms.values() if r["kind"] != "rho_tuned"]
        rel_ok[unit] = len({json.dumps(r["f"]["relation"]) for r in ic}) <= 1
        probe_ok[unit] = len({r["f"].get("ops") for r in ic}) <= 1 and None not in {r["f"].get("ops") for r in ic}
    checks["one_scalar_per_point_ic_and_rho"] = all(scalar_ok.values()) if scalar_ok else None
    checks["oracle_replay"] = all(replay_ok.values()) if replay_ok else None
    checks["one_relation_per_point_every_ic_process"] = all(rel_ok.values()) if rel_ok else None
    checks["one_probe_count_per_point_every_ic_process"] = all(probe_ok.values()) if probe_ok else None
    digests = set()
    for r in executed:
        if r["kind"] != "rho_tuned" and r["status"] == "valid":
            digests.add(json.dumps(r.get("index_digest"), sort_keys=True))
    checks["one_index_digest_set_every_ic_process"] = (len(digests) == 1 and "null" not in digests) if digests else None
    q0 = units.get("q0", {})
    want = protocol["online"]["q0_identity"]
    if q0:
        checks["q0_matches_archived_feistel_identity"] = all(
            r["f"].get("relation") == want["relation"] and str(r["f"].get("recovered_scalar")) == want["scalar"] and
            r["f"].get("ops") == want["probes_folded"] for r in q0.values())
    else:
        checks["q0_matches_archived_feistel_identity"] = None
    rank_rows = [r for r in executed if r["kind"] == "ic_rank"]
    checks["rank_tables_equal_archived"] = (all(r["status"] == "valid" and r["f"].get("logs_equal_archived") is True
                                                for r in rank_rows) if rank_rows else None)
    rank_ok = {}
    for block, arms in rank_blocks(runs).items():
        rows = [arms[a] for a in RANK if a in arms]
        digests = {r["f"].get("rank_relations_blake3") for r in rows}
        probes = {json.dumps(r["rank_attempt_probes"]) for r in rows}
        calls = {r["f"].get("rank_root_calls_total") for r in rows}
        counters = {json.dumps([(r["f"].get("rank_padd") or {}).get(key) for key in
                                ("fallback_states", "irregular_inputs", "resolved_hits", "swapped_pairs")] +
                               [(r["f"].get("rank_frame") or {}).get("builds")])
                    for r in rows}
        rank_ok[block] = (len(digests) == 1 and None not in digests and len(probes) == 1 and
                          len(calls) == 1 and None not in calls and len(counters) == 1 and
                          "null" not in next(iter(counters)) and
                          all(len(r["rank_attempt_probes"] or []) == len(r["rank_attempt_ns"] or []) for r in rows))
    checks["rank_relations_probes_root_calls_and_counters_identical_per_block"] = (
        all(rank_ok.values()) if rank_ok else None)
    detail.update({"units_seen": len(units),
                   "scalar_failures": sorted(u for u, v in scalar_ok.items() if not v),
                   "relation_failures": sorted(u for u, v in rel_ok.items() if not v),
                   "probe_failures": sorted(u for u, v in probe_ok.items() if not v),
                   "rank_failures": sorted(u for u, v in rank_ok.items() if not v),
                   "rank_padd_counters": {"%s/%s" % (b, a): r["f"].get("rank_padd")
                                          for b, arms in sorted(rank_blocks(runs).items())
                                          for a, r in sorted(arms.items())},
                   "rank_frame_counters": {"%s/%s" % (b, a): r["f"].get("rank_frame")
                                           for b, arms in sorted(rank_blocks(runs).items())
                                           for a, r in sorted(arms.items())}})
    return checks, detail


def ratio_of_means(pairs):
    return sum(a for a, _ in pairs) / sum(b for _, b in pairs)


def geo_ratio(pairs):
    return math.exp(statistics.mean(math.log(a) - math.log(b) for a, b in pairs))


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


def paired_blocks(runs, a, b):
    """[(rest_a, att_a, rest_b, att_b)] for every block holding both rank arms."""
    out = []
    for _, arms in sorted(rank_blocks(runs).items()):
        if a in arms and b in arms:
            ra, xa = process(arms[a])
            rb, xb = process(arms[b])
            if len(xa) == len(xb):
                out.append((ra, xa, rb, xb))
    return out


def shared_blocks(runs):
    """[(rest_mean, [[attempt ms of each rank process]])] for every block holding every rank arm."""
    out = []
    for _, arms in sorted(rank_blocks(runs).items()):
        if not all(a in arms for a in RANK):
            continue
        parts = [process(arms[a]) for a in RANK]
        if len({len(x) for _, x in parts}) == 1:
            out.append((statistics.mean(rest for rest, _ in parts), [x for _, x in parts]))
    return out


def e2e_shared(runs, complete, cold_a, cold_b, seed, rho_denominator=False):
    """E2E(cold_a) / E2E(cold_b) with the shared rank stage K, or E2E(cold_a) / mean rho cold."""
    blocks = shared_blocks(runs)
    units = sorted(complete)
    if not blocks or not units:
        return None

    def block_value(block, picks):
        rest, procs = block
        if picks is None:
            return rest + statistics.mean(sum(x) for x in procs)
        return rest + statistics.mean(sum(x[i] for i in picks) for x in procs)

    def value(block_values, point_draw):
        k = statistics.mean(block_values)
        numerator = k + statistics.mean(complete[u][cold_a]["f"]["cold_ms"] for u in point_draw)
        if rho_denominator:
            return numerator / statistics.mean(complete[u]["rT"]["f"]["rho_cold_ms"] for u in point_draw)
        return numerator / (k + statistics.mean(complete[u][cold_b]["f"]["cold_ms"] for u in point_draw))

    point = value([block_value(b, None) for b in blocks], units)
    rng = random.Random(seed)
    draws = []
    for _ in range(DRAWS):
        bv = []
        for _ in blocks:
            block = blocks[rng.randrange(len(blocks))]
            bv.append(block_value(block, rng.choices(range(len(block[1][0])), k=len(block[1][0]))))
        pd = [units[rng.randrange(len(units))] for _ in units]
        draws.append(value(bv, pd))
    draws.sort()
    return {"estimate": point, "ci95": [draws[int(0.025 * DRAWS)], draws[int(0.975 * DRAWS) - 1]],
            "n_points": len(units), "rank_blocks": len(blocks),
            "shared_rank_stage_ms": statistics.mean(block_value(b, None) for b in blocks),
            "bootstrap": ("blocks resampled; attempts resampled within each drawn block, shared by the block's "
                          "rank processes; points resampled, paired; %d draws" % DRAWS)}


def e2e_own(runs, complete, rank_a, cold_a, rank_b, cold_b, seed):
    """E2E(rank_a, cold_a) / E2E(rank_b, cold_b), each arm with its own rank processes (secondary)."""
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
        return (num / k + statistics.mean(complete[u][cold_a]["f"]["cold_ms"] for u in point_draw)) / (
            den / k + statistics.mean(complete[u][cold_b]["f"]["cold_ms"] for u in point_draw))

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


def attempt_ratio(runs, a, b, seed, select=None):
    """Per-attempt cost a / b, attempts paired within blocks (optionally a subset of attempt indices)."""
    blocks = paired_blocks(runs, a, b)
    if not blocks:
        return None
    pairs = []
    for _, xa, _, xb in blocks:
        idx = range(len(xa)) if select is None else select(xa, xb)
        pairs.append([(xa[i], xb[i]) for i in idx])
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
    out["primary_e2e_shared_cP_over_cPI"] = e2e_shared(runs, complete, "cP", "cPI", SEED)
    out["aa_e2e_shared_cP_over_cPaa"] = e2e_shared(runs, complete, "cP", "cPaa", SEED + 1)
    out["aa_cold_cP_over_cPaa"] = estimate(paired(complete, "cP", "cPaa", "cold_ms"), SEED + 2)
    out["planted_cold_cPIX_over_cPI"] = estimate(paired(complete, "cPIX", "cPI", "cold_ms"), SEED + 3)
    out["sharing_rank_attempt_kPI_over_kP"] = attempt_ratio(runs, "kPI", "kP", SEED + 4)
    out["secondary_e2e_own_kP_cP_over_kPI_cPI"] = e2e_own(runs, complete, "kP", "cP", "kPI", "cPI", SEED + 5)
    out["secondary_e2e_shared_cP_over_cPIT"] = e2e_shared(runs, complete, "cP", "cPIT", SEED + 6)
    for a, b, k in (("cP", "cPI", 10), ("cPI", "cPIT", 11), ("cP", "cPIT", 12), ("cPIX", "cP", 13)):
        out["cold_without_rank_%s_over_%s" % (a, b)] = estimate(paired(complete, a, b, "cold_ms"), SEED + k)
    for key, name, k in (("setup_ms", "setup", 20), ("index_ms", "index_build", 21), ("online_ms", "online", 22),
                         ("peak_rss_bytes", "peak_rss", 23), ("scan_selftest_ms", "scan_selftest", 24)):
        out[name + "_cP_over_cPI"] = estimate(paired(complete, "cP", "cPI", key), SEED + k)
    out["scan_selftest_cPI_over_cPIT"] = estimate(paired(complete, "cPI", "cPIT", "scan_selftest_ms"), SEED + 25)
    out["online_cPI_over_cPIT"] = estimate(paired(complete, "cPI", "cPIT", "online_ms"), SEED + 26)
    for key in ("cold_ms", "setup_ms", "online_ms", "index_ms", "scan_selftest_ms", "peak_rss_bytes"):
        out["mean_" + key] = ({arm: statistics.mean(a[arm]["f"][key] for a in complete.values()) for arm in IC_COLD}
                              if complete else {})
    rank_out = {}
    for arm in RANK:
        rows = [r for r in runs if r["kind"] == "ic_rank" and r["arm"] == arm and r["status"] == "valid"]
        if rows:
            probes = sum(v for r in rows for v in r["rank_attempt_probes"] if v is not None)
            ns = sum(v for r in rows for v in r["rank_attempt_ns"])
            rank_out[arm] = {"rank_stage_ms": [r["f"]["rank_stage_ms"] for r in rows],
                             "mean_rank_stage_ms": statistics.mean(r["f"]["rank_stage_ms"] for r in rows),
                             "index_ms": [r["f"]["index_ms"] for r in rows],
                             "single_process_e2e_cold_ms": [r["f"]["cold_ms"] for r in rows],
                             "attempts": [len(r["rank_attempt_ns"] or []) for r in rows],
                             "mean_attempt_ms": ns / 1e6 / sum(len(r["rank_attempt_ns"]) for r in rows),
                             "ns_per_probe": ns / probes if probes else None,
                             "mean_attempt_probes": probes / sum(len(r["rank_attempt_probes"]) for r in rows)}
    if "kP" in rank_out and "kPI" in rank_out:
        rank_out["rank_stage_kPI_over_kP"] = rank_out["kPI"]["mean_rank_stage_ms"] / rank_out["kP"]["mean_rank_stage_ms"]
        rank_out["single_process_e2e_kP_over_kPI"] = (statistics.mean(rank_out["kP"]["single_process_e2e_cold_ms"]) /
                                                      statistics.mean(rank_out["kPI"]["single_process_e2e_cold_ms"]))
    out["rank_stage"] = rank_out
    primary = out["primary_e2e_shared_cP_over_cPI"]
    if complete and primary:
        k = primary["shared_rank_stage_ms"]
        out["e2e_ms"] = {"shared_rank_stage": k}
        for arm in IC_COLD:
            out["e2e_ms"]["K+" + arm] = k + out["mean_cold_ms"][arm]
        out["e2e_ms"]["rank_share_cP"] = k / (k + out["mean_cold_ms"]["cP"])
        out["e2e_ms"]["rank_share_cPI"] = k / (k + out["mean_cold_ms"]["cPI"])
    rho = [a["rT"]["f"] for a in complete.values()]
    if rho and "e2e_ms" in out:
        steps = sum(float(r["ops"]) for r in rho)
        ms_per_step = sum(r["online_ms"] for r in rho) / steps
        sqrt_r = protocol["online"]["sqrt_r"]
        unit = ms_per_step * sqrt_r
        out["rho_ms_per_step"] = ms_per_step
        out["rho_mean_online_ms"] = statistics.mean(r["online_ms"] for r in rho)
        out["rho_mean_cold_ms"] = statistics.mean(r["rho_cold_ms"] for r in rho)
        out["S_unit_ms"] = unit
        out["S_rho_cold"] = out["rho_mean_cold_ms"] / unit
        out["S_rho_online"] = out["rho_mean_online_ms"] / unit
        out["S_rank_stage"] = out["e2e_ms"]["shared_rank_stage"] / unit
        out["S_e2e_cold"] = {arm: out["e2e_ms"]["K+" + arm] / unit for arm in ("cP", "cPI", "cPIT")}
        out["S_cold_without_rank"] = {arm: out["mean_cold_ms"][arm] / unit for arm in IC_COLD}
        out["S_online"] = {arm: out["mean_online_ms"][arm] / unit for arm in IC_COLD}
        out["delta_S_e2e_cold_cP_to_cPI"] = out["S_e2e_cold"]["cPI"] - out["S_e2e_cold"]["cP"]
        for arm, k in (("cP", 50), ("cPI", 51), ("cPIT", 52)):
            out["e2e_cold_gap_%s_over_rT" % arm] = e2e_shared(runs, complete, arm, None, SEED + k,
                                                              rho_denominator=True)
        for arm, k in (("cP", 60), ("cPI", 61)):
            out["online_gap_%s_over_rT" % arm] = estimate(
                [(a[arm]["f"]["online_ms"], a["rT"]["f"]["online_ms"]) for a in complete.values()], SEED + k)
    return out


def decide(checks, stats):
    # Required checks are three-state so partial receipts can report unknown.
    # Unknown is useful in the diagnostic output, but it cannot satisfy a gate.
    gates_ok = all(v is True for v in checks.values())
    aa_e2e, aa_cold = stats.get("aa_e2e_shared_cP_over_cPaa"), stats.get("aa_cold_cP_over_cPaa")
    sharing = stats.get("sharing_rank_attempt_kPI_over_kP")
    planted, primary = stats.get("planted_cold_cPIX_over_cPI"), stats.get("primary_e2e_shared_cP_over_cPI")
    controls = {"aa_e2e_inside_0.97_1.03": aa_e2e is not None and 0.97 <= aa_e2e["estimate"] <= 1.03,
                "aa_cold_inside_0.97_1.03": aa_cold is not None and 0.97 <= aa_cold["estimate"] <= 1.03,
                "sharing_rank_attempt_inside_0.97_1.03": sharing is not None and 0.97 <= sharing["estimate"] <= 1.03,
                "planted_lower_bound_above_1": planted is not None and planted["ci95"][0] > 1.0}
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
    lines = ["# n=83 index lift (lift_scan in the index build): frozen result", "",
             "Verdict: **%s**" % result["decision"], "", "| statistic | estimate [95%] |", "| --- | --- |"]
    for key in ("primary_e2e_shared_cP_over_cPI", "aa_e2e_shared_cP_over_cPaa", "aa_cold_cP_over_cPaa",
                "sharing_rank_attempt_kPI_over_kP", "planted_cold_cPIX_over_cPI",
                "secondary_e2e_own_kP_cP_over_kPI_cPI", "secondary_e2e_shared_cP_over_cPIT",
                "cold_without_rank_cP_over_cPI", "cold_without_rank_cPI_over_cPIT", "cold_without_rank_cP_over_cPIT",
                "cold_without_rank_cPIX_over_cP", "setup_cP_over_cPI", "index_build_cP_over_cPI",
                "online_cP_over_cPI", "peak_rss_cP_over_cPI", "scan_selftest_cP_over_cPI",
                "scan_selftest_cPI_over_cPIT", "online_cPI_over_cPIT",
                "e2e_cold_gap_cP_over_rT", "e2e_cold_gap_cPI_over_rT", "e2e_cold_gap_cPIT_over_rT",
                "online_gap_cP_over_rT", "online_gap_cPI_over_rT"):
        lines.append("| %s | %s |" % (key, fmt(s.get(key))))
    rank = {k: v for k, v in s.get("rank_stage", {}).items() if not k.startswith("k")}
    lines += ["", "End-to-end means (ms): " + json.dumps(s.get("e2e_ms")),
              "", "Mean cold without rank (ms): " + json.dumps({k: round(v, 1) for k, v in s.get("mean_cold_ms", {}).items()}),
              "", "Mean index build (ms): " + json.dumps({k: round(v, 1) for k, v in s.get("mean_index_ms", {}).items()}),
              "", "S end-to-end cold: " + json.dumps(s.get("S_e2e_cold")),
              "", "S online: " + json.dumps(s.get("S_online")),
              "", "Rank stage: " + json.dumps(rank),
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
    checks["all_rank_blocks_complete"] = len([b for b in rank_blocks(runs).values() if set(RANK) <= set(b)]) == \
        len(protocol["design"]["rank_blocks"])
    decision, controls = decide(checks, stats)
    result = {"kind": protocol["kind"], "decision": decision, "checks": checks, "controls": controls,
              "detail": detail, "problems": problems,
              "skipped_time_guard": sum(1 for r in runs if r["status"] == "skipped_time_guard"),
              "contention_flags": [{"serial": r["serial"], "arm": r["arm"], "flags": r["contention"]}
                                   for r in runs if r.get("contention")],
              "statistics": stats}
    (args.receipt / "result.json").write_text(json.dumps(result, indent=1, sort_keys=True) + "\n")
    (args.receipt / "result_table.md").write_text(table(result))
    print(json.dumps({"decision": decision, "primary": stats.get("primary_e2e_shared_cP_over_cPI"),
                      "controls": controls, "checks": checks}, sort_keys=True))


if __name__ == "__main__":
    main()
