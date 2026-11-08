#!/usr/bin/env python3
"""Write the frozen protocol (`protocol.json`) of the n=83 field-ops-2 experiment.

Run once, before any timing, after `restore.py --no-pin-check` (which derives
both producers, regenerates the closure headers and checks every parent
digest), `make_targets.py`, `check_panel_disjoint.py`, `check_seed_disjoint.py`,
`make_power_prior.py`, the local profile (`inputs/local_profile.json`) and
`power_check.py`. `restore.py` re-checks every digest this file records.
`--draft` writes a protocol without the power and profile fields, for local
runs before the power check; it is never the frozen protocol.

The bases, side A's arms (the current row, the parent's field-ops producer)
and the per-process gates are the parent's (`koblitz-n83-fieldops-20261104`,
on main, PR #1400), read from its frozen `protocol.json` (SHA-256 pinned in
`restore.py`). Side B's arms are the same configurations on the field-ops-2
producer `ic_online_fieldops2_r770` (`make_fieldops2_source.py`), built from
`online-b/` with the same `-C target-feature=+pclmulqdq` as side A. The
design, pairing, bootstrap, A/A control, Tier 1 records and fail-closed
verifier are the parent's, which follow the Tier 1 template
(`koblitz-n83-closure-indexlift-rep-20261020`, PR #1002). The planted control
is round 2's (`koblitz-n83-indexbuild2-20261020`): two COLD processes, cM38R1
and cM38R1X (KIC_INDEX_CANON=lift_plant), compared on the index build.
"""

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
POINTS = 12
K = 3            # alternating primary pairs per point
K_AA = 2         # alternating A/A pairs per point
K_PLANTED = 1    # alternating planted pairs per point
SEED0 = 2200     # rank seed of pair j at point i: SEED0 + 3 i + j (2201 .. 2236)
ORDER_SEED0 = 2026110770
RHO_SEED_BASE = 1070000
DRAWS = 10000
BOOT_SEED = 20261070
NEW_BINARY = "ic_online_fieldops2_r770"
PARENT_ARMS = ("cPFO", "cM10FO", "cM38FO", "kM38FO", "rT")
STAGE_KEYS = ("index_build_factor", "selftest_factor", "rank_stage_factor", "online_factor")
DEADLINE_MIN = 165


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def derived_arm(parent_arm, role, **override):
    arm = dict(parent_arm, binary=NEW_BINARY, field_ops_pipeline=PIPELINE, role=role)
    arm.pop("parent_source", None)
    arm.update(override)
    return arm


