#!/usr/bin/env python3
"""Write the frozen protocol (`protocol.json`) of the n=83 K'=4 / 400-orbit experiment.

Run once, before any timing, after `restore.py --no-pin-check` (the field-ops
producer's own pins, headers M38 and D4, the D4 table), `local_identity.py`,
`make_local_profile.py`, `make_targets.py`, `check_panel_disjoint.py`,
`check_seed_disjoint.py`, `make_power_prior.py` and `power_check.py`.
`restore.py` re-checks every digest this file records.

The question and the owner ruling are in the text below. The producer is the
field-ops experiment's (`koblitz-n83-fieldops-20261104`, on main, run
41869146827, binary `ic_online_fieldops_r770`), the SAME binary on both sides:
side A is the current n=83 row (M38 header, K' = 16, 608 orbits; arms kM38FO,
cM38FO verbatim from the field-ops protocol), side B is the D4 header (K' = 4,
400 orbits; arms kD4FO, cD4FO). Only the base differs between the sides.
"""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIELDOPS = HERE.parent / "koblitz-n83-fieldops-20261104"
POINTS = 20
K = 3            # alternating primary pairs per point
K_AA = 2         # alternating A/A pairs per point
K_PLANTED = 1    # alternating planted pairs per point
SEED0 = 2500     # rank seed of pair j at point i: SEED0 + 3 i + j (2501 .. 2560); 2301-2360 collided, see README
ORDER_SEED0 = 2026110780
RHO_SEED_BASE = 1080000
DRAWS = 10000
BOOT_SEED = 20261080
DEADLINE_MIN = 165
BINARY = "ic_online_fieldops_r770"
PIPELINE = "fmul_clmul_inline+sqr_clmul_inline+state_square_clmul+maps_le_bytes+selftest_round_tables"
FIELDOPS_PROTOCOL_SHA256_FILE = "protocol.json"
OWNER_RULING = ("Owner ruling, 2026-11-07, given in chat: a closure base with K' >= 4 unknown-log columns counts "
                "as an index-calculus row. K' = 0 stays a known-log reference row.")


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    import restore  # noqa: E402  (this directory)

    fo = json.loads((FIELDOPS / "protocol.json").read_text())
    if sha256(FIELDOPS / "protocol.json") != restore.FIELDOPS_PROTOCOL_SHA256:
        raise SystemExit("the field-ops protocol differs from its pinned digest")
    power = json.loads((HERE / "analysis" / "power.json").read_text())
    ident = json.loads((HERE / "inputs" / "local_identity.json").read_text())
    profile = json.loads((HERE / "inputs" / "local_profile.json").read_text())
    targets = json.loads((HERE / "inputs" / "cold_targets.json").read_text())
    disjoint = json.loads((HERE / "inputs" / "panel_disjointness.json").read_text())
    seeds_new = json.loads((HERE / "inputs" / "seed_disjointness.json").read_text())
    if not ident["all_pass"]:
        raise SystemExit("the local identity test did not pass")
    if disjoint.get("disjoint") is not True or seeds_new.get("new") is not True:
        raise SystemExit("the panel or the rank seeds are not new on n=83")
    if not seeds_new["positive_control"]["finds_parent_schedule"]:
        raise SystemExit("the seed scan's positive control failed")
    if len(targets["points"]) != POINTS:
        raise SystemExit("panel size differs from the design")
    pd = power["design"]
    if (pd["points"], pd["primary_pairs_per_point"], pd["aa_pairs_per_point"], pd["planted_pairs_per_point"]) != \
            (POINTS, K, K_AA, K_PLANTED):
        raise SystemExit("power.json was computed for another design")

    def first(base, kind, canon="lift"):
        return next(r for r in ident["runs"] if r["base"] == base and r["kind"] == kind and r["index_canon"] == canon)

    # ---- bases
    m38 = dict(fo["online"]["bases"]["M38"])
    m38_run = first("M38", "cold")
    m38.update({"orbits_per_column": m38_run["closure"]["orbits_per_column"],
                "closure_multipliers_sha256": m38_run["closure_multipliers_sha256"],
                "log_table_input_blake3": m38_run["log_table_input_blake3"],
                "k_prime": m38["orbit_columns"],
                "parent_source": ("koblitz-n83-fieldops-20261104 protocol.json online.bases.M38 (sha256 %s), every "
                                  "field verbatim; four fields added from the local identity run (inputs/local_identity.json)"
                                  % restore.FIELDOPS_PROTOCOL_SHA256)})
    d4_run = first("D4", "cold")
    d4_header = HERE / "snapshots" / "closure" / "base_n83_closure_D4.jsonl"
    d4_table = HERE / "inputs" / "factor_logs_n83_closure_D4.json"
    verify = json.loads((HERE / "inputs" / "local_verify_closure_D4.json").read_text())
    if verify["status"] != "PASS" or verify["base_hash"] != d4_run["base_hash"]:
        raise SystemExit("the D4 closure verification is missing, failed or is for another base")
    law = int(fo["online"]["subgroup_order"]) / (166 * d4_run["root_table_entries"])
    d4 = {
        "base_hash": d4_run["base_hash"],
        "builder": "make_closure_base.py --columns 4 --norm 165 (the field-ops experiment's builder, unchanged, "
                   "from B's K600 header, in restore.py)",
        "factor_base_points": d4_run["factor_base_points"],
        "factor_log_table": "inputs/factor_logs_n83_closure_D4.json",
        "factor_log_table_check": ("verify_closure.py --base --table --planted (pinned oracle): every orbit, member "
                                   "and label of the base, [L_c]G = R_c for every column, [w L_c]G = P for every orbit; "
                                   "the table is the first four logs of the M38 table (make_log_table.py), also "
                                   "reproduced log for log by every rank process"),
        "factor_log_table_sha256": sha256(d4_table),
        "header_sha256": sha256(d4_header),
        "index_digest": {"accounting": "after the last target; outside setup and every online interval",
                         "logical_states": d4_run["regular_states"],
                         **{k: d4_run["index_digest"][k] for k in ("logical_states_blake3", "table_map_sum64",
                                                                  "table_map_xor64", "table_entries")},
                         "source": "inputs/local_identity.json: identical over 5 local processes (cold lift, cold "
                                   "lift_plant, rank seeds 301-303); a function of the orbit representatives only"},
        "index_orbits": d4_run["index_orbits"],
        "k_prime": d4_run["orbit_columns"],
        "law_band": [0.8, 1.2],
        "law_probes_per_relation": law,
        "layout_digest": {"source": "inputs/local_identity.json: the same five processes (KIC_INDEX_CANON = lift and "
                                    "lift_plant: every index key re-checked against lift_scan and the selected "
                                    "canonicalizer, 2 x stored states checks)",
                          "stored_states_blake3": d4_run["index_digest"]["stored_states_blake3"],
                          "table_slots_blake3": d4_run["index_digest"]["table_slots_blake3"]},
        "logs_equal_B_first_columns": True,
        "norm_cap": d4_run["closure"]["norm_cap"],
        "orbit_columns": d4_run["orbit_columns"],
        "orbits_per_column": d4_run["closure"]["orbits_per_column"],
        "closure_multipliers_sha256": d4_run["closure_multipliers_sha256"],
        "log_table_input_blake3": d4_run["log_table_input_blake3"],
        "path": "snapshots/closure/base_n83_closure_D4.jsonl",
        "q0_identity": {"probes_folded": d4_run["probes_folded"], "relation": d4_run["relation"],
                        "scalar": d4_run["recovered_scalar"],
                        "source": "inputs/local_identity.json (cold lift and lift_plant, rank seeds 301-303: identical "
                                  "relation; the scalar replays [d]G = Q in the pinned oracle in the run)"},
        "regular_states": d4_run["regular_states"],
        "role": ("Z[tau]-multiplier closure D4: 4 columns x 100 orbits (alpha = a + b tau, a odd > 0, "
                 "a^2 + ab + 2b^2 <= 165); column c's orbits are alpha(R_c) for B's R_c"),
        "root_table_entries": d4_run["root_table_entries"],
        "root_table_slots": d4_run["root_table_slots"],
        "source": "this experiment (make_closure_base.py --columns 4 --norm 165)",
        "stored_states_folded": d4_run["stored_states"],
    }
    if not (d4["orbits_per_column"] == 100 and d4["index_orbits"] == 400 and d4["orbit_columns"] == 4):
        raise SystemExit("D4 is not 4 columns x 100 orbits")

    # ---- arms
    arms = {}
    for name in ("kM38FO", "cM38FO", "rT"):
        arms[name] = dict(fo["arms"][name])
        arms[name]["parent_source"] = "the field-ops protocol's arm %s, verbatim" % name

    def d4_arm(src, role, **override):
        arm = dict(fo["arms"][src], base="D4", role=role)
        for key in ("parent_source", "derived_from"):
            arm.pop(key, None)
        arm.update(override)
        arm["derived_from"] = "the field-ops arm %s on base D4 (same binary %s)" % (src, BINARY)
        return arm

    arms["kD4FO"] = d4_arm("kM38FO", "PRIMARY candidate rank stage: kM38FO's configuration on the D4 base")
    arms["cD4FO"] = d4_arm("cM38FO", "PRIMARY candidate cold: cM38FO's configuration on the D4 base")
    arms["kD4FOaa"] = dict(arms["kD4FO"], role="A/A copy of kD4FO")
    arms["cD4FOaa"] = dict(arms["cD4FO"], role="A/A copy of cD4FO")
    arms["cD4FOX"] = d4_arm("cM38FO", ("PLANTED timing and exactness control: cD4FO with KIC_INDEX_CANON=lift_plant: "
                                       "every index key is also checked against lift_scan and the selected "
                                       "canonicalizer (2 x stored states checks); same layout digests, slower index "
                                       "build"), index_canon="lift_plant")
    assert all(a["binary"] == BINARY for n, a in arms.items() if n != "rT")
    rank_seeds = {"s%03d" % i: [SEED0 + 3 * i + j for j in range(1, K + 1)] for i in range(POINTS)}
    p = {
        "schema": 1,
        "kind": "n83-k4c400-paired-e2e-tier1",
        "frozen_before_any_timing": True,
        "draft_not_frozen": False,
        "frozen_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "owner_ruling": {"date": "2026-11-07", "verbatim_in_chat": OWNER_RULING,
                         "consequence": ("D4 (K' = 4) is an index-calculus row. A K' = 0 base would be a known-log "
                                         "reference row (`koblitz-n83-knownlog-20261019`, BASELINES.md: ruling "
                                         "pending for that row), and is not measured here"),
                         "recorded_in": ["this protocol", "README.md", "docs/ic/BASELINES.md (next to the known-log "
                                                                        "ruling-pending note)"]},
        "question": ("Is the END-TO-END cold cost (setup + index build + rank stage + linear algebra + one-target "
                     "online) of the D4 closure base (K' = 4 unknown-log columns, 400 orbits: "
                     "make_closure_base.py --columns 4 --norm 165) lower than the current n=83 row's M38 base "
                     "(K' = 16, 608 orbits), with the SAME frozen merged producer binary on both sides "
                     "(ic_online_fieldops_r770, koblitz-n83-fieldops-20261104), on new held-out points and new rank "
                     "seeds? Two levers move together (algo_levers.md 1 and 2): K' falls 16 -> 4, so the rank stage "
                     "needs 4 relations instead of 16, and the orbit count falls 608 -> 400, so the stored states "
                     "(83 K_orb^2 / 2) fall 2.31x; the logical states (13.28 M) fall under 2^24, which steps the "
                     "Feistel self-test domain down from 2^26 to 2^24. The price is a smaller table (E 12.6 M "
                     "against 30.4 M entries), so the probe law r / (166 E) rises 2.41x per relation and per "
                     "target. The producer, every environment variable, the pipeline and the point panel are the "
                     "same; only the base header and its factor-log table differ. Repeated alternating pairs and a "
                     "95% two-stage paired bootstrap lower bound above 1 decide (AGENTS.md, 'CPU performance "
                     "isolation gate', Tier 1)."),
        "why_this_run": ("The local prototype (inputs/local_profile.json, inputs/local_prototype_rows.jsonl; a loaded "
                         "shared VM; 10 rank seeds per arm, no interval) measured a 1.85x end-to-end speed-up of "
                         "this header over M38 (mean process totals %.0f vs %.0f ms). It is a diagnostic: one "
                         "online target per cold run is a single exponential sample, the rank stage is heavy-tailed "
                         "(sd %.0f ms on D4), and nothing was matched to rho. This run is the Tier 1 measurement." % (
                             profile["arms"]["d_K4_400"]["rank_process_total_ms_mean"],
                             profile["arms"]["M38"]["rank_process_total_ms_mean"],
                             profile["arms"]["d_K4_400"]["rank_process_total_ms_sd"])),
        "success_criterion": "AGENTS.md 'Success criterion: iterative improvement of the index-calculus baseline'",
        "tier_rule": fo["tier_rule"],
        "baseline_row": {"experiment": "koblitz-n83-fieldops-20261104", "landed": "on main",
                         "run": "https://github.com/isogeny-labs/cryptanalysis/actions/runs/41869146827",
                         "binary": BINARY, "base": "M38",
                         "primary": "1.2610 [1.2541, 1.2681] over the rank-finder row (side A of that run)",
                         "fieldops_protocol_sha256": restore.FIELDOPS_PROTOCOL_SHA256,
                         "ratchet_rule": ("if another PR replaces the n=83 row before this one lands, this result is "
                                          "recorded as a measurement against the row it measured (M38 on the "
                                          "field-ops producer), and a combined run follows")},
        "template": {"experiment": "koblitz-n83-fieldops-20261104", "landed": "on main",
                     "copied_verbatim": sorted(restore.VERBATIM_FROM_FIELDOPS)},
        "sources": {
            "producer": ("the field-ops producer of koblitz-n83-fieldops-20261104, derived and pinned by ITS "
                         "restore.py (every pin of its protocol.json), built from its online-b/ crate with -C "
                         "target-feature=+pclmulqdq; this experiment builds and runs that crate unchanged"),
            "fieldops_protocol_sha256": restore.FIELDOPS_PROTOCOL_SHA256,
            "fieldops_source_sha256": fo["sources"]["fieldops_source_sha256"],
            "online_b_manifest_sha256": sha256(FIELDOPS / "online-b" / "Cargo.toml"),
            "online_b_lock_sha256": sha256(FIELDOPS / "online-b" / "Cargo.lock"),
            "online_b_cargo_config_sha256": sha256(FIELDOPS / "online-b" / ".cargo" / "config.toml"),
            "online_manifest_sha256": sha256(FIELDOPS / "online" / "Cargo.toml"),
            "online_lock_sha256": sha256(FIELDOPS / "online" / "Cargo.lock"),
            "crypto_770f6a69": fo["sources"]["crypto_770f6a69"],
            "field_ops_pipeline": PIPELINE,
            "rank_probe_pipeline": fo["sources"]["rank_probe_pipeline"],
            "index_build_pipeline": fo["sources"]["index_build_pipeline"],
            "closure_headers_sha256": {"M38": m38["header_sha256"], "D4": d4["header_sha256"]},
            "builds": {"both_sides": ("the field-ops experiment's online-b/ crate, one binary %s, built once with "
                                      "-C target-feature=+pclmulqdq; the tuned rho rho_tuned_r770 from the field-ops "
                                      "online/ crate" % BINARY)},
            "fieldops_files_pinned": {key: sha256(path) for key, path in restore.fieldops_files().items()},
            "local_sha256": {key: sha256(path) for key, path in restore.local_files().items()},
        },
        "online": {
            "bases": {"M38": m38, "D4": d4},
            "curve_id": fo["online"]["curve_id"],
            "subgroup_order": fo["online"]["subgroup_order"],
            "lambda": fo["online"]["lambda"],
            "sqrt_r": fo["online"]["sqrt_r"],
            "tuned_rho_config": "../koblitz-n83-fieldops-20261104/" + fo["online"]["tuned_rho_config"],
            "cold_targets_file": ("inputs/cold_targets.json (role %s, %d points), disjoint from Q0, B's panel and "
                                  "every earlier n=83 panel including the field-ops and field-ops-2 panels "
                                  "(make_targets.py EARLIER_ROLES; role-agnostic x/y scan in "
                                  "inputs/panel_disjointness.json, 0 hits)" % (targets["role"], POINTS)),
            "cold_interval": fo["online"]["cold_interval"],
            "rank_interval": fo["online"]["rank_interval"],
            "online_interval": fo["online"]["online_interval"],
            "base_construction": ("M38: restored by the field-ops restore.py (frozen SHA-256); D4: "
                                  "make_closure_base.py --columns 4 --norm 165, regenerated by restore.py to its "
                                  "frozen SHA-256, verified by verify_closure.py before timing"),
        },
        "arms": arms,
        "design": {
            "points": POINTS, "primary_pairs_per_point": K, "aa_pairs_per_point": K_AA,
            "planted_pairs_per_point": K_PLANTED,
            "sides": {"A": ["kM38FO", "cM38FO"], "B": ["kD4FO", "cD4FO"], "Baa": ["kD4FOaa", "cD4FOaa"]},
            "planted_arms": ["cD4FO", "cD4FOX"],
            "side_rule": fo["design"]["side_rule"],
            "pair_rule": ("a primary pair is one A side and one B side with the same point and the same rank seed "
                          "(the seed is the rank process's RNG seed on each base; the two bases give different "
                          "rank work, so the pair shares a point and a seed, not a draw). Each point's K pairs run "
                          "as 2K sides in strict alternation, ABAB... or BABA..., the starting side drawn from "
                          "random.Random(ORDER_SEED0 + i)"),
            "rank_stage_design": ("each side runs its own rank process on its own base: kM38FO needs 16 attempts "
                                  "(16 unknown-log columns), kD4FO needs 4. The rank work is therefore NOT the same "
                                  "in the two sides; it is the quantity under test. Within a base it is the same "
                                  "(gated: identical relation digests, probe vectors, root calls and counters per "
                                  "seed across kD4FO and kD4FOaa)"),
            "aa_rule": ("the A/A pairs compare B with Baa: kD4FO / cD4FO against kD4FOaa / cD4FOaa, the same arm "
                        "twice, alternating, same point and seed"),
            "planted_rule": ("a planted pair is cD4FO and cD4FOX, cold processes only, alternating, with the start "
                             "drawn from the same generator"),
            "rho_rule": fo["design"]["rho_rule"],
            "segment_rule": ("O1: Q0 on cM38FO and cD4FO, shuffled by random.Random(ORDER_SEED0 + 99). Then one "
                             "segment P<i> per point i = 1..POINTS in panel order. Its four sub-blocks (primary, aa, "
                             "planted, rho) run in an order shuffled by the point's generator"),
            "order_seed0": ORDER_SEED0,
            "rank_seed0": SEED0,
            "rank_seeds": rank_seeds,
            "rank_seeds_note": ("2501-2560 are new on n=83 (inputs/seed_disjointness.json; the positive control "
                                "finds the field-ops schedule's 2101-2136). The first choice, 2301-2360, collided with "
                                "koblitz-n83-onlineframe2-20261021/schedule.json and was replaced. %d distinct rank seeds give %d D4 "
                                "attempts (4 per seed) for the probe-law gate and %d attempts on M38"
                                % (POINTS * K, POINTS * K * 4, POINTS * K * 16)),
            "rho_seed_base": RHO_SEED_BASE,
            "q0_point": fo["design"]["q0_point"],
            "q0_arms": ["cM38FO", "cD4FO"],
            "process_model": "one point per process, fresh process per run, one pinned CPU, one runner",
            "segment_upper_estimate_s": {"O": 100, "P": 450},
            "timeout_s": fo["design"]["timeout_s"],
            "time_guard": ("before each segment: skip it (rows skipped_time_guard) if the elapsed job time plus the "
                           "larger of its upper estimate and 1.1x the longest segment of its panel so far exceeds "
                           "%d min. A skipped row makes the run invalid" % DEADLINE_MIN),
            "deadline_min": DEADLINE_MIN,
            "runtime_estimate": ("power.json runtime: about %.0f min for the job (%.0f min schedule), about %.0f min "
                                 "on a 1.5x slower host; time guard %d min, job limit %d min" % (
                                     power["runtime"]["job_total_min"], power["runtime"]["schedule_min"],
                                     power["runtime"]["job_total_min_on_a_1.5x_slower_host"], DEADLINE_MIN,
                                     power["runtime"]["job_limit_min"])),
        },
        "gates": [
            "every scheduled row present and valid (exit 0, verified, schedule match, no memory event), no time-guard skip",
            ("receipt integrity (verify_receipt.py, fail closed): every executed row's raw producer record decodes, "
             "its SHA-256 equals the wrapper summary's raw_result_sha256, and its arm, kind, panel, point and seed "
             "equal the frozen schedule's; serial, arm, point, seed, segment, command line and stdout file equal the "
             "schedule's; rows ran in schedule order; runner_start.json records this protocol's, this schedule's, "
             "arm.py's and run_schedule.py's SHA-256 and no smoke subset; every row ran its ARM's binary (by name "
             "and by the digest runner_start.json lists), unchanged at the end. An unknown gate is a failure"),
            ("every IC row's summary names its arm's rank_probe_pipeline and field_ops_pipeline (%s on every IC arm: "
             "the same binary on both sides)" % PIPELINE),
            "placement: every process's Cpus_allowed_list, read from /proc while it ran, is the one execution CPU",
            "host identity: the CPU record at the start and the end of the schedule has the same model, microcode and flags",
            ("before any timing: check_log_table.py: M38's table and header re-verified and D4's header and table "
             "pass verify_closure.py --base --table --planted in the pinned oracle (three planted corruptions "
             "rejected on each), both SHA-256 pinned; the field-ops crates' tests pass"),
            ("every IC process (arm.py): KIC_INDEX_CANON as the arm (lift; lift_plant in cD4FOX only); index roots "
             "checked 0 times, or 2 x stored states in cD4FOX; the full scan self-test; the arm's "
             "index_build_pipeline and field_ops_pipeline; ITS base's frozen base hash, columns, orbits, orbits per "
             "column, multiplier list, states, slots, root entries, logical-state and table-map digests; its "
             "base's frozen LAYOUT digests (stored_states_blake3, table_slots_blake3); cold: the frozen cached "
             "table's input digest; rank: the arm's rank_solve, K' relations, one frame per attempt"),
            "per point: one scalar across every IC process (both bases, cold and rank) and rT, replayed as [d]G = Q in the pinned oracle",
            "per point and base: one relation and one probe count across every IC process of that base",
            "per base (M38 and D4): one index and layout digest set across every process, equal to the frozen one",
            "Q0 (O1): cM38FO gives M38's frozen identity (1,612,533 probes), cD4FO gives D4's frozen identity (inputs/local_identity.json)",
            "rank arms: full rank (K' relations), 0 failed attempts, 0 rows without gain, one frame per attempt, and the written factor-log table equal to the base's frozen verified table, log for log",
            "per D4 rank seed: rank_relations_blake3, per-attempt probe vector, root calls and point-addition counters identical across every kD4FO and kD4FOaa process with that seed",
            ("probe law (both arms gated): pooled probes per relation of kD4FO over its %d distinct seeds (%d attempts) "
             "over r / (166 E_D4), and of kM38FO over its %d seeds (%d attempts) over r / (166 E_M38), each inside "
             "[0.80, 1.20]; each over at least 64 attempts" % (POINTS * K, POINTS * K * 4, POINTS * K, POINTS * K * 16)),
        ],
        "statistics": {
            "e2e_per_side": fo["statistics"]["e2e_per_side"],
            "primary": ("R = sum over the %d primary pairs of E2E(A) / sum over the same pairs of E2E(B). 95%% "
                        "percentile interval from a two-stage paired bootstrap, %d draws, random.Random(%d): the "
                        "points drawn with replacement, then each drawn point's pairs drawn with replacement; A and "
                        "B of a pair are always drawn together" % (POINTS * K, DRAWS, BOOT_SEED)),
            "primary_is": "the paired END-TO-END ratio of the M38 row over D4; every stage ratio is co-reported and never decides",
            "stage_secondary": ("four STAGE ratios, each labelled a stage secondary and never deciding, in the "
                                "primary pairs with the same bootstrap: index build (timing_ms.index_build of the cold "
                                "process) cM38FO / cD4FO, scan self-test (scan_order_selftest.ms of the cold process) "
                                "cM38FO / cD4FO, rank stage (timing_ms.rank_stage) kM38FO / kD4FO, and online "
                                "(online_ms of the cold process) cM38FO / cD4FO"),
            "pairing_basis": fo["statistics"]["pairing_basis"],
            "secondary": [
                "geometric mean of the per-pair ratios E2E(A)/E2E(B), with the same bootstrap",
                "index build, scan self-test, rank stage and online (stage secondaries, labelled), paired",
                "cold, setup cM38FO / cD4FO, paired",
                "index build in the rank processes kM38FO / kD4FO, paired",
                "E2E process CPU time and process wall A / B, with the same bootstrap",
                "peak RSS and minor faults of the cold processes",
                "per-point ratio, and the ratio by pair position and by side order",
                "observed coefficient of variation of the rank stage, online and E2E per side (to compare with power.json)",
                "probe law of kM38FO and kD4FO; rank ns per probe; rho ms/step from rT; S per side; E2E cold gap over rT",
                "section 5a band: band_model.py (see `section_5a`)",
            ],
        },
        "section_5a": {
            "rule": ("AGENTS.md section 5a: every arm's unpriced native work, the matched rho's included, is priced at "
                     "0, 0.1 and 1 GAE per operation, and two arms are ranked only where the order holds across the "
                     "band (band.py of koblitz-n83-opcounts-20261023, run unchanged)"),
            "what_is_counted": ("rho: counted in this run (rT's own charges_setup_and_solve in every rT process). "
                                "IC: the field-ops producer emits no operation counts, so the IC units are a MODEL: "
                                "the archived counted run 39882571652's per-kind counts (stacked producer, "
                                "experiments/koblitz-n83-opcounts-20261023, analysis_v2/counts-v2.json) taken per "
                                "root-index probe (probe-proportional kinds) and per relation attempt (the rest), "
                                "applied to THIS run's measured probes and attempts per side and pair, and to each "
                                "base's exact stored states for root-index inserts. It is a derived band, labelled "
                                "model, not a counted run of this producer"),
            "script": "band_model.py", "reported": ["gap to rT at w = 0, 0.1, 1 for A (M38) and B (D4)",
                                                     "A vs B order across the band", "crossover weights"],
            "limit": ("factor-base construction and the linear algebra are not charged; the intervals carry no "
                      "model uncertainty; rho's scalar multiplications stay a bound (0 to 2 (r_bits - 1) GAE)")},
        "controls_pass_rule": {
            "aa": ("over the %d A/A pairs (B against Baa): the COLD ratio of sums cD4FO / cD4FOaa point estimate "
                   "inside [0.97, 1.03], and the END-TO-END ratio's 95%% two-stage interval contains 1. The field-ops "
                   "template required the end-to-end POINT estimate inside [0.97, 1.03]; with independent rank and "
                   "online draws on D4 that fails a true null about half the time (power.json: "
                   "e2e_point_inside_0.97_1.03_rate), so the end-to-end rule is the interval" % (POINTS * K_AA)),
            "planted": ("index build cD4FOX / cD4FO over the %d planted pairs, 95%% bootstrap lower bound (pairs "
                        "resampled, 10,000 draws) above 1; every cD4FOX must also reproduce the frozen layout "
                        "digests and check 2 x stored states roots" % (POINTS * K_PLANTED)),
            "planted_exactness": ("the three planted corruptions rejected by verify_closure.py on both closure bases "
                                  "before timing, and the crate tests passing"),
            "otherwise": "verdict invalid",
        },
        "decision_rule": {
            "improvement": ("R lower bound > 1: a qualified Tier 1 end-to-end speedup of the D4 base over the M38 row "
                            "with the same producer. It replaces the n=83 row only if every gate and control passes"),
            "regression": "R upper bound < 1",
            "not_separated": "otherwise",
            "invalid": "any gate or control fails or is unknown, or any scheduled row is missing (time-guard skips included)",
        },
        "multiplicity": "one primary statistic; every secondary is descriptive and never changes the verdict",
        "exactness_argument": {
            "producer": fo["exactness_argument"]["fieldops"],
            "bases": ("D4 is another input to the same producer: its orbit representatives, labels and table are "
                      "checked by the pinned oracle (verify_closure.py), its index and layout digests are frozen from "
                      "a local run and reproduced by every process of this run, every rank process reproduces the "
                      "frozen table, and every recovered scalar replays [d]G = Q in the oracle. Within-column "
                      "algebraic coincidences remove 4.98% of D4's logical keys (E = 12,618,968 of 13,280,000): "
                      "that is a property of the base, in E and in the probe law"),
        },
        "evidence_change": ("none: both sides run the full scan self-test over their own domain (D4's is 2^24, M38's "
                            "2^26: the domain is the smallest even power of two covering the base's logical states, "
                            "the producer's own rule, not a sampled or shortened check), build, check and digest "
                            "their own index, and the rank stage runs to full rank and checks its table against the "
                            "frozen verified table. The Feistel domain stepping down is a consequence of the "
                            "smaller base and is part of what is measured"),
        "rejected_candidates": ("headers a (K'=8, 624 orbits), b (K'=4, 612), c (K'=8, 448) of the local prototype "
                                "are not measured here; inputs/local_profile.json lists their local numbers"),
        "power": {"file": "analysis/power.json", "label": power["label"], "min_delta": power["min_delta"],
                  "power_at_min_delta": power["power_at_min_delta"],
                  "rejection_rate_at_no_effect": power["type_i_at_1.00"],
                  "designs_compared": {k: {"power_at_1.10": v["cells"]["1.10"]["power"],
                                           "power_at_1.20": v["cells"]["1.20"]["power"]}
                                       for k, v in power["designs"].items()},
                  "expected_ratio_at_prior_means_modelled": power["expected_ratio_at_prior_means"],
                  "variance": power["variance"], "aa_control": power["aa_control"], "law_gate": power["law_gate"],
                  "planted_control": power["planted_control"]},
        "local_diagnostics": {"profile": "inputs/local_profile.json", "identity": "inputs/local_identity.json",
                              "closure_check": "inputs/local_verify_closure_D4.json",
                              "label": "cloud-agent VM, shared; correctness and sizing only"},
        "bootstrap": {"draws": DRAWS, "seed": BOOT_SEED},
    }
    (HERE / "protocol.json").write_text(json.dumps(p, indent=1, sort_keys=True) + "\n")
    print(str(HERE / "protocol.json"))


if __name__ == "__main__":
    main()
