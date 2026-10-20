#!/usr/bin/env python3
"""Audit a receipt of the n=83 K899 run and apply the frozen decision rule.

1. loads `runs.jsonl` against `schedule.json` and decodes every raw record;
2. checks the gates of `protocol.json` (per-process K, base, layout, fold,
   index digests and frame counters are checked by `arm.py`; here: one
   scalar per point across every IC process of both K and the tuned rho,
   with an oracle replay; one relation and one probe count per point and K
   across the IC processes of that K; Q0 against the archived K600 Feistel
   identity and the frozen K899 identity; every rank table equal to its K's
   frozen table; per rank block, kP899, kP899aa and kPX899 with one relation
   digest, one per-attempt probe vector, one root-call total and one set of
   point-addition counters; and the probe law band: per K, the mean probes
   per rank attempt pooled over the blocks, over r / (166 E_K), inside the
   frozen band);
3. checks the controls (A/A, planted) and computes the primary and every
   secondary statistic with bootstrap intervals;
4. writes `result.json` and `result_table.md` into the receipt directory.

E2E(k, c) = mean rank stage of rank arm k over the rank blocks + mean
cold(c) over the cold points. Primary R = E2E(kP600, cP600) / E2E(kP899,
cP899). The two K run different attempts (K600 has 600 attempts per block,
K899 899, on other columns), so the bootstrap resamples the rank blocks
(the same drawn block ids for both arms: one process of each per block,
run back to back), then the attempt indices of each arm within each drawn
block independently, keeping each process's non-attempt time, and the cold
points paired across the cold arms; 10,000 draws. Where two rank arms run
the same attempts (kP899 / kP899aa, kPX899 / kP899) the attempts are paired.

`--correctness-only` (local smoke) runs steps 1-2 on whatever rows exist and
writes `correctness.json` with no timing values in it.

Built from `koblitz-n83-rankprobe-20261019`'s `verify_receipt.py` (load,
raw decoding, paired estimators and the S / rho block unchanged in method).
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
IC_COLD = ("cP600", "cP899", "cP899aa", "cPI600", "cPI899")
RANK = ("kP600", "kP899", "kP899aa", "kPX899")
SAME_ATTEMPTS = ("kP899", "kP899aa", "kPX899")
DRAWS = 10000
SEED = 20261019899
R_ORDER = 8569786107849059


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
        arm = protocol["arms"][run["arm"]]
        item = {"serial": serial, "segment": segment["id"], "panel": segment["panel"], "arm": run["arm"],
                "kind": arm["kind"], "K": arm.get("K"), "unit": run["point_id"], "point": run["point"],
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


def rank_blocks(runs):
    """{segment id: {rank arm: row}} over valid rank rows."""
    out = {}
    for r in runs:
        if r["status"] == "valid" and r["kind"] == "ic_rank":
            out.setdefault(r["segment"], {})[r["arm"]] = r
    return out


def law(entries):
    return R_ORDER / (166.0 * entries)


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
        for k in (600, 899):
            ic = [r for r in arms.values() if r["kind"] != "rho_tuned" and r["K"] == k]
            if not ic:
                continue
            rel_ok["%s/K%d" % (unit, k)] = len({json.dumps(r["f"]["relation"]) for r in ic}) <= 1
            ops = {r["f"].get("ops") for r in ic}
            probe_ok["%s/K%d" % (unit, k)] = len(ops) <= 1 and None not in ops
    checks["one_scalar_per_point_both_K_and_rho"] = all(scalar_ok.values()) if scalar_ok else None
    checks["oracle_replay"] = all(replay_ok.values()) if replay_ok else None
    checks["one_relation_per_point_and_K"] = all(rel_ok.values()) if rel_ok else None
    checks["one_probe_count_per_point_and_K"] = all(probe_ok.values()) if probe_ok else None
    q0 = units.get("q0", {})
    if q0:
        ok = True
        for r in q0.values():
            want = protocol["online"]["k"][str(r["K"])]["q0_identity"]
            ok &= (r["f"].get("relation") == want["relation"] and str(r["f"].get("recovered_scalar")) == want["scalar"]
                   and r["f"].get("ops") == want["probes_folded"])
        checks["q0_matches_frozen_identity_per_K"] = ok
    else:
        checks["q0_matches_frozen_identity_per_K"] = None
    rank_rows = [r for r in executed if r["kind"] == "ic_rank"]
    checks["rank_tables_equal_frozen_per_K"] = (all(r["status"] == "valid" and r["f"].get("logs_equal_archived") is True
                                                    for r in rank_rows) if rank_rows else None)
    rank_ok = {}
    for block, arms in rank_blocks(runs).items():
        rows = [arms[a] for a in SAME_ATTEMPTS if a in arms]
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
    checks["k899_rank_arms_identical_relations_probes_root_calls_counters_per_block"] = (
        all(rank_ok.values()) if rank_ok else None)
    band = protocol["law_band"]["band"]
    law_out = {}
    for k in (600, 899):
        rows = [r for r in rank_rows if r["status"] == "valid" and r["K"] == k and r["arm"] in ("kP600", "kP899")]
        probes = [v for r in rows for v in (r["rank_attempt_probes"] or []) if v is not None]
        if probes:
            entries = protocol["online"]["k"][str(k)]["root_table_entries"]
            mean = statistics.mean(probes)
            law_out["K%d" % k] = {"attempts": len(probes), "mean_probes": mean, "law": law(entries),
                                  "ratio": mean / law(entries),
                                  "se_ratio": statistics.pstdev(probes) / math.sqrt(len(probes)) / law(entries)}
    detail["law"] = law_out
    checks["probe_law_band_both_K"] = (all(band[0] <= v["ratio"] <= band[1] for v in law_out.values())
                                       and len(law_out) == 2) if law_out else None
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


def blocks_of(runs, a, b):
    """[(rest_a, att_a, rest_b, att_b)] for every block holding both rank arms."""
    out = []
    for _, arms in sorted(rank_blocks(runs).items()):
        if a in arms and b in arms:
            ra, xa = process(arms[a])
            rb, xb = process(arms[b])
            out.append((ra, xa, rb, xb))
    return out


def e2e(runs, complete, rank_a, cold_a, rank_b, cold_b, seed, paired_attempts, rho_denominator=False):
    """E2E(rank_a, cold_a) / E2E(rank_b, cold_b), or E2E(rank_a, cold_a) / mean rho cold.

    paired_attempts: the two rank arms ran the same attempts (same K, seed); the
    drawn attempt indices are shared. Otherwise each arm's attempts are drawn
    independently within the drawn block."""
    blocks = blocks_of(runs, rank_a, rank_b if not rho_denominator else rank_a)
    units = sorted(complete)
    if not blocks or not units:
        return None
    if paired_attempts and any(len(xa) != len(xb) for _, xa, _, xb in blocks):
        return None

    def value(block_draw, picks_a, picks_b, point_draw):
        num = den = 0.0
        for (ra, xa, rb, xb), pa, pb in zip(block_draw, picks_a, picks_b):
            num += ra + (sum(xa) if pa is None else sum(xa[i] for i in pa))
            den += rb + (sum(xb) if pb is None else sum(xb[i] for i in pb))
        k = len(block_draw)
        numerator = num / k + statistics.mean(complete[u][cold_a]["f"]["cold_ms"] for u in point_draw)
        if rho_denominator:
            return numerator / statistics.mean(complete[u]["rT"]["f"]["rho_cold_ms"] for u in point_draw)
        return numerator / (den / k + statistics.mean(complete[u][cold_b]["f"]["cold_ms"] for u in point_draw))

    none = [None] * len(blocks)
    point = value(blocks, none, none, units)
    rng = random.Random(seed)
    draws = []
    for _ in range(DRAWS):
        bd = [blocks[rng.randrange(len(blocks))] for _ in blocks]
        pa = [rng.choices(range(len(b[1])), k=len(b[1])) for b in bd]
        pb = pa if paired_attempts else [rng.choices(range(len(b[3])), k=len(b[3])) for b in bd]
        pd = [units[rng.randrange(len(units))] for _ in units]
        draws.append(value(bd, pa, pb, pd))
    draws.sort()
    return {"estimate": point, "ci95": [draws[int(0.025 * DRAWS)], draws[int(0.975 * DRAWS) - 1]],
            "n_points": len(units), "rank_blocks": len(blocks),
            "bootstrap": ("blocks resampled (same block ids for both arms); attempts resampled within each drawn "
                          "block, %s; points resampled, paired; %d draws"
                          % ("paired across the two rank arms" if paired_attempts else
                             "independently per arm (different K, different attempts)", DRAWS))}


def stage_ratio(runs, a, b, seed):
    """Whole rank stage a / b (means over blocks), unpaired attempts within drawn blocks."""
    blocks = blocks_of(runs, a, b)
    if not blocks:
        return None

    def value(bd, pa, pb):
        num = sum(ra + (sum(xa) if p is None else sum(xa[i] for i in p)) for (ra, xa, _, _), p in zip(bd, pa))
        den = sum(rb + (sum(xb) if p is None else sum(xb[i] for i in p)) for (_, _, rb, xb), p in zip(bd, pb))
        return num / den

    none = [None] * len(blocks)
    est = value(blocks, none, none)
    rng = random.Random(seed)
    draws = []
    for _ in range(2000):
        bd = [blocks[rng.randrange(len(blocks))] for _ in blocks]
        draws.append(value(bd, [rng.choices(range(len(b[1])), k=len(b[1])) for b in bd],
                           [rng.choices(range(len(b[3])), k=len(b[3])) for b in bd]))
    draws.sort()
    return {"estimate": est, "ci95": [draws[50], draws[1949]], "rank_blocks": len(blocks),
            "bootstrap": "blocks then attempts resampled, independently per arm, 2,000 draws"}


def attempt_ratio(runs, a, b, seed):
    """Per-attempt cost a / b for two arms with the same attempts, paired within blocks."""
    blocks = [blk for blk in blocks_of(runs, a, b) if len(blk[1]) == len(blk[3])]
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
    out["primary_e2e_kP600_cP600_over_kP899_cP899"] = e2e(runs, complete, "kP600", "cP600", "kP899", "cP899",
                                                           SEED, paired_attempts=False)
    out["aa_e2e_kP899_cP899_over_kP899aa_cP899aa"] = e2e(runs, complete, "kP899", "cP899", "kP899aa", "cP899aa",
                                                          SEED + 1, paired_attempts=True)
    out["aa_cold_cP899_over_cP899aa"] = estimate(paired(complete, "cP899", "cP899aa", "cold_ms"), SEED + 2)
    out["planted_rank_attempt_kPX899_over_kP899"] = attempt_ratio(runs, "kPX899", "kP899", SEED + 3)
    out["rank_attempt_kP899_over_kP899aa"] = attempt_ratio(runs, "kP899", "kP899aa", SEED + 4)
    out["rank_stage_kP600_over_kP899"] = stage_ratio(runs, "kP600", "kP899", SEED + 5)
    out["secondary_e2e_kP600_cPI600_over_kP899_cPI899"] = e2e(runs, complete, "kP600", "cPI600", "kP899",
                                                               "cPI899", SEED + 10, paired_attempts=False)
    out["secondary_e2e_kP600_cP600_over_kP899_cPI899"] = e2e(runs, complete, "kP600", "cP600", "kP899",
                                                              "cPI899", SEED + 11, paired_attempts=False)
    for key, name in (("cold_ms", "cold_without_rank"), ("setup_ms", "setup"), ("index_ms", "index_build"),
                      ("online_ms", "online"), ("peak_rss_bytes", "peak_rss")):
        out[name + "_cP899_over_cP600"] = estimate(paired(complete, "cP899", "cP600", key), SEED + 20)
    out["cold_without_rank_cP600_over_cPI600"] = estimate(paired(complete, "cP600", "cPI600", "cold_ms"), SEED + 21)
    out["cold_without_rank_cP899_over_cPI899"] = estimate(paired(complete, "cP899", "cPI899", "cold_ms"), SEED + 22)
    for key in ("cold_ms", "setup_ms", "online_ms", "index_ms", "peak_rss_bytes", "ops"):
        out["mean_" + key] = ({arm: statistics.mean(float(a[arm]["f"][key]) for a in complete.values())
                               for arm in IC_COLD} if complete else {})
    rank_out = {}
    for arm in RANK:
        rows = [r for r in runs if r["kind"] == "ic_rank" and r["arm"] == arm and r["status"] == "valid"]
        if rows:
            probes = sum(v for r in rows for v in r["rank_attempt_probes"] if v is not None)
            ns = sum(v for r in rows for v in r["rank_attempt_ns"])
            attempts = sum(len(r["rank_attempt_ns"]) for r in rows)
            rank_out[arm] = {"rank_stage_ms": [r["f"]["rank_stage_ms"] for r in rows],
                             "mean_rank_stage_ms": statistics.mean(r["f"]["rank_stage_ms"] for r in rows),
                             "index_ms": [r["f"]["index_ms"] for r in rows],
                             "single_process_e2e_cold_ms": [r["f"]["cold_ms"] for r in rows],
                             "attempts": [len(r["rank_attempt_ns"] or []) for r in rows],
                             "mean_attempt_ms": ns / 1e6 / attempts,
                             "ns_per_probe": ns / probes if probes else None,
                             "ns_per_probe_first50": [
                                 sum(r["rank_attempt_ns"][:50]) / sum(r["rank_attempt_probes"][:50]) for r in rows],
                             "mean_attempt_probes": probes / attempts}
    for a, b in (("kP600", "kP899"), ("kPX899", "kP899"), ("kP899", "kP899aa")):
        if a in rank_out and b in rank_out:
            rank_out["mean_rank_stage_%s_over_%s" % (a, b)] = (rank_out[a]["mean_rank_stage_ms"] /
                                                               rank_out[b]["mean_rank_stage_ms"])
            rank_out["ns_per_probe_%s_over_%s" % (a, b)] = rank_out[a]["ns_per_probe"] / rank_out[b]["ns_per_probe"]
    out["rank_stage"] = rank_out
    if complete and "kP600" in rank_out and "kP899" in rank_out:
        m = out["mean_cold_ms"]
        k6, k9 = rank_out["kP600"]["mean_rank_stage_ms"], rank_out["kP899"]["mean_rank_stage_ms"]
        out["e2e_ms"] = {"kP600+cP600": k6 + m["cP600"], "kP899+cP899": k9 + m["cP899"],
                         "kP600+cPI600": k6 + m["cPI600"], "kP899+cPI899": k9 + m["cPI899"],
                         "rank_share_K600": k6 / (k6 + m["cP600"]), "rank_share_K899": k9 / (k9 + m["cP899"])}
    rho = [a["rT"]["f"] for a in complete.values()]
    if rho and "e2e_ms" in out:
        steps = sum(float(r["ops"]) for r in rho)
        ms_per_step = sum(r["online_ms"] for r in rho) / steps
        unit = ms_per_step * protocol["online"]["sqrt_r"]
        out["rho_ms_per_step"] = ms_per_step
        out["rho_mean_online_ms"] = statistics.mean(r["online_ms"] for r in rho)
        out["rho_mean_cold_ms"] = statistics.mean(r["rho_cold_ms"] for r in rho)
        out["S_unit_ms"] = unit
        out["S_rho_cold"] = out["rho_mean_cold_ms"] / unit
        out["S_rho_online"] = out["rho_mean_online_ms"] / unit
        out["S_e2e_cold"] = {key: out["e2e_ms"][key] / unit for key in
                             ("kP600+cP600", "kP899+cP899", "kP600+cPI600", "kP899+cPI899")}
        out["S_cold_without_rank"] = {arm: out["mean_cold_ms"][arm] / unit for arm in IC_COLD}
        out["S_online"] = {arm: out["mean_online_ms"][arm] / unit for arm in IC_COLD}
        out["delta_S_e2e_cold_K600_to_K899"] = out["S_e2e_cold"]["kP899+cP899"] - out["S_e2e_cold"]["kP600+cP600"]
        for rank_arm, cold_arm, seed in (("kP600", "cP600", 50), ("kP899", "cP899", 51), ("kP899", "cPI899", 52),
                                         ("kP600", "cPI600", 53)):
            out["e2e_cold_gap_%s_%s_over_rT" % (rank_arm, cold_arm)] = e2e(
                runs, complete, rank_arm, cold_arm, None, None, SEED + seed, paired_attempts=True,
                rho_denominator=True)
        for arm, seed in (("cP600", 60), ("cP899", 61)):
            out["online_gap_%s_over_rT" % arm] = estimate(
                [(a[arm]["f"]["online_ms"], a["rT"]["f"]["online_ms"]) for a in complete.values()], SEED + seed)
    return out


def decide(checks, stats, protocol):
    gates_ok = all(v is not False for v in checks.values())
    aa_e2e, aa_cold = stats.get("aa_e2e_kP899_cP899_over_kP899aa_cP899aa"), stats.get("aa_cold_cP899_over_cP899aa")
    planted = stats.get("planted_rank_attempt_kPX899_over_kP899")
    primary = stats.get("primary_e2e_kP600_cP600_over_kP899_cP899")
    controls = {"aa_e2e_inside_0.97_1.03": aa_e2e is not None and 0.97 <= aa_e2e["estimate"] <= 1.03,
                "aa_cold_inside_0.97_1.03": aa_cold is not None and 0.97 <= aa_cold["estimate"] <= 1.03,
                "planted_lower_bound_above_1": planted is not None and planted["ci95"][0] > 1.0}
    if not gates_ok or not all(controls.values()) or primary is None:
        return "invalid", controls
    lo, hi = primary["ci95"]
    return ("improvement" if lo > 1 else "regression" if hi < 1 else "not_separated"), controls


def fmt(e):
    if not e:
        return "n/a"
    n = e.get("n", e.get("n_points", e.get("attempts", e.get("rank_blocks"))))
    return "%.4f [%.4f, %.4f] (n=%s)" % (e["estimate"], e["ci95"][0], e["ci95"][1], n)


def table(result):
    s = result["statistics"]
    lines = ["# n=83 K899 factor base (rank-probe producer at K899 against K600): frozen result", "",
             "Verdict: **%s**" % result["decision"], "", "| statistic | estimate [95%] |", "| --- | --- |"]
    for key in ("primary_e2e_kP600_cP600_over_kP899_cP899", "aa_e2e_kP899_cP899_over_kP899aa_cP899aa",
                "aa_cold_cP899_over_cP899aa", "planted_rank_attempt_kPX899_over_kP899",
                "rank_attempt_kP899_over_kP899aa", "rank_stage_kP600_over_kP899",
                "secondary_e2e_kP600_cPI600_over_kP899_cPI899", "secondary_e2e_kP600_cP600_over_kP899_cPI899",
                "cold_without_rank_cP899_over_cP600", "setup_cP899_over_cP600", "index_build_cP899_over_cP600",
                "online_cP899_over_cP600", "peak_rss_cP899_over_cP600", "cold_without_rank_cP600_over_cPI600",
                "cold_without_rank_cP899_over_cPI899", "e2e_cold_gap_kP600_cP600_over_rT",
                "e2e_cold_gap_kP899_cP899_over_rT", "e2e_cold_gap_kP899_cPI899_over_rT",
                "online_gap_cP600_over_rT", "online_gap_cP899_over_rT"):
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
              "", "Probe law: " + json.dumps(result["detail"].get("law")),
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
        out = {"checks": checks, "detail": {k: v for k, v in detail.items() if k != "law"},
               "problems": problems, "rows": len(runs)}
        (args.receipt / "correctness.json").write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
        print(json.dumps(out, sort_keys=True))
        return
    stats = statistics_block(runs, protocol)
    checks["every_scheduled_row_present"] = not missing
    checks["all_points_complete"] = stats["complete_points"] == protocol["design"]["cold_points"]
    checks["all_rank_blocks_complete"] = len([b for b in rank_blocks(runs).values() if set(RANK) <= set(b)]) == \
        len(protocol["design"]["rank_blocks"])
    decision, controls = decide(checks, stats, protocol)
    result = {"kind": protocol["kind"], "decision": decision, "checks": checks, "controls": controls,
              "detail": detail, "problems": problems,
              "skipped_time_guard": sum(1 for r in runs if r["status"] == "skipped_time_guard"),
              "contention_flags": [{"serial": r["serial"], "arm": r["arm"], "flags": r["contention"]}
                                   for r in runs if r.get("contention")],
              "statistics": stats}
    (args.receipt / "result.json").write_text(json.dumps(result, indent=1, sort_keys=True) + "\n")
    (args.receipt / "result_table.md").write_text(table(result))
    print(json.dumps({"decision": decision, "primary": stats.get("primary_e2e_kP600_cP600_over_kP899_cP899"),
                      "controls": controls, "checks": checks}, sort_keys=True))


if __name__ == "__main__":
    main()