def main():
    global PIPELINE
    import restore  # noqa: E402  (this directory)
    import make_fieldops2_source as derivation  # noqa: E402

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--draft", action="store_true")
    args = parser.parse_args()
    PIPELINE = derivation.PIPELINE
    parent = restore.parent_protocol()
    if args.draft:
        power = {"expected_ratio_at_prior_means": 0.0, "expected_index_build_ratio": 0.0,
                 "expected_selftest_ratio": 0.0, "expected_rank_stage_ratio": 0.0, "expected_online_ratio": 0.0,
                 "design": {"points": POINTS, "primary_pairs_per_point": K, "aa_pairs_per_point": K_AA,
                            "planted_pairs_per_point": K_PLANTED},
                 "runtime": {"job_total_min": 0, "schedule_min": 0, "job_total_min_on_a_1.5x_slower_host": 0,
                             "job_limit_min": 0}, "min_delta": None, "power_at_min_delta": None,
                 "type_i_at_1.00": None, "cells": {"modelled": None}, "aa_control": None, "law_gate": None,
                 "planted_control": None}
        profile = {"modelled": dict.fromkeys(STAGE_KEYS)}
        profile_file = HERE / "inputs" / "local_profile.json"
        if profile_file.exists():
            given = json.loads(profile_file.read_text()).get("modelled") or {}
            if all(isinstance(given.get(k), (int, float)) for k in STAGE_KEYS):
                profile["modelled"] = {k: given[k] for k in STAGE_KEYS}
    else:
        power = json.loads((HERE / "analysis" / "power.json").read_text())
        profile = json.loads((HERE / "inputs" / "local_profile.json").read_text())
        if any(not isinstance(profile.get("modelled", {}).get(k), (int, float)) for k in STAGE_KEYS):
            raise SystemExit("inputs/local_profile.json `modelled` must give " + ", ".join(STAGE_KEYS))
    prior = json.loads((HERE / "inputs" / "power_prior.json").read_text())
    flat = list(prior["side_A_primary_pairs"].values())
    mean = {k: sum(side[k] for side in flat) / len(flat) for k in
            ("rank_stage_ms", "cold_ms", "index_ms", "scan_selftest_ms", "online_ms")}
    targets = json.loads((HERE / "inputs" / "cold_targets.json").read_text())
    disjoint = json.loads((HERE / "inputs" / "panel_disjointness.json").read_text())
    seeds_new = json.loads((HERE / "inputs" / "seed_disjointness.json").read_text())
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
    bases = {}
    for name, spec in parent["online"]["bases"].items():
        spec = dict(spec)
        spec["parent_source"] = ("koblitz-n83-fieldops-20261104 protocol.json online.bases.%s "
                                 "(sha256 %s), verbatim" % (name, restore.PARENT_PROTOCOL_SHA256))
        bases[name] = spec
    arms = {}
    for name in PARENT_ARMS:
        arms[name] = dict(parent["arms"][name])
        arms[name]["parent_source"] = "the parent's arm %s, verbatim (the current row's producer, or the rho reference)" % name
    arms["cPR1"] = derived_arm(parent["arms"]["cPFO"], "Q0 exactness on B's K600 header, field-ops-2 producer")
    arms["cM10R1"] = derived_arm(parent["arms"]["cM10FO"], "Q0 exactness on the M10 closure header, field-ops-2 producer")
    arms["cM38R1"] = derived_arm(parent["arms"]["cM38FO"],
                                 "PRIMARY candidate cold: cM38FO's configuration on the field-ops-2 producer")
    arms["kM38R1"] = derived_arm(parent["arms"]["kM38FO"],
                                 "PRIMARY candidate rank stage: kM38FO's configuration on the field-ops-2 producer")
    arms["cM38R1aa"] = dict(arms["cM38R1"], role="A/A copy of cM38R1")
    arms["kM38R1aa"] = dict(arms["kM38R1"], role="A/A copy of kM38R1")
    arms["cM38R1X"] = derived_arm(parent["arms"]["cM38FO"], (
        "PLANTED timing and exactness control: cM38R1 with KIC_INDEX_CANON=lift_plant: every index key from the "
        "linear run finder is also checked against lift_scan and the selected canonicalizer (2 x stored states "
        "checks); same layout digests, slower index build"), index_canon="lift_plant")
    source_of = {"cPR1": "cPFO", "cM10R1": "cM10FO"}
    for name in arms:
        if name not in PARENT_ARMS:
            arms[name]["derived_from"] = "the parent's arm %s with binary %s" % (
                source_of.get(name, "kM38FO" if name.startswith("k") else "cM38FO"), NEW_BINARY)
            if name == "cM38R1X":
                arms[name]["derived_from"] += " and index_canon lift_plant"
    rank_seeds = {"s%03d" % i: [SEED0 + 3 * i + j for j in range(1, K + 1)] for i in range(POINTS)}
    protocol = {
        "schema": 1,
        "kind": "n83-fieldops2-paired-e2e-tier1",
        "frozen_before_any_timing": True,
        "draft_not_frozen": bool(args.draft),
        "frozen_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "question": ("Is the field-ops-2 producer's END-TO-END cold cost (setup + index build + rank stage + "
                     "linear algebra + one-target online) on the M38 closure base lower than the current n=83 a=1 "
                     "row's (the field-ops producer of koblitz-n83-fieldops-20261104), on new held-out points "
                     "and new rank seeds? The field-ops-2 producer computes the same values with one change to "
                     "how: R1, at n = 83 the inlined GF(2^83) product and square are called with the field degree "
                     "and mask as constants (`if gf.n == 83 { return fast_field::mul(83, (1 << 83) - 1, tail, a, "
                     "b) }`), so the reduction's shifts are immediates instead of values read from the field "
                     "struct; every key, probe, relation, root call, counter, index and rank table is the "
                     "parent's. Both sides are built with -C target-feature=+pclmulqdq (.cargo/config.toml of "
                     "online/ and online-b/). The test uses repeated alternating pairs and a 95% paired "
                     "confidence interval whose lower bound must exceed 1 (AGENTS.md, 'CPU performance "
                     "isolation gate', Tier 1)."),
        "why_this_run": ("On the parent's run 41869146827 (on main) its side B (this experiment's side A) spent "
                         "%.2f of its %.2f s end to end in the rank stage and %.2f s of the cold process in the "
                         "index build, %.2f s in the scan self-test and %.2f s in the online stage (means over its "
                         "36 primary pairs, inputs/power_prior.json). Every field product of those stages runs "
                         "the parent's inlined reduction with its degree and mask read at run time; R1 makes "
                         "them constants at n = 83. A local diagnostic (shared VM, not evidence) saw the index "
                         "build about 5.3%% and the rank stage about 3.1%% shorter with identical digests; the "
                         "local profile (inputs/local_profile.json) gives the four stage factors the power "
                         "check models." % (mean["rank_stage_ms"] / 1000,
                                            (mean["rank_stage_ms"] + mean["cold_ms"]) / 1000,
                                            mean["index_ms"] / 1000, mean["scan_selftest_ms"] / 1000,
                                            mean["online_ms"] / 1000)),
        "success_criterion": "AGENTS.md 'Success criterion: iterative improvement of the index-calculus baseline'",
        "tier_rule": ("AGENTS.md 'CPU performance evidence tiers', Tier 1: same pinned exposed CPU, same workload and "
                      "limits; code and workload hashes, paired order, raw failures, correctness, process CPU time, "
                      "memory, cgroup throttling and memory failures, steal time and scheduling counters recorded; "
                      "repeated alternating pairs and a 95% paired confidence interval whose lower bound exceeds 1"),
        "baseline_row": {"experiment": "koblitz-n83-fieldops-20261104", "landed": "on main (PR #1400)",
                         "producer_sha256": parent["sources"]["fieldops_source_sha256"],
                         "binary": "ic_online_fieldops_r770",
                         "tier1_qualification": {"run": "https://github.com/isogeny-labs/cryptanalysis/actions/runs/41869146827",
                                                 "primary": "1.2610 [1.2541, 1.2681] over the rank-finder row"},
                         "parent_protocol_sha256": restore.PARENT_PROTOCOL_SHA256,
                         "ratchet_rule": ("if another PR replaces the n=83 row before this one lands, this result "
                                          "is recorded as an improvement over the row it measured (this one), "
                                          "and a combined run follows")},
        "template": {"experiment": "koblitz-n83-fieldops-20261104", "landed": "on main (PR #1400)",
                     "tier1_template_of_the_parent": "koblitz-n83-closure-indexlift-rep-20261020 (PR #1002), via the parent",
                     "planted_design_of": "koblitz-n83-indexbuild2-20261020 (PR #1009)",
                     "copied_verbatim": sorted(restore.TEMPLATE)},
        "expected_effect": ("about %.3f end to end at the parent run's side-B means and the local stage factors "
                            "(index build %.3f, scan self-test %.3f, rank stage %.3f, online %.3f as ratios A / B; "
                            "power_check.py; an estimate, not a claim)" % (
                                power["expected_ratio_at_prior_means"], power["expected_index_build_ratio"],
                                power["expected_selftest_ratio"], power["expected_rank_stage_ratio"],
                                power["expected_online_ratio"])),
        "sources": {
            "crypto_770f6a69": parent["sources"]["crypto_770f6a69"],
            "rankprobe_producer": parent["sources"]["rankprobe_producer"],
            "indexlift_producer": parent["sources"]["indexlift_producer"],
            "closure_producer": parent["sources"]["closure_producer"],
            "composition": parent["sources"]["composition"],
            "grandparent_source_sha256": sha256(restore.DERIVED_GRANDPARENT),
            "indexbuild_source_sha256": sha256(restore.DERIVED_IB),
            "indexbuild2_source_sha256": sha256(restore.DERIVED_IB2),
            "online_source_sha256": sha256(restore.DERIVED),
            "online_source_sha256_parent": parent["sources"]["fieldops_source_sha256"],
            "rankfinder_source_sha256": sha256(restore.DERIVED_RF),
            "fieldops_source_sha256": sha256(restore.DERIVED),
            "fieldops2_source_sha256": sha256(restore.DERIVED_B),
            "fieldops2_derivation": ("make_fieldops2_source.py: %d counted replacements (%s) on the row's "
                                     "producer text; check_inverse() undoes them to the parent's bytes on every "
                                     "derivation" % (len(derivation.edits()),
                                                     ", ".join(e[0] for e in derivation.edits()))),
            "field_ops_pipeline": PIPELINE,
            "field_ops_pipeline_side_A": parent["sources"]["field_ops_pipeline"],
            "rank_probe_pipeline": parent["sources"]["rank_probe_pipeline"],
            "index_build_pipeline": parent["sources"]["index_build_pipeline"],
            "builds": {
                "side_A": ("online/Cargo.toml: bins ic_online_fieldops_r770 and rho_tuned_r770, with `-C "
                           "target-feature=+pclmulqdq` (online/.cargo/config.toml, the same flags the field-ops "
                           "row was built with)"),
                "side_B": ("online-b/Cargo.toml: bin ic_online_fieldops2_r770, built with the same `-C "
                           "target-feature=+pclmulqdq` (online-b/.cargo/config.toml, the same file); "
                           "fast_field::check fails closed if the CPU lacks the instruction"),
                "shared": "one toolchain; online/Cargo.lock and online-b/Cargo.lock are the same file",
            },
            "parent_protocol_sha256": restore.PARENT_PROTOCOL_SHA256,
            "verbatim_from_parent": list(restore.VERBATIM),
            "verbatim_from_template": dict(restore.TEMPLATE),
            "changed_from_parent": {
                "online/Cargo.toml, online/.cargo/config.toml": ("[[bin]] ic_online_rankfinder_r770 replaced by "
                                                                 "ic_online_fieldops_r770 (the row, built from "
                                                                 "the parent's online-b/ recipe) beside "
                                                                 "rho_tuned_r770; the carry-less multiply enabled "
                                                                 "as in the parent's online-b/"),
                "online-b/": ("bin ic_online_fieldops2_r770 instead of ic_online_fieldops_r770, the same "
                              "flags, dependencies and lock"),
                "verify_receipt.py, test_verify_receipt.py": ("the arm names and binaries of this experiment; the "
                                                              "field_ops_pipeline gate now has a pipeline on both "
                                                              "sides"),
                "make_schedule.py": "arm names in its text only",
                "restore.py": "one more derivation step and the parent's pins",
                "make_targets.py, check_seed_disjoint.py": "the new role and seed range",
                "make_power_prior.py, power_check.py": "the prior run (the parent's), the seed and the minimum effect",
                "make_fieldops2_source.py": "new: side B's derivation (R1)",
            },
            "local_sha256": {key: sha256(path) for key, path in restore.local_files().items()
                             if not args.draft or Path(path).exists()},
        },
        "online": {
            "bases": bases,
            "curve_id": parent["online"]["curve_id"],
            "subgroup_order": parent["online"]["subgroup_order"],
            "lambda": parent["online"]["lambda"],
            "sqrt_r": parent["online"]["sqrt_r"],
            "tuned_rho_config": parent["online"]["tuned_rho_config"],
            "cold_targets_file": ("inputs/cold_targets.json (role %s, %d points). It is disjoint from Q0, B's panel "
                                  "and every n=83 panel of the law on origin and in the scratch worktrees "
                                  "(make_targets.py EARLIER_ROLES, including the parent's fieldops-cold-v1; "
                                  "role-agnostic x/y scan in inputs/panel_disjointness.json, 0 hits)" % (
                                      targets["role"], POINTS)),
            "cold_interval": parent["online"]["cold_interval"],
            "rank_interval": parent["online"]["rank_interval"],
            "online_interval": parent["online"]["online_interval"],
            "base_construction": parent["online"]["base_construction"],
        },
        "arms": arms,
        "design": {
            "points": POINTS,
            "primary_pairs_per_point": K,
            "aa_pairs_per_point": K_AA,
            "planted_pairs_per_point": K_PLANTED,
            "sides": {"A": ["kM38FO", "cM38FO"], "B": ["kM38R1", "cM38R1"], "Baa": ["kM38R1aa", "cM38R1aa"]},
            "planted_arms": ["cM38R1", "cM38R1X"],
            "side_rule": parent["design"]["side_rule"],
            "pair_rule": parent["design"]["pair_rule"],
            "rank_stage_design": ("same rank seed per pair, not a shared rank stage: each side runs its own rank "
                                  "process on its own binary. The change touches how field products, squarings, "
                                  "linear maps and the scan self-test are computed, not which values, so the rank "
                                  "stage's work is the same in both (gated: identical relation digests, probe "
                                  "vectors, root calls and counters per seed across kM38FO, kM38R1 and kM38R1aa); "
                                  "the rank stage is timed on each side, and so are the cold processes, so any "
                                  "code-layout effect of the new binary stays inside E2E instead of being assumed "
                                  "away"),
            "aa_rule": parent["design"]["aa_rule"],
            "planted_rule": ("a planted pair is cM38R1 and cM38R1X, cold processes only, alternating, with the "
                             "start drawn from the same generator"),
            "rho_rule": parent["design"]["rho_rule"],
            "segment_rule": ("O1: Q0 on cPFO, cPR1, cM10FO, cM10R1, cM38FO and cM38R1, shuffled by "
                             "random.Random(ORDER_SEED0 + 99). Then one segment P<i> per point i = 1..POINTS in "
                             "panel order. Its four sub-blocks (primary, aa, planted, rho) run in an order shuffled "
                             "by the point's generator"),
            "order_seed0": ORDER_SEED0,
            "rank_seed0": SEED0,
            "rank_seeds": rank_seeds,
            "rank_seeds_note": ("2201-2236 are new on n=83 (inputs/seed_disjointness.json: every n83 schedule and "
                                "protocol on origin/main, every origin n83 branch and the scratch worktrees; the "
                                "positive control finds the parent's 2101-2136)"),
            "rho_seed_base": RHO_SEED_BASE,
            "q0_point": parent["design"]["q0_point"],
            "q0_arms": ["cPFO", "cPR1", "cM10FO", "cM10R1", "cM38FO", "cM38R1"],
            "process_model": "one point per process, fresh process per run, one pinned CPU, one runner",
            "segment_upper_estimate_s": {"O": 200, "P": 450},
            "timeout_s": parent["design"]["timeout_s"],
            "time_guard": ("before each segment: skip it (rows skipped_time_guard) if the elapsed job time plus the "
                           "larger of its upper estimate and 1.1x the longest segment of its panel so far exceeds "
                           "%d min. A skipped row makes the run invalid" % DEADLINE_MIN),
            "deadline_min": DEADLINE_MIN,
            "runtime_estimate": ("power.json runtime: about %.0f min for the job (%.0f min schedule), about %.0f min on "
                                 "a 1.5x slower host; time guard %d min, job limit %d min" % (
                                     power["runtime"]["job_total_min"], power["runtime"]["schedule_min"],
                                     power["runtime"]["job_total_min_on_a_1.5x_slower_host"], DEADLINE_MIN,
                                     power["runtime"]["job_limit_min"])),
        },
        "gates": [
            "every scheduled row present and valid (exit 0, verified, schedule match, no memory event), no time-guard skip",
            ("receipt integrity (verify_receipt.py, fail closed): every executed row's raw producer record decodes, "
             "its SHA-256 equals the wrapper summary's raw_result_sha256, and its arm, kind, panel, point and seed "
             "equal the frozen schedule's. Each row's serial, arm, point, seed, segment, command line and stdout "
             "file equal the schedule's. Rows ran in schedule order. runner_start.json records this protocol's, "
             "this schedule's, arm.py's and run_schedule.py's SHA-256 and no smoke subset. Every row ran its ARM's "
             "binary (by name and by the digest runner_start.json lists), unchanged at the end. An unknown gate is "
             "a failure"),
            ("every IC row's summary names its arm's rank_probe_pipeline (linear_canon_lanes8 on both binaries) and "
             "its arm's field_ops_pipeline (%s on the field-ops binary, absent on side A's binary and in every "
             "side-A arm)" % PIPELINE),
            "placement: every process's Cpus_allowed_list, read from /proc while it ran, is the one execution CPU",
            ("host identity: the CPU record (scripts/host_cpu_record.py) at the start and the end of the schedule has "
             "the same model, microcode and flags"),
            ("before any timing: check_log_table.py (verbatim). B's table is re-verified in the pinned oracle. Both "
             "closure headers are regenerated to their frozen SHA-256 and pass verify_closure.py, and the three "
             "planted corruptions are rejected. The online crate's tests pass on side A's crate (online) and on "
             "side B's (online-b, built with +pclmulqdq), including fieldops_tests (the inlined product and square "
             "against the library's on every pair of a 2^20-element sample and on edge cases, the square map against "
             "the inlined square, the byte-image lookup against the shift loop, and the table-evaluated permutation "
             "against `apply` on every index of the M38 and M10 domains for both self-test keys), rankfinder_tests "
             "and the parent's indexbuild2_tests"),
            ("every IC process (arm.py): KIC_INDEX_CANON as the arm (lift; lift_plant in cM38R1X only); index roots "
             "checked against the selected canonicalizer 0 times, or 2 x stored states in cM38R1X; the full scan "
             "self-test; the arm's index_build_pipeline (the same on both sides); the arm's field_ops_pipeline; its "
             "base's frozen base hash, columns, orbits, states, slots, root entries, logical-state and table-map "
             "digests; its base's frozen LAYOUT digests (stored_states_blake3, table_slots_blake3); on rank arms the "
             "arm's rank_solve and one frame per attempt"),
            "per point: one scalar across every IC process (both binaries, cold and rank) and rT, replayed as [d]G = Q in the pinned oracle",
            "per point and base: one relation and one probe count across every IC process of both binaries",
            "per base (K600, M38 and M10): one index and layout digest set across both binaries, equal to the frozen one",
            ("Q0 (O1): cPFO and cPR1 give B's archived identity (1,987,852 probes); cM38FO and cM38R1, and cM10FO and "
             "cM10R1, give their closure base's frozen identity"),
            ("rank arms: full rank, 0 failed attempts, one frame per attempt, and the written factor-log table equal "
             "to the base's frozen verified table, log for log"),
            ("per M38 rank seed: rank_relations_blake3, the per-attempt probe vector, root calls and point-addition "
             "counters identical across every kM38FO, kM38R1 and kM38R1aa process with that seed"),
            ("probe law: kM38FO's pooled probes per relation over its %d distinct seeds (%d attempts) over "
             "r / (166 E) inside [0.80, 1.20]" % (POINTS * K, POINTS * K * 16)),
        ],
        "statistics": {
            "e2e_per_side": parent["statistics"]["e2e_per_side"],
            "primary": ("R = sum over the %d primary pairs of E2E(A) / sum over the same pairs of E2E(B). 95%% "
                        "percentile interval from a two-stage paired bootstrap, %d draws, random.Random(%d): the "
                        "points drawn with replacement, then each drawn point's pairs drawn with replacement; A and "
                        "B of a pair are always drawn together" % (POINTS * K, DRAWS, BOOT_SEED)),
            "primary_is": "the paired END-TO-END ratio over the current row; every stage ratio is co-reported and never decides",
            "stage_secondary": ("four STAGE ratios, each labelled a stage secondary and never deciding, in the primary "
                                "pairs with the same bootstrap: index build (timing_ms.index_build of the cold "
                                "process) cM38FO / cM38R1, scan self-test (scan_order_selftest.ms of the cold process) "
                                "cM38FO / cM38R1, rank stage (timing_ms.rank_stage) kM38FO / kM38R1, and online "
                                "(online_ms of the cold process) cM38FO / cM38R1"),
            "pairing_basis": parent["statistics"]["pairing_basis"],
            "secondary": [
                "geometric mean of the per-pair ratios E2E(A)/E2E(B), with the same bootstrap",
                "index build, scan self-test, rank stage and online (stage secondaries, labelled), paired",
                "cold, setup cM38FO / cM38R1, paired",
                "index build in the rank processes kM38FO / kM38R1, paired",
                "E2E process CPU time and process wall A / B, with the same bootstrap",
                "peak RSS and minor faults of the cold processes",
                "per-point ratio, and the ratio by pair position and by side order",
                "probe law of kM38FO and kM38R1; rank ns per probe; rho ms/step from rT; S per side; E2E cold gap FO / rT",
            ],
        },
        "controls_pass_rule": {
            "aa": ("over the %d A/A pairs: E2E(B) / E2E(Baa) and cold cM38R1 / cM38R1aa, the same ratio of sums, "
                   "point estimates both inside [0.97, 1.03]" % (POINTS * K_AA)),
            "planted": ("index build cM38R1X / cM38R1 over the %d planted pairs, 95%% bootstrap lower bound (pairs "
                        "resampled, 10,000 draws) above 1; every cM38R1X must also reproduce the frozen layout "
                        "digests and check 2 x stored states roots" % (POINTS * K_PLANTED)),
            "planted_exactness": ("the three planted corruptions rejected by verify_closure.py on both closure bases "
                                  "before timing, and the crate tests passing"),
            "otherwise": "verdict invalid",
        },
        "decision_rule": {
            "improvement": "R lower bound > 1: a qualified Tier 1 end-to-end speedup of the field-ops producer over the row",
            "regression": "R upper bound < 1",
            "not_separated": "otherwise",
            "invalid": "any gate or control fails or is unknown, or any scheduled row is missing (time-guard skips included)",
        },
        "multiplicity": "one primary statistic; every secondary is descriptive and never changes the verdict",
        "exactness_argument": {
            "parent": parent["exactness_argument"],
            "fieldops2": " ".join(re.search(r"R1\. \*\*A constant reduce shift.*?(?=\n`--check`)", derivation.__doc__,
                                            re.S).group(0).split()),
        },
        "evidence_change": ("none: the rank stage still runs to full rank, writes its table and checks it against the "
                            "frozen verified table; every process still runs the full scan self-test (the same three "
                            "checks of the same function over the same domain), builds, checks and digests its own "
                            "index. No sampled check is used."),
        "rejected_candidates": "R2 (proto_r12, which also touched the linear run finder) was rejected before this design and is not part of it; README section 3 lists what is out of scope",
        "power": {"file": "analysis/power.json", "min_delta": power["min_delta"],
                  "power_at_min_delta": power["power_at_min_delta"],
                  "rejection_rate_at_no_effect": power["type_i_at_1.00"],
                  "modelled": power["cells"]["modelled"],
                  "expected_ratio_at_prior_means": power["expected_ratio_at_prior_means"],
                  "expected_stage_ratios": {"index_build": power["expected_index_build_ratio"],
                                            "scan_selftest": power["expected_selftest_ratio"],
                                            "rank_stage": power["expected_rank_stage_ratio"],
                                            "online": power["expected_online_ratio"]},
                  "aa_control": power["aa_control"], "law_gate": power["law_gate"],
                  "planted_control": power["planted_control"]},
        "local_diagnostics": {"profile": "inputs/local_profile.json", "exactness": "inputs/local_exactness.json",
                              "label": "cloud-agent VM, shared; correctness and sizing only",
                              "modelled_stage_factors": {k: profile["modelled"][k] for k in STAGE_KEYS}},
        "bootstrap": {"draws": DRAWS, "seed": BOOT_SEED},
    }
    (HERE / "protocol.json").write_text(json.dumps(protocol, indent=1, sort_keys=True) + "\n")
    print(str(HERE / "protocol.json"))


if __name__ == "__main__":
    main()
