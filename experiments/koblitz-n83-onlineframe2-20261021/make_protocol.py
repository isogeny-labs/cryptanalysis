#!/usr/bin/env python3
"""Write the frozen protocol (`protocol.json`) of the n=83 online-frame round-2 experiment.

Run once, before any timing, after `restore.py --no-pin-check` (which derives
both producers, regenerates the closure headers and checks every parent
digest), `make_targets.py`, `check_panel_disjoint.py`, `check_seed_disjoint.py`,
`summarize_exactness.py`, `make_power_prior.py` and `power_check.py`.
`restore.py` re-checks every digest this file records. `--draft` writes a
protocol without the power and exactness fields, for the local exactness
runs before the power check; it is never the frozen protocol.

The bases, side A's arms (the current row, the parent's round-2 index-build
producer, `ic_online_indexbuild2_r770`) and the per-process gates are the
parent's (`koblitz-n83-indexbuild2-20261020`, PR #1009), read from its frozen
`protocol.json` (SHA-256 pinned in `restore.py`). Side B's arms are the same
configurations on the online-frame producer `ic_online_onlineframe2_r770`
(`make_onlineframe2_source.py`) with `KIC_ONLINE_SOLVE=frame`. The design,
pairing, bootstrap, A/A control, Tier 1 records and fail-closed verifier are
the parent's, which follow the Tier 1 template
(`koblitz-n83-closure-indexlift-rep-20261020`, PR #1002).
"""

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
POINTS = 16
K = 4            # alternating primary pairs per point
K_AA = 1         # alternating A/A pairs per point
K_PLANTED = 1    # alternating planted pairs per point
K_LAYOUT = 1     # alternating same-binary layout pairs per point
SEED0 = 2300     # rank seed of pair j at point i: SEED0 + 4 i + j (2301 .. 2364)
ORDER_SEED0 = 2026102170
RHO_SEED_BASE = 1060000
DRAWS = 10000
BOOT_SEED = 20261060
NEW_BINARY = "ic_online_onlineframe2_r770"
PARENT_ARMS = ("cPIC", "cM10IC", "cM38IC", "kM38IC", "rT")
DEADLINE_MIN = 165


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def derived_arm(parent_arm, role, online_solve="frame", **override):
    arm = dict(parent_arm, binary=NEW_BINARY, online_solve=online_solve, role=role)
    arm.pop("parent_source", None)
    arm.update(override)
    return arm


