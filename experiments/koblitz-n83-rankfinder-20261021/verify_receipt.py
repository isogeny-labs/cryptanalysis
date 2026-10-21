#!/usr/bin/env python3
"""Audit a receipt of the n=83 rank-finder experiment and apply the frozen decision rule.

This is the parent's verifier (`koblitz-n83-indexbuild2-20261020`, PR #1009,
itself the Tier 1 template's with two gates added) with this experiment's
arms: side A = kM38IC + cM38IC (the current row, the parent's round-2
index-build producer, arms verbatim from the parent protocol), side B =
kM38RF + cM38RF (the rank-finder derived producer), A/A B against Baa =
kM38RFaa + cM38RFaa, and the planted pairs kM38RFX against kM38RF on the
RANK STAGE (rank processes; kM38RFX runs KIC_RANK_SOLVE=frame_plant). Three
changes besides the names: the planted ratio is on the rank stage; one gate
is added (every IC row's summary names its arm's `rank_probe_pipeline`); the
probe-law blocks are the primary and A/A rank rows (the planted pairs reuse
seed 7). The rank-stage ratio is reported as a labelled stage secondary.

1. Receipt integrity, fail closed. This is the hardened pattern of main
   (index-lift's `raw_record`, the parent's `load`) plus schedule identity:
   * every executed row's raw producer record is valid base64 JSON;
   * its SHA-256 equals the wrapper summary's `raw_result_sha256`;
   * its arm, kind, panel, point and seed equal the frozen schedule's;
   * each row's serial, arm, point, seed and segment equal the schedule's,
     its stdout file is `runs/<serial>.stdout.txt`, and its command line
     carries the schedule's arm, kind, panel, point and seed;
   * the rows ran in schedule order;
   * `runner_start.json` records this `protocol.json`, this `schedule.json`,
     this `arm.py` and this `run_schedule.py` by SHA-256, and no smoke
     subset;
   * every row ran a binary that `runner_start.json` lists, and the binaries
     were unchanged at the end.
2. Tier 1 records: every process placed on the one execution CPU
   (`Cpus_allowed_list`); the CPU record has the same model, microcode and
   flags at the start and the end.
3. The parent's gates: the pre-timing table and closure check; one scalar
   per point across every IC process and rT, replayed in the oracle; one
   relation and one probe count per point and base; one index and layout
   digest set per base, equal to the frozen one; Q0; the rank tables; per M38
   rank seed, identical relation digests, probe vectors, root calls and
   counters; the probe-law band of kM38IC over its distinct seeds; every
   IC row's rank_probe_pipeline equal to its arm's.
4. Statistics. E2E(side) = rank stage of the side's rank process + cold time
   of its cold process. Primary R = sum E2E(A) / sum E2E(B) over the primary
   pairs, with a two-stage paired bootstrap (points, then pairs within
   points; A and B of a pair drawn together; 10,000 draws, fixed seed). The
   controls are the A/A pairs (B against Baa) and the planted pairs
   (kM38RFX against kM38RF, rank stage).
5. Decision. Every required gate must be present and true; a missing or
   unknown gate is a failure. Every control must pass.

The script writes `result.json` and `result_table.md` into the receipt
directory. `--correctness-only` (local smoke) runs steps 1-3 on the rows that
exist, allows a smoke subset, and writes `correctness.json` with no timing
values in it.
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
SAME_TARGETS = ("kM38IC", "kM38RF", "kM38RFaa", "kM38RFX")
LAW_ARMS = ("kM38IC", "kM38RF")
GATED_LAW_ARM = "kM38IC"
PLANTED_ARM, PLANTED_BASE_ARM = "kM38RFX", "kM38RF"
PLANTED_KEY = "planted_rank_stage_%s_over_%s" % (PLANTED_ARM, PLANTED_BASE_ARM)
PROTOCOL = json.loads((HERE / "protocol.json").read_text()) if (HERE / "protocol.json").exists() else {}
DRAWS = PROTOCOL.get("bootstrap", {}).get("draws", 10000)
SEED = PROTOCOL.get("bootstrap", {}).get("seed", 20261050)
AA_BAND = (0.97, 1.03)
REQUIRED_CHECKS = (
    "all_executed_rows_valid", "receipt_matches_schedule", "runner_identity_matches_frozen_files",
    "rows_in_schedule_order", "binaries_unchanged", "placement_pinned_every_process",
    "host_cpu_identity_unchanged", "pre_timing_tables_and_closure_bases_verified",
    "one_scalar_per_point_ic_and_rho", "oracle_replay", "one_relation_per_point_and_base",
    "one_probe_count_per_point_and_base", "one_index_and_layout_digest_set_per_base_equal_frozen",
    "q0_matches_archived_and_frozen_identities", "rank_tables_equal_frozen_verified_tables",
    "rank_relations_probes_root_calls_and_counters_identical_per_seed", "primary_probe_law_inside_frozen_band",
    "every_scheduled_row_present", "all_primary_pairs_complete", "all_aa_pairs_complete",
    "all_planted_pairs_complete", "every_row_ran_its_arms_binary", "every_ic_row_ran_its_arms_rank_probe_pipeline",
)


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


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


def command_issues(row, run, kind):
    argv = row.get("command") or []

    def value(flag):
        return argv[argv.index(flag) + 1] if flag in argv and argv.index(flag) + 1 < len(argv) else None

    want = {"--arm": run["arm"], "--kind": kind, "--panel": run["point_id"], "--seed": str(run["seed"]),
            "--point": "%s,%s" % tuple(run["point"])}
    return ["command %s differs from the frozen schedule" % flag for flag, v in want.items() if value(flag) != v]


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
    unknown = sorted(set(by_serial) - set(scheduled))
    if unknown:
        problems.append("%d rows are not in the schedule" % len(unknown))
    missing = sorted(set(scheduled) - set(by_serial))
    if missing and not partial:
        problems.append("%d scheduled runs have no row" % len(missing))
    order = [row["serial"] for row in rows]
    in_order = order == sorted(order)
    finished = [row["finished_unix_s"] for row in rows if row.get("status") != "skipped_time_guard"]
    in_order &= finished == sorted(finished)
    runs = []
    for serial, row in sorted(by_serial.items()):
        if serial not in scheduled:
            continue
        segment, run = scheduled[serial]
        kind = protocol["arms"][run["arm"]]["kind"]
        if (row["arm"] != run["arm"] or row["point_id"] != run["point_id"] or row["seed"] != run["seed"] or
                row.get("segment") != segment["id"]):
            problems.append("row %d does not match the schedule" % serial)
        item = {"serial": serial, "segment": segment["id"], "panel": segment["panel"], "arm": run["arm"],
                "kind": kind, "unit": run["point_id"], "point": run["point"], "seed": run["seed"],
                "role": run["role"], "pair": run["pair"], "side": run["side"], "position": run["position"],
                "status": row["status"], "issues": list(row.get("issues", [])),
                "contention": row.get("contention_flags", []), "row": row}
        if row["status"] != "skipped_time_guard":
            if row.get("stdout_file") != "runs/%05d.stdout.txt" % serial:
                problems.append("row %d stdout file is not its serial's" % serial)
            cmd = command_issues(row, run, kind)
            if cmd:
                problems.append("row %d: %s" % (serial, "; ".join(cmd)))
            raw, raw_issues = raw_record(receipt, row, run, kind)
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
                item["base"] = protocol["arms"][run["arm"]].get("base")
                if kind == "rho_tuned":
                    item["f"]["rho_cold_ms"] = (item["f"].get("setup_ms") or 0.0) + (item["f"].get("online_ms") or 0.0)
                else:
                    summary = next((rec for rec in raw["records"]
                                    if rec.get("kind") == "compact_orbit_dlp_summary"), {})
                    item["rank_attempt_ns"] = summary.get("rank_attempt_ns")
                    item["rank_attempt_probes"] = summary.get("rank_attempt_probes")
                    item["rank_probe_pipeline"] = summary.get("rank_probe_pipeline")
                    item["summary_present"] = bool(summary)
                    item["index_digest"] = {k: v for k, v in (summary.get("index_digest") or {}).items()
                                            if k != "accounting"} or None
        runs.append(item)
    return runs, problems, missing, in_order


def runner_checks(receipt, runs, partial):
    """Runner identity, binaries, placement and CPU identity (three-state)."""
    checks, detail = {}, {}
    start_path, end_path = receipt / "runner_start.json", receipt / "runner_end.json"
    start = json.loads(start_path.read_text()) if start_path.exists() else None
    end = json.loads(end_path.read_text()) if end_path.exists() else None
    if start is None:
        checks["runner_identity_matches_frozen_files"] = None
    else:
        want = {"protocol_sha256": sha256(HERE / "protocol.json"), "schedule_sha256": sha256(HERE / "schedule.json"),
                "arm_wrapper_sha256": sha256(HERE / "arm.py"), "runner_sha256": sha256(HERE / "run_schedule.py")}
        same = all(start.get(k) == v for k, v in want.items())
        subset = start.get("smoke_subset") or {}
        no_subset = not subset.get("segments") and not subset.get("one_per_arm") and \
            not subset.get("max_runs_per_segment")
        detail["runner_identity"] = {"files_equal": same, "no_smoke_subset": no_subset}
        checks["runner_identity_matches_frozen_files"] = same and (no_subset or partial)
    executed = [r for r in runs if r["status"] != "skipped_time_guard"]
    if start is None or end is None:
        checks["binaries_unchanged"] = None
        checks["host_cpu_identity_unchanged"] = None
    else:
        listed = set((start.get("binaries_sha256") or {}).values())
        checks["binaries_unchanged"] = (start.get("binaries_sha256") == end.get("binaries_sha256_after") and
                                        bool(listed) and all(r["row"].get("binary_sha256") in listed
                                                             for r in executed))
        a, b = start.get("cpu_record"), end.get("cpu_record")
        if not a or not b:
            checks["host_cpu_identity_unchanged"] = None
        else:
            keys = ("model_name", "microcode", "flags_sha256", "cpu_family", "model", "stepping")
            checks["host_cpu_identity_unchanged"] = all(a.get(k) == b.get(k) for k in keys) and \
                a.get("model_name") is not None
            detail["host_class"] = a.get("host_class")
            detail["microcode"] = a.get("microcode")
    if start is None:
        checks["every_row_ran_its_arms_binary"] = None
    else:
        listed_by_name = start.get("binaries_sha256") or {}
        wrong = []
        for r in executed:
            argv = r["row"].get("command") or []
            path = argv[argv.index("--binary") + 1] if "--binary" in argv else ""
            name = Path(path).name
            if name != PROTOCOL.get("arms", {}).get(r["arm"], {}).get("binary") or \
                    r["row"].get("binary_sha256") != listed_by_name.get(name):
                wrong.append(r["serial"])
        checks["every_row_ran_its_arms_binary"] = bool(executed) and not wrong
        detail["rows_on_another_binary"] = wrong
    cpu = start.get("execution_cpu") if start else None
    placed = [((r["row"].get("placement") or {}).get("Cpus_allowed_list"),
               (r["row"].get("placement") or {}).get("execution_cpu")) for r in executed]
    if cpu is None or not executed:
        checks["placement_pinned_every_process"] = None
    else:
        checks["placement_pinned_every_process"] = all(c == str(cpu) and e == cpu for c, e in placed)
    detail["placement_failures"] = [r["serial"] for r, (c, e) in zip(executed, placed) if c != str(cpu) or e != cpu]
    return checks, detail


def by_unit(runs, kinds):
    out = {}
    for r in runs:
        if r["status"] == "valid" and r["kind"] in kinds:
            out.setdefault(r["unit"], []).append(r)
    return out


def law_ratio(runs, protocol, arm):
    """Pooled probes per relation over law, one process per distinct seed (blocks then attempts resampled)."""
    seen = {}
    for r in runs:
        if r["status"] == "valid" and r["kind"] == "ic_rank" and r["arm"] == arm and r["role"] in ("primary", "aa"):
            seen.setdefault(r["seed"], r)
    if not seen:
        return None
    spec = protocol["online"]["bases"][protocol["arms"][arm]["base"]]
    law = int(protocol["online"]["subgroup_order"]) / (166 * spec["root_table_entries"])
    blocks = [list(r["rank_attempt_probes"]) for _, r in sorted(seen.items())]
    flat = [v for b in blocks for v in b]
    rng = random.Random(SEED + 90 + LAW_ARMS.index(arm))
    draws = []
    for _ in range(2000):
        pick = [blocks[rng.randrange(len(blocks))] for _ in blocks]
        sample = [b[rng.randrange(len(b))] for b in pick for _ in b]
        draws.append(statistics.mean(sample) / law)
    draws.sort()
    return {"estimate": statistics.mean(flat) / law, "ci95": [draws[50], draws[1949]], "attempts": len(flat),
            "blocks": len(blocks), "law_probes_per_relation": law, "mean_probes_per_relation": statistics.mean(flat)}


def pipeline_failures(ic_rows, protocol):
    """Serials of IC rows whose summary is missing or names another rank_probe_pipeline than the arm's
    (None on side A's binary, which emits no such field)."""
    return [r["serial"] for r in ic_rows if not r.get("summary_present") or
            r.get("rank_probe_pipeline") != protocol["arms"][r["arm"]].get("rank_probe_pipeline")]


def correctness(runs, protocol, receipt):
    checks, detail = {}, {}
    executed = [r for r in runs if r["status"] != "skipped_time_guard"]
    checks["all_executed_rows_valid"] = bool(executed) and all(r["status"] == "valid" for r in executed)
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
    for unit, rows in sorted(units.items()):
        scalars = {str(r["f"].get("recovered_scalar")) for r in rows}
        scalar_ok[unit] = len(scalars) == 1 and "None" not in scalars
        replay_ok[unit] = scalar_ok[unit] and replay(rows[0]["point"], next(iter(scalars)))
        per_base = {}
        for r in rows:
            if r["kind"] != "rho_tuned":
                per_base.setdefault(r["base"], []).append(r)
        rel_ok[unit] = all(len({json.dumps(r["f"].get("relation")) for r in b}) == 1 for b in per_base.values())
        probe_ok[unit] = all(len({r["f"].get("ops") for r in b}) == 1 and None not in {r["f"].get("ops") for r in b}
                             for b in per_base.values())
    checks["one_scalar_per_point_ic_and_rho"] = all(scalar_ok.values()) if scalar_ok else None
    checks["oracle_replay"] = all(replay_ok.values()) if replay_ok else None
    checks["one_relation_per_point_and_base"] = all(rel_ok.values()) if rel_ok else None
    checks["one_probe_count_per_point_and_base"] = all(probe_ok.values()) if probe_ok else None
    digest_keys = ("logical_states_blake3", "table_map_sum64", "table_map_xor64", "table_entries")
    layout_keys = ("stored_states_blake3", "table_slots_blake3")
    digest_sets, digest_ok = {}, {}
    for r in executed:
        if r["kind"] != "rho_tuned" and r["status"] == "valid":
            digest_sets.setdefault(r["base"], set()).add(json.dumps(r.get("index_digest"), sort_keys=True))
    for base, found in digest_sets.items():
        spec = protocol["online"]["bases"][base]
        want = dict({k: spec["index_digest"][k] for k in digest_keys},
                    **{k: spec["layout_digest"][k] for k in layout_keys})
        got = json.loads(next(iter(found))) if len(found) == 1 else None
        digest_ok[base] = got is not None and all(got.get(k) == v for k, v in want.items())
    checks["one_index_and_layout_digest_set_per_base_equal_frozen"] = (
        all(digest_ok.values()) and set(digest_ok) == {"K600", "M38", "M10"} if digest_ok else None)
    detail["index_digest_sets_per_base"] = {b: len(v) for b, v in digest_sets.items()}
    q0 = units.get("q0", [])
    if q0 and {r["arm"] for r in q0} == set(protocol["design"]["q0_arms"]):
        ok = True
        for r in q0:
            want = protocol["online"]["bases"][r["base"]]["q0_identity"]
            ok &= (r["f"].get("relation") == want["relation"] and str(r["f"].get("recovered_scalar")) == want["scalar"]
                   and r["f"].get("ops") == want["probes_folded"])
        checks["q0_matches_archived_and_frozen_identities"] = ok
    else:
        checks["q0_matches_archived_and_frozen_identities"] = None
    rank_rows = [r for r in executed if r["kind"] == "ic_rank"]
    ic_rows = [r for r in executed if r["kind"] in ("ic_cold", "ic_rank")]
    wrong_pipeline = pipeline_failures(ic_rows, protocol)
    checks["every_ic_row_ran_its_arms_rank_probe_pipeline"] = (not wrong_pipeline) if ic_rows else None
    detail["rows_on_another_rank_probe_pipeline"] = wrong_pipeline
    checks["rank_tables_equal_frozen_verified_tables"] = (
        all(r["status"] == "valid" and r["f"].get("logs_equal_archived") is True for r in rank_rows)
        if rank_rows else None)
    by_seed = {}
    for r in rank_rows:
        if r["status"] == "valid" and r["arm"] in SAME_TARGETS:
            by_seed.setdefault(r["seed"], []).append(r)
    seed_ok = {}
    for seed, rows in by_seed.items():
        digests = {r["f"].get("rank_relations_blake3") for r in rows}
        probes = {json.dumps(r["rank_attempt_probes"]) for r in rows}
        calls = {r["f"].get("rank_root_calls_total") for r in rows}
        counters = {json.dumps([(r["f"].get("rank_padd") or {}).get(key) for key in
                                ("fallback_states", "irregular_inputs", "resolved_hits", "swapped_pairs")])
                    for r in rows}
        seed_ok[seed] = (len(digests) == 1 and None not in digests and len(probes) == 1 and
                         len(calls) == 1 and None not in calls and len(counters) == 1 and
                         "null" not in next(iter(counters)) and
                         all(len(r["rank_attempt_probes"] or []) == len(r["rank_attempt_ns"] or []) for r in rows))
    checks["rank_relations_probes_root_calls_and_counters_identical_per_seed"] = (
        all(seed_ok.values()) if seed_ok else None)
    detail["processes_per_m38_seed"] = {str(s): len(v) for s, v in sorted(by_seed.items())}
    law = law_ratio(runs, protocol, GATED_LAW_ARM)
    band = protocol["online"]["bases"][protocol["arms"][GATED_LAW_ARM]["base"]]["law_band"]
    checks["primary_probe_law_inside_frozen_band"] = None if law is None else band[0] <= law["estimate"] <= band[1]
    detail.update({"units_seen": len(units),
                   "scalar_failures": sorted(u for u, v in scalar_ok.items() if not v),
                   "relation_failures": sorted(u for u, v in rel_ok.items() if not v),
                   "probe_failures": sorted(u for u, v in probe_ok.items() if not v),
                   "rank_seed_failures": sorted(s for s, v in seed_ok.items() if not v),
                   "probe_law_gate": law,
                   "rows_without_gain": {"%05d/%s" % (r["serial"], r["arm"]): r["f"].get("rank_rows_without_gain")
                                         for r in rank_rows if r["status"] == "valid"},
                   "rank_frame_counters": {"%05d/%s" % (r["serial"], r["arm"]): r["f"].get("rank_frame")
                                           for r in rank_rows if r["status"] == "valid"}})
    return checks, detail


# ---------------------------------------------------------------- statistics


def sides(runs, role):
    """{(unit, pair): {side: {"rank": row, "cold": row}}} over valid rows of a role."""
    out = {}
    for r in runs:
        if r["status"] == "valid" and r["role"] == role:
            out.setdefault((r["unit"], r["pair"]), {}).setdefault(r["side"], {})[
                "rank" if r["kind"] == "ic_rank" else "cold"] = r
    return out


def cpu_ms(row):
    return (row["row"].get("child_cpu_user_ms") or 0.0) + (row["row"].get("child_cpu_system_ms") or 0.0)


SIDE_VALUES = {
    "e2e": lambda s: s["rank"]["f"]["rank_stage_ms"] + s["cold"]["f"]["cold_ms"],
    "rank_stage": lambda s: s["rank"]["f"]["rank_stage_ms"],
    "cold": lambda s: s["cold"]["f"]["cold_ms"],
    "cpu_time": lambda s: cpu_ms(s["rank"]) + cpu_ms(s["cold"]),
    "process_wall": lambda s: s["rank"]["row"]["process_wall_ms"] + s["cold"]["row"]["process_wall_ms"],
    "setup": lambda s: s["cold"]["f"]["setup_ms"],
    "index_build": lambda s: s["cold"]["f"]["index_ms"],
    "scan_selftest": lambda s: s["cold"]["f"]["scan_selftest_ms"],
    "rank_process_index_build": lambda s: s["rank"]["f"]["index_ms"],
    "cold_minor_faults": lambda s: s["cold"]["row"]["child_minor_faults"],
    "online": lambda s: s["cold"]["f"]["online_ms"],
    "peak_rss": lambda s: s["cold"]["f"]["peak_rss_bytes"],
}


def complete_pairs(runs, role, a, b, k):
    """{unit: [(side a, side b, pair)]} for pairs with both sides complete."""
    out = {}
    for (unit, pair), s in sorted(sides(runs, role).items(), key=lambda kv: (kv[0][0], kv[0][1])):
        if all(x in s and {"rank", "cold"} <= set(s[x]) for x in (a, b)):
            out.setdefault(unit, []).append((s[a], s[b], pair))
    return out


def ratio_of_sums(points):
    return sum(x for pairs in points for x, _ in pairs) / sum(y for pairs in points for _, y in pairs)


def geo_mean(points):
    logs = [math.log(x / y) for pairs in points for x, y in pairs]
    return math.exp(statistics.mean(logs))


def two_stage(points, statistic, seed, draws=DRAWS):
    """points: [[(a, b), ...] per point]. Points, then pairs within each drawn point, with replacement."""
    if not points:
        return None
    rng = random.Random(seed)
    n = len(points)
    values = []
    for _ in range(draws):
        sample = []
        for _ in range(n):
            pairs = points[rng.randrange(n)]
            sample.append([pairs[rng.randrange(len(pairs))] for _ in pairs])
        values.append(statistic(sample))
    values.sort()
    return {"estimate": statistic(points), "ci95": [values[int(0.025 * draws)], values[int(0.975 * draws) - 1]],
            "n_points": n, "n_pairs": sum(len(p) for p in points),
            "bootstrap": "two-stage paired: points, then pairs within each drawn point; %d draws" % draws}


def paired_values(pairs_by_unit, key):
    fn = SIDE_VALUES[key]
    return [[(fn(a), fn(b)) for a, b, _ in pairs] for _, pairs in sorted(pairs_by_unit.items())]


def planted_ratio(runs, seed, key="rank_stage_ms"):
    """kM38RFX / kM38RF (the planted rank pairs) of a field; pairs resampled, X and B together."""
    groups = {}
    for r in runs:
        if r["status"] == "valid" and r["role"] == "planted":
            groups.setdefault(r["unit"], {})[r["arm"]] = r
    pairs = [(g[PLANTED_ARM]["f"][key], g[PLANTED_BASE_ARM]["f"][key]) for _, g in sorted(groups.items())
             if PLANTED_ARM in g and PLANTED_BASE_ARM in g]
    if not pairs:
        return None
    rng = random.Random(seed)

    def value(sample):
        return sum(x for x, _ in sample) / sum(y for _, y in sample)

    draws = sorted(value([pairs[rng.randrange(len(pairs))] for _ in pairs]) for _ in range(DRAWS))
    return {"estimate": value(pairs), "ci95": [draws[int(0.025 * DRAWS)], draws[int(0.975 * DRAWS) - 1]],
            "pairs": len(pairs), "field": key,
            "bootstrap": "planted pairs resampled with replacement, X and B of a pair together, %d draws" % DRAWS}


def statistics_block(runs, protocol):
    out = {}
    primary = complete_pairs(runs, "primary", "A", "B", protocol["design"]["primary_pairs_per_point"])
    aa = complete_pairs(runs, "aa", "B", "Baa", protocol["design"]["aa_pairs_per_point"])
    out["primary_pairs"] = sum(len(v) for v in primary.values())
    out["aa_pairs"] = sum(len(v) for v in aa.values())
    out["primary_e2e_paired_A_over_B"] = two_stage(paired_values(primary, "e2e"), ratio_of_sums, SEED)
    out["primary_e2e_geometric_mean_of_pair_ratios"] = two_stage(paired_values(primary, "e2e"), geo_mean, SEED + 1)
    for n, key in enumerate(("rank_stage", "cold", "cpu_time", "process_wall", "setup", "index_build", "online",
                             "peak_rss", "scan_selftest", "rank_process_index_build", "cold_minor_faults")):
        out["%s_A_over_B" % key] = two_stage(paired_values(primary, key), ratio_of_sums, SEED + 10 + n)
    out["aa_e2e_B_over_Baa"] = two_stage(paired_values(aa, "e2e"), ratio_of_sums, SEED + 2)
    out["aa_cold_B_over_Baa"] = two_stage(paired_values(aa, "cold"), ratio_of_sums, SEED + 3)
    out["aa_cpu_time_B_over_Baa"] = two_stage(paired_values(aa, "cpu_time"), ratio_of_sums, SEED + 4)
    out[PLANTED_KEY] = planted_ratio(runs, SEED + 5)
    out["planted_index_build_%s_over_%s" % (PLANTED_ARM, PLANTED_BASE_ARM)] = planted_ratio(runs, SEED + 6, "index_ms")
    out["rank_stage_secondary_A_over_B"] = out["rank_stage_A_over_B"]
    out["probe_law"] = {arm: law_ratio(runs, protocol, arm) for arm in LAW_ARMS}
    e2e = paired_values(primary, "e2e")
    out["per_pair"] = [{"unit": unit, "pair": p, "e2e_A_ms": SIDE_VALUES["e2e"](a), "e2e_B_ms": SIDE_VALUES["e2e"](b),
                        "ratio": SIDE_VALUES["e2e"](a) / SIDE_VALUES["e2e"](b), "first_side": (
                            "A" if a["rank"]["position"] < b["rank"]["position"] else "B")}
                       for unit, pairs in sorted(primary.items()) for a, b, p in pairs]
    out["per_point_ratio"] = {unit: ratio_of_sums([[(SIDE_VALUES["e2e"](a), SIDE_VALUES["e2e"](b))
                                                    for a, b, _ in pairs]]) for unit, pairs in sorted(primary.items())}
    for label in ("A", "B"):
        rows = [r for r in out["per_pair"] if r["first_side"] == label]
        out["ratio_when_%s_first" % label] = (sum(r["e2e_A_ms"] for r in rows) / sum(r["e2e_B_ms"] for r in rows)
                                              if rows else None)
    by_pos = {}
    for r in out["per_pair"]:
        by_pos.setdefault(r["pair"], []).append(r)
    out["ratio_by_pair_position"] = {str(p): sum(r["e2e_A_ms"] for r in rows) / sum(r["e2e_B_ms"] for r in rows)
                                     for p, rows in sorted(by_pos.items())}
    means = {}
    for label, fn in (("A", 0), ("B", 1)):
        flat = [pair[fn] for pairs in primary.values() for pair in pairs]
        if flat:
            means[label] = {key: statistics.mean(float(SIDE_VALUES[key](s)) for s in flat) for key in SIDE_VALUES}
    out["mean_per_side"] = means
    rank_out = {}
    for arm in SAME_TARGETS:
        rows = [r for r in runs if r["kind"] == "ic_rank" and r["arm"] == arm and r["status"] == "valid"]
        if rows:
            probes = sum(v for r in rows for v in r["rank_attempt_probes"] if v is not None)
            ns = sum(v for r in rows for v in r["rank_attempt_ns"])
            rank_out[arm] = {"processes": len(rows),
                             "mean_rank_stage_ms": statistics.mean(r["f"]["rank_stage_ms"] for r in rows),
                             "mean_attempt_ms": ns / 1e6 / sum(len(r["rank_attempt_ns"]) for r in rows),
                             "ns_per_probe": ns / probes if probes else None}
    out["rank_stage"] = rank_out
    rho = [r["f"] for r in runs if r["status"] == "valid" and r["kind"] == "rho_tuned"]
    if rho and means:
        steps = sum(float(r["ops"]) for r in rho)
        ms_per_step = sum(r["online_ms"] for r in rho) / steps
        unit = ms_per_step * protocol["online"]["sqrt_r"]
        out["rho_ms_per_step"] = ms_per_step
        out["rho_mean_cold_ms"] = statistics.mean(r["rho_cold_ms"] for r in rho)
        out["rho_mean_online_ms"] = statistics.mean(r["online_ms"] for r in rho)
        out["S_rho_cold"] = out["rho_mean_cold_ms"] / unit
        out["S_e2e_cold"] = {label: m["e2e"] / unit for label, m in means.items()}
        out["S_online"] = {label: m["online"] / unit for label, m in means.items()}
        if len(out["S_e2e_cold"]) == 2:
            out["delta_S_e2e_cold_A_to_B"] = out["S_e2e_cold"]["B"] - out["S_e2e_cold"]["A"]
        out["e2e_cold_gap_over_rT"] = {label: m["e2e"] / out["rho_mean_cold_ms"] for label, m in means.items()}
    return out


def decide(checks, stats):
    # Fail closed: every required gate must be present and exactly True; a missing or unknown gate is a failure.
    gates_ok = all(checks.get(key) is True for key in REQUIRED_CHECKS) and all(v is True for v in checks.values())
    aa_e2e, aa_cold = stats.get("aa_e2e_B_over_Baa"), stats.get("aa_cold_B_over_Baa")
    planted = stats.get(PLANTED_KEY)
    primary = stats.get("primary_e2e_paired_A_over_B")
    controls = {"aa_e2e_inside_0.97_1.03": aa_e2e is not None and AA_BAND[0] <= aa_e2e["estimate"] <= AA_BAND[1],
                "aa_cold_inside_0.97_1.03": aa_cold is not None and AA_BAND[0] <= aa_cold["estimate"] <= AA_BAND[1],
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
    n = e.get("n_pairs", e.get("attempts", e.get("pairs")))
    return "%.4f [%.4f, %.4f] (n=%s)" % (e["estimate"], e["ci95"][0], e["ci95"][1], n)


def table(result):
    s = result["statistics"]
    lines = ["# n=83 rank finder (paired, repeated alternating pairs): frozen result", "",
             "Verdict: **%s**" % result["decision"], "", "| statistic | estimate [95%] |", "| --- | --- |"]
    for key in ("primary_e2e_paired_A_over_B", "primary_e2e_geometric_mean_of_pair_ratios",
                "rank_stage_secondary_A_over_B", "cold_A_over_B", "cpu_time_A_over_B", "process_wall_A_over_B",
                "setup_A_over_B", "index_build_A_over_B", "scan_selftest_A_over_B", "rank_process_index_build_A_over_B",
                "online_A_over_B", "peak_rss_A_over_B", "cold_minor_faults_A_over_B", "aa_e2e_B_over_Baa",
                "aa_cold_B_over_Baa", "aa_cpu_time_B_over_Baa", PLANTED_KEY,
                "planted_index_build_%s_over_%s" % (PLANTED_ARM, PLANTED_BASE_ARM)):
        lines.append("| %s | %s |" % (key, fmt(s.get(key))))
    for arm, law in (s.get("probe_law") or {}).items():
        lines.append("| probe law %s (mean probes per relation / law) | %s |" % (arm, fmt(law)))
    lines += ["", "Mean per side (ms; A = kM38IC+cM38IC, B = kM38RF+cM38RF): " + json.dumps(s.get("mean_per_side")),
              "", "Per-point ratio: " + json.dumps(s.get("per_point_ratio")),
              "", "Ratio by pair position: " + json.dumps(s.get("ratio_by_pair_position")),
              "", "Ratio when A first / B first: %s / %s" % (s.get("ratio_when_A_first"), s.get("ratio_when_B_first")),
              "", "Rank stage: " + json.dumps(s.get("rank_stage")),
              "", "S end-to-end cold: " + json.dumps(s.get("S_e2e_cold")),
              "", "E2E cold gap over rT: " + json.dumps(s.get("e2e_cold_gap_over_rT")),
              "", "Checks: " + json.dumps(result["checks"]), "", "Controls: " + json.dumps(result["controls"])]
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("receipt", type=Path)
    parser.add_argument("--correctness-only", action="store_true")
    args = parser.parse_args()
    protocol = json.loads((HERE / "protocol.json").read_text())
    schedule = json.loads((HERE / "schedule.json").read_text())
    runs, problems, missing, in_order = load(args.receipt, schedule, protocol, args.correctness_only)
    checks, detail = correctness(runs, protocol, args.receipt)
    runner, runner_detail = runner_checks(args.receipt, runs, args.correctness_only)
    checks.update(runner)
    detail["runner"] = runner_detail
    checks["receipt_matches_schedule"] = not problems
    checks["rows_in_schedule_order"] = in_order
    if args.correctness_only:
        out = {"checks": checks, "detail": detail, "problems": problems, "rows": len(runs)}
        (args.receipt / "correctness.json").write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
        print(json.dumps({"checks": checks, "problems": problems, "rows": len(runs)}, sort_keys=True))
        return
    stats = statistics_block(runs, protocol)
    design = protocol["design"]
    checks["every_scheduled_row_present"] = not missing and not any(r["status"] == "skipped_time_guard" for r in runs)
    checks["all_primary_pairs_complete"] = stats["primary_pairs"] == design["points"] * design["primary_pairs_per_point"]
    checks["all_aa_pairs_complete"] = stats["aa_pairs"] == design["points"] * design["aa_pairs_per_point"]
    planted = stats.get(PLANTED_KEY)
    checks["all_planted_pairs_complete"] = planted is not None and \
        planted["pairs"] == design["points"] * design["planted_pairs_per_point"]
    decision, controls = decide(checks, stats)
    result = {"kind": protocol["kind"], "decision": decision, "checks": checks, "controls": controls,
              "detail": detail, "problems": problems,
              "skipped_time_guard": sum(1 for r in runs if r["status"] == "skipped_time_guard"),
              "contention_flags": [{"serial": r["serial"], "arm": r["arm"], "flags": r["contention"]}
                                   for r in runs if r.get("contention")],
              "statistics": stats}
    (args.receipt / "result.json").write_text(json.dumps(result, indent=1, sort_keys=True) + "\n")
    (args.receipt / "result_table.md").write_text(table(result))
    print(json.dumps({"decision": decision, "primary": stats.get("primary_e2e_paired_A_over_B"),
                      "controls": controls, "checks": checks}, sort_keys=True))


if __name__ == "__main__":
    main()