def main():
    import restore  # noqa: E402  (this directory)
    import make_onlineframe2_source as derivation  # noqa: E402

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--draft", action="store_true")
    args = parser.parse_args()
    parent = restore.parent_protocol()
    if args.draft:
        power = {"expected_ratio_at_prior_means": 0.0, "expected_cold_ratio_at_prior_means": 0.0,
                 "expected_online_ratio": 0.0, "online_share_of_e2e_A": 0.0,
                 "design": {"points": POINTS, "primary_pairs_per_point": K, "aa_pairs_per_point": K_AA,
                            "planted_pairs_per_point": K_PLANTED, "layout_pairs_per_point": K_LAYOUT},
                 "runtime": {"job_total_min": 0, "schedule_min": 0, "job_total_min_on_a_1.5x_slower_host": 0,
                             "job_limit_min": 0}, "min_delta": None, "power_at_min_delta": None,
                 "type_i_at_1.00": None, "cells": {"modelled": None, "archived_onlineframe": None},
                 "aa_control": None, "law_gate": None, "planted_control": None, "candidate_model": None}
        exactness = None
    else:
        power = json.loads((HERE / "analysis" / "power.json").read_text())
        exactness = json.loads((HERE / "inputs" / "local_exactness.json").read_text())
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
    if (pd["points"], pd["primary_pairs_per_point"], pd["aa_pairs_per_point"], pd["planted_pairs_per_point"],
            pd["layout_pairs_per_point"]) != (POINTS, K, K_AA, K_PLANTED, K_LAYOUT):
        raise SystemExit("power.json was computed for another design")
    bases = {}
    for name, spec in parent["online"]["bases"].items():
        spec = dict(spec)
        spec["parent_source"] = ("koblitz-n83-indexbuild2-20261020 protocol.json online.bases.%s "
                                 "(sha256 %s), verbatim" % (name, restore.PARENT_PROTOCOL_SHA256))
        bases[name] = spec
    arms = {}
    for name in PARENT_ARMS:
        arms[name] = dict(parent["arms"][name])
        arms[name]["parent_source"] = "the parent's arm %s, verbatim (the current row's producer)" % name
    arms["cPOF"] = derived_arm(parent["arms"]["cPIC"], "Q0 exactness on B's K600 header, online-frame producer")
    arms["cM10OF"] = derived_arm(parent["arms"]["cM10IC"],
                                 "Q0 exactness on the M10 closure header, online-frame producer")
    arms["cM38OF"] = derived_arm(parent["arms"]["cM38IC"], (
        "PRIMARY candidate cold: cM38IC's configuration on the online-frame producer, KIC_ONLINE_SOLVE=frame"))
    arms["kM38OF"] = derived_arm(parent["arms"]["kM38IC"], (
        "PRIMARY candidate rank stage: kM38IC's configuration on the online-frame producer (the rank stage is "
        "the parent's code; the point it then solves uses KIC_ONLINE_SOLVE=frame)"))
    arms["cM38OFaa"] = dict(arms["cM38OF"], role="A/A copy of cM38OF")
    arms["kM38OFaa"] = dict(arms["kM38OF"], role="A/A copy of kM38OF")
    arms["cM38OFX"] = derived_arm(parent["arms"]["cM38IC"], (
        "PLANTED timing and exactness control: cM38OF with KIC_ONLINE_SOLVE=frame_s3plant: on every state the "
        "online scan reaches, the parent's S3 loop is redone and compared with the frame loop (relation, probe "
        "counter, root calls, relation checks and every candidate's key pair); slower online interval"),
        online_solve="frame_s3plant")
    arms["cM38OS"] = derived_arm(parent["arms"]["cM38IC"], (
        "LAYOUT control (descriptive): the online-frame binary with KIC_ONLINE_SOLVE=s3, the parent's online "
        "loop; cM38OS / cM38OF online is the online ratio within one binary, free of the A/B binary-layout "
        "offset the parent's run saw on unchanged stages"), online_solve="s3")
    for name in arms:
        if name not in PARENT_ARMS:
            src = {"cPOF": "cPIC", "cM10OF": "cM10IC"}.get(name, "kM38IC" if name.startswith("k") else "cM38IC")
            arms[name]["derived_from"] = "the parent's arm %s with binary %s and online_solve %s" % (
                src, NEW_BINARY, arms[name]["online_solve"])
    rank_seeds = {"s%03d" % i: [SEED0 + K * i + j for j in range(1, K + 1)] for i in range(POINTS)}
    mean = power.get("prior_means_ms", {})
    protocol = {
        "schema": 1,
        "kind": "n83-onlineframe2-paired-e2e-tier1",
        "frozen_before_any_timing": True,
        "draft_not_frozen": bool(args.draft),
        "frozen_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "question": ("Is the online-frame producer's END-TO-END cold cost (setup + index build + rank stage + linear "
                     "algebra + one-target online) on the M38 closure base lower than the current n=83 a=1 row's "
                     "(the round-2 index-build producer of koblitz-n83-indexbuild2-20261020), on new held-out points "
                     "and new rank seeds? The online-frame producer is the row's producer with the one-target online "
                     "scan run on the rank stage's PIPE_FRAME point-addition loop (KIC_ONLINE_SOLVE=frame, the seven "
                     "replacements of koblitz-n83-onlineframe-20261019) instead of the batched S3 solve; every "
                     "relation, probe count, root call and relation check is the S3 loop's, and setup, the root "
                     "index and the rank stage are the parent's bytes. The test uses repeated alternating pairs and "
                     "a 95% paired confidence interval whose lower bound must exceed 1 (AGENTS.md, 'CPU performance "
                     "isolation gate', Tier 1)."),
        "why_this_run": ("PR #988 measured KIC_ONLINE_SOLVE=frame at 1.5733 [1.5714, 1.5753] online on the "
                         "rank-probe producer, with one pair per point; its qualification note "
                         "(reviews/pr-988-onlineframe-qualification-20261019/QUALIFICATION.md) records that this is "
                         "not a qualified Tier 1 speedup (no repeated alternating pairs). The selector is not in the "
                         "current row's lineage (rank-probe -> index-lift + closure -> index-build -> round 2), so "
                         "it is ported here as a counted derivation and measured end to end over the current row "
                         "with repeated alternating pairs. In the parent's run the row's online stage was "
                         "%.1f ms of %.1f ms end to end (%.1f%%)" % (
                             mean.get("online_ms", 0.0), mean.get("E2E_A", 0.0),
                             100 * power["online_share_of_e2e_A"])),
        "success_criterion": "AGENTS.md 'Success criterion: iterative improvement of the index-calculus baseline'",
        "tier_rule": ("AGENTS.md 'CPU performance evidence tiers', Tier 1: same pinned exposed CPU, same workload and "
                      "limits; code and workload hashes, paired order, raw failures, correctness, process CPU time, "
                      "memory, cgroup throttling and memory failures, steal time and scheduling counters recorded; "
                      "repeated alternating pairs and a 95% paired confidence interval whose lower bound exceeds 1"),
        "baseline_row": {"experiment": "koblitz-n83-indexbuild2-20261020", "pr": 1009, "merge": "186c5b0a8",
                         "producer_sha256": parent["sources"]["indexbuild2_source_sha256"],
                         "binary": "ic_online_indexbuild2_r770",
                         "tier1_qualification": {"run": "https://github.com/aburan28/cryptanalysis/actions/runs/39464544962",
                                                 "primary": "1.1169 [1.1110, 1.1231] over the index-build row"},
                         "parent_protocol_sha256": restore.PARENT_PROTOCOL_SHA256,
                         "ratchet": ("if a sibling lead replaces the row before this result lands, this result is "
                                     "recorded as an improvement over the row it measured (this one), under the "
                                     "ratchet rule; it is not re-based")},
        "online_frame_origin": {"experiment": "koblitz-n83-onlineframe-20261019", "pr": 988,
                                "run": "https://github.com/aburan28/cryptanalysis/actions/runs/39303742695",
                                "online_ratio": "1.5733 [1.5714, 1.5753], one pair per point (not Tier 1 qualified)",
                                "protocol_sha256": restore.ONLINEFRAME_PROTOCOL_SHA256,
                                "derivation_sha256": sha256(HERE / "make_onlineframe_source.py")},
        "template": {"experiment": "koblitz-n83-indexbuild2-20261020", "pr": 1009,
                     "tier1_template_of_the_parent": "koblitz-n83-closure-indexlift-rep-20261020 (PR #1002)",
                     "copied_verbatim": sorted(restore.TEMPLATE)},
        "expected_effect": ("about %.4f end to end, %.4f cold and %.3f online at the parent run's row means, with the "
                            "online factor taken from the row's own rank-stage frame cost per probe (power_check.py; "
                            "an estimate, not a claim)" % (
                                power["expected_ratio_at_prior_means"], power["expected_cold_ratio_at_prior_means"],
                                power["expected_online_ratio"])),
        "sources": {
            "crypto_770f6a69": parent["sources"]["crypto_770f6a69"],
            "rankprobe_producer": parent["sources"]["rankprobe_producer"],
            "indexlift_producer": parent["sources"]["indexlift_producer"],
            "closure_producer": parent["sources"]["closure_producer"],
            "composition": parent["sources"]["composition"],
            "greatgrandparent_source_sha256": sha256(restore.DERIVED_GREATGRANDPARENT),
            "grandparent_source_sha256": sha256(restore.DERIVED_GRANDPARENT),
            "online_source_sha256": sha256(restore.DERIVED),
            "online_source_sha256_parent": parent["sources"]["indexbuild2_source_sha256"],
            "onlineframe2_source_sha256": sha256(restore.DERIVED_B),
            "onlineframe2_derivation": ("make_onlineframe2_source.py: %d counted replacements (%s) on the row's "
                                        "producer text, seven of them imported from make_onlineframe_source.py "
                                        "(koblitz-n83-onlineframe-20261019, verbatim); check_inverse() undoes them "
                                        "to the parent's bytes on every derivation" % (
                                            len(derivation.EDITS), ", ".join(e[0] for e in derivation.EDITS))),
            "index_build_pipeline": parent["sources"]["indexbuild2_pipeline"],
            "parent_protocol_sha256": restore.PARENT_PROTOCOL_SHA256,
            "onlineframe_protocol_sha256": restore.ONLINEFRAME_PROTOCOL_SHA256,
            "verbatim_from_parent": list(restore.VERBATIM),
            "verbatim_from_template": dict(restore.TEMPLATE),
            "changed_from_parent": {
                "online/Cargo.toml": ("[[bin]] ic_online_indexbuild_r770 removed (still derived, no longer an arm), "
                                      "[[bin]] ic_online_onlineframe2_r770 added (same lock, same dependencies)"),
                "arm.py": ("KIC_ONLINE_SOLVE from the arm's online_solve, and the online-solve and online-counter "
                           "gates; the record's root calls, relation checks, x codes and intermediates copied into "
                           "the fields"),
                "make_schedule.py": "the layout sub-block (cM38OS / cM38OF) and cM38OFX in O1",
                "verify_receipt.py, test_verify_receipt.py": ("the arm names and binaries of this experiment, the "
                                                              "online-identity gates, the planted control on the "
                                                              "online interval and the layout secondary"),
                "restore.py": "one more derivation step, the parent's and the online-frame protocol's pins",
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
                                  "(make_targets.py EARLIER_ROLES, including the parent's indexbuild2-cold-v1; "
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
            "layout_pairs_per_point": K_LAYOUT,
            "sides": {"A": ["kM38IC", "cM38IC"], "B": ["kM38OF", "cM38OF"], "Baa": ["kM38OFaa", "cM38OFaa"]},
            "planted_arms": ["cM38OF", "cM38OFX"],
            "layout_arms": ["cM38OS", "cM38OF"],
            "side_rule": parent["design"]["side_rule"],
            "pair_rule": parent["design"]["pair_rule"],
            "rank_stage_design": ("same rank seed per pair, not a shared rank stage: each side runs its own rank "
                                  "process on its own binary. KIC_ONLINE_SOLVE is read only by the online scan, so "
                                  "the rank stage's work is the same in both (gated: identical relation digests, "
                                  "probe vectors, root calls and counters per seed across kM38IC, kM38OF and "
                                  "kM38OFaa); timing it on each side keeps any code-layout effect of the new binary "
                                  "on the rank loop inside E2E instead of assuming it away"),
            "aa_rule": parent["design"]["aa_rule"],
            "planted_rule": ("a planted pair is cM38OF and cM38OFX, cold processes only, alternating, with the start "
                             "drawn from the same generator"),
            "layout_rule": ("a layout pair is cM38OS and cM38OF, cold processes only, alternating, with the start "
                            "drawn from the same generator; descriptive, never decides"),
            "rho_rule": parent["design"]["rho_rule"],
            "segment_rule": ("O1: Q0 on cPIC, cPOF, cM10IC, cM10OF, cM38IC, cM38OF and cM38OFX, shuffled by "
                             "random.Random(ORDER_SEED0 + 99). Then one segment P<i> per point i = 1..POINTS in "
                             "panel order. Its five sub-blocks (primary, aa, planted, layout, rho) run in an order "
                             "shuffled by the point's generator"),
            "order_seed0": ORDER_SEED0,
            "rank_seed0": SEED0,
            "rank_seeds": rank_seeds,
            "rank_seeds_note": ("2301-2364 are new on n=83 (inputs/seed_disjointness.json: every n83 schedule and "
                                "protocol on origin/main, every origin n83 branch and the scratch worktrees; the "
                                "positive control finds the parent's 1501-1536)"),
            "rho_seed_base": RHO_SEED_BASE,
            "q0_point": parent["design"]["q0_point"],
            "q0_arms": ["cPIC", "cPOF", "cM10IC", "cM10OF", "cM38IC", "cM38OF", "cM38OFX"],
            "process_model": "one point per process, fresh process per run, one pinned CPU, one runner",
            "segment_upper_estimate_s": {"O": 200, "P": 500},
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
            "placement: every process's Cpus_allowed_list, read from /proc while it ran, is the one execution CPU",
            ("host identity: the CPU record (scripts/host_cpu_record.py) at the start and the end of the schedule has "
             "the same model, microcode and flags"),
            ("before any timing: check_log_table.py (verbatim). B's table is re-verified in the pinned oracle. Both "
             "closure headers are regenerated to their frozen SHA-256 and pass verify_closure.py, and the three "
             "planted corruptions are rejected. The online crate's tests pass for both IC binaries: the row's 32 "
             "and the online-frame producer's 35 (the row's 32, the imported onlineframe_tests and "
             "onlineframe2_tests: PIPE_FRAME and PIPE_FRAME_S3PLANT against the parent's PIPE_COMPACT online loop "
             "through extract128 on planted targets, on the selected- and the lift-keyed folded index)"),
            ("every IC process (arm.py): the parent's per-process gates (index canonicalizer lift, 0 planted index "
             "checks, the full scan self-test, the round-2 index_build_pipeline on both binaries, its base's frozen "
             "base hash, columns, orbits, states, slots, root entries, index and LAYOUT digests); and the arm's "
             "online solve in the target record and the summary (absent on the row's binary), with online counters "
             "absent (row), all zero (s3), exactly one frame and no planted check (frame), or exactly one frame "
             "and at least one state and candidate compared (frame_s3plant)"),
            "per point: one scalar across every IC process (both binaries, cold and rank) and rT, replayed as [d]G = Q in the pinned oracle",
            ("per point and base, across every IC process of both binaries and every online solve: one relation "
             "(point indices, x codes and pinned intermediates), one probe count, one root-call count and one "
             "relation-check count"),
            "per base (K600, M38 and M10): one index and layout digest set across both binaries, equal to the frozen one",
            ("Q0 (O1): cPIC and cPOF give B's archived identity (1,987,852 probes); cM38IC, cM38OF and cM38OFX, and "
             "cM10IC and cM10OF, give their closure base's frozen identity"),
            ("rank arms: full rank, 0 failed attempts, one frame per attempt (the rank stage's own counters, read "
             "before the online scan), and the written factor-log table equal to the base's frozen verified table"),
            ("per M38 rank seed: rank_relations_blake3, the per-attempt probe vector, root calls and point-addition "
             "counters identical across every kM38IC, kM38OF and kM38OFaa process with that seed"),
            ("probe law: kM38IC's pooled probes per relation over its %d distinct seeds (%d attempts) over "
             "r / (166 E) inside [0.80, 1.20]" % (POINTS * K, POINTS * K * 16)),
        ],
        "statistics": {
            "e2e_per_side": parent["statistics"]["e2e_per_side"],
            "primary": ("R = sum over the %d primary pairs of E2E(A) / sum over the same pairs of E2E(B). 95%% "
                        "percentile interval from a two-stage paired bootstrap, %d draws, random.Random(%d): the "
                        "points drawn with replacement, then each drawn point's pairs drawn with replacement; A and "
                        "B of a pair are always drawn together" % (POINTS * K, DRAWS, BOOT_SEED)),
            "primary_is": ("the paired END-TO-END ratio over the current row; every stage ratio is co-reported and "
                           "never decides. The design resolves the expected end-to-end effect (power.json); the "
                           "online stage is therefore NOT the primary"),
            "stage_secondary": ("ONLINE STAGE ratio, labelled a stage secondary: online_ms of cM38IC over cM38OF in "
                                "the primary pairs, same bootstrap; also the same-binary layout ratio cM38OS / "
                                "cM38OF online over the layout pairs (pairs resampled)"),
            "pairing_basis": parent["statistics"]["pairing_basis"],
            "secondary": [
                "geometric mean of the per-pair ratios E2E(A)/E2E(B), with the same bootstrap",
                "cold, setup, index build, scan self-test and online cM38IC / cM38OF, paired (all but online expected about 1)",
                "rank stage kM38IC / kM38OF, paired (expected about 1: the same rank work)",
                "online ns per probe per arm; online in the rank processes kM38IC / kM38OF",
                "E2E process CPU time and process wall A / B, with the same bootstrap",
                "peak RSS and minor faults of the cold processes",
                "per-point ratio, and the ratio by pair position and by side order",
                "online counters (resolved hits, swapped pairs, fallback states, planted checks)",
                "probe law of kM38IC and kM38OF; rho ms/step from rT; S per side; E2E cold and online gaps IC / rT",
            ],
        },
        "controls_pass_rule": {
            "aa": ("over the %d A/A pairs: E2E(B) / E2E(Baa) and cold cM38OF / cM38OFaa, the same ratio of sums, "
                   "point estimates both inside [0.97, 1.03]" % (POINTS * K_AA)),
            "planted": ("ONLINE cM38OFX / cM38OF over the %d planted pairs, 95%% bootstrap lower bound (pairs "
                        "resampled, 10,000 draws) above 1; every cM38OFX must also compare at least one state and "
                        "candidate with the S3 loop and pass every per-point identity gate" % (POINTS * K_PLANTED)),
            "planted_exactness": ("the three planted corruptions rejected by verify_closure.py on both closure bases "
                                  "before timing; the crate tests passing; and frame_s3plant's in-process comparison "
                                  "(a panic on any difference) in every cM38OFX process, including Q0"),
            "otherwise": "verdict invalid",
        },
        "decision_rule": {
            "improvement": ("R lower bound > 1: a qualified Tier 1 end-to-end speedup of the online-frame producer "
                            "over the row (a pipeline improvement)"),
            "regression": "R upper bound < 1",
            "not_separated": ("otherwise; the online stage secondary is then reported as a labelled stage result "
                              "only, never as a pipeline improvement"),
            "invalid": "any gate or control fails or is unknown, or any scheduled row is missing (time-guard skips included)",
        },
        "multiplicity": "one primary statistic; every secondary is descriptive and never changes the verdict",
        "exactness_argument": {
            "parent": parent["exactness_argument"],
            "onlineframe2": (
                "E is defined over F_2, so phi(x, y) = (x^2, y^2) is a group automorphism and T +- phi^s(R) = "
                "phi^s(phi^(-s)(T) +- R). The two roots of S3(x(phi^s R), x(T), X) are exactly x(T + phi^s R) and "
                "x(T - phi^s R). The frame loop (PIPE_FRAME, the rank stage's own loop since the rank-probe "
                "producer, already run on the M38 closure index by the row's rank stage) computes these two field "
                "elements by point addition from the stored root's (x, y), with one batched inversion per state, "
                "and applies phi^s as a rotation of the normal-basis word, so each candidate's partner words, "
                "canonical keys and shifts are the S3 loop's, possibly in the other order, at the same probe "
                "positions. Exceptional inputs (x(R_k) = x(T_s), x(R_k) = 0, x(T_s) = 0, roots failing the curve "
                "check) go to the S3 solver. At a hit the frame loop solves that candidate's S3 input and evaluates "
                "the pair in the S3 order, so the first lifted relation, its probe count, the root calls and the "
                "relation checks are the S3 loop's. KIC_ONLINE_SOLVE is read only by the online scan; setup, the "
                "root index, the self-test and the rank stage are the parent's bytes (check_inverse), so the "
                "layout digests, rank tables and rank-seed identities are the parent's. Checked by the crate "
                "tests, locally (inputs/local_exactness.json) and per process and per point in the run, with "
                "frame_s3plant comparing every reached state."),
        },
        "evidence_change": ("none: every process still runs the full exhaustive scan self-test, builds, checks and "
                            "digests its own index, and verifies the recovered scalar; the online scan's output is "
                            "gated identical across both binaries and all three online solves"),
        "power": {"file": "analysis/power.json", "min_delta": power["min_delta"],
                  "power_at_min_delta": power["power_at_min_delta"],
                  "rejection_rate_at_no_effect": power["type_i_at_1.00"],
                  "modelled": power["cells"]["modelled"],
                  "archived_onlineframe": power["cells"]["archived_onlineframe"],
                  "candidate_model": power["candidate_model"],
                  "expected_ratio_at_prior_means": power["expected_ratio_at_prior_means"],
                  "aa_control": power["aa_control"], "law_gate": power["law_gate"],
                  "planted_control": power["planted_control"]},
        "local_diagnostics": {"exactness": "inputs/local_exactness.json",
                              "label": "cloud-agent VM, shared; correctness only, no timing evidence",
                              "summary": exactness and exactness.get("summary")},
        "bootstrap": {"draws": DRAWS, "seed": BOOT_SEED},
    }
    (HERE / "protocol.json").write_text(json.dumps(protocol, indent=1, sort_keys=True) + "\n")
    print(str(HERE / "protocol.json"))


if __name__ == "__main__":
    main()
