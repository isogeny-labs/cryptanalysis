#!/usr/bin/env python3
"""Write the frozen protocol (`protocol.json`) of the n=83 rank-finder experiment.

Run once, before any timing, after `restore.py --no-pin-check` (which derives
both producers, regenerates the closure headers and checks every parent
digest), `make_targets.py`, `check_panel_disjoint.py`, `check_seed_disjoint.py`,
`profile/summarize.py`, `make_power_prior.py` and `power_check.py`.
`restore.py` re-checks every digest this file records. `--draft` writes a
protocol without the power and profile fields, for local runs before the
power check; it is never the frozen protocol.

The bases, side A's arms (the current row, the parent's round-2 index-build
producer) and the per-process gates are the parent's
(`koblitz-n83-indexbuild2-20261020`, PR #1009), read from its frozen
`protocol.json` (SHA-256 pinned in `restore.py`). Side B's arms are the same
configurations on the rank-finder producer `ic_online_rankfinder_r770`
(`make_rankfinder_source.py`). The design, pairing, bootstrap, A/A control,
Tier 1 records and fail-closed verifier are the parent's, which follow the
Tier 1 template (`koblitz-n83-closure-indexlift-rep-20261020`, PR #1002).
The planted control moves to the changed stage: a planted pair is two RANK
processes, kM38RF and kM38RFX (KIC_RANK_SOLVE=frame_plant: every linear key
is recomputed by the rank-cut loop with lift_scan and compared).
"""

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
POINTS = 12
K = 3            # alternating primary pairs per point
K_AA = 2         # alternating A/A pairs per point
K_PLANTED = 1    # alternating planted pairs per point
SEED0 = 1800     # rank seed of pair j at point i: SEED0 + 3 i + j (1801 .. 1836)
ORDER_SEED0 = 2026102170
RHO_SEED_BASE = 1050000
DRAWS = 10000
BOOT_SEED = 20261050
NEW_BINARY = "ic_online_rankfinder_r770"
PARENT_ARMS = ("cPIC", "cM10IC", "cM38IC", "kM38IC", "rT")
DEADLINE_MIN = 165


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def derived_arm(parent_arm, role, **override):
    arm = dict(parent_arm, binary=NEW_BINARY, rank_probe_pipeline=PIPELINE, role=role)
    arm.pop("parent_source", None)
    arm.update(override)
    return arm


def main():
    global PIPELINE
    import restore  # noqa: E402  (this directory)
    import make_rankfinder_source as derivation  # noqa: E402

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--draft", action="store_true")
    args = parser.parse_args()
    PIPELINE = derivation.PIPELINE
    parent = restore.parent_protocol()
    if args.draft:
        power = {"expected_ratio_at_prior_means": 0.0, "expected_rank_stage_ratio": 0.0, "design": {"points": POINTS, "primary_pairs_per_point": K,
                                                               "aa_pairs_per_point": K_AA,
                                                               "planted_pairs_per_point": K_PLANTED},
                 "runtime": {"job_total_min": 0, "schedule_min": 0, "job_total_min_on_a_1.5x_slower_host": 0,
                             "job_limit_min": 0}, "min_delta": None, "power_at_min_delta": None,
                 "type_i_at_1.00": None, "cells": {"modelled": None}, "aa_control": None, "law_gate": None,
                 "planted_control": None}
        profile = {"modelled": {"rank_stage_factor": None}}
    else:
        power = json.loads((HERE / "analysis" / "power.json").read_text())
        profile = json.loads((HERE / "inputs" / "local_profile.json").read_text())
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
        spec["parent_source"] = ("koblitz-n83-indexbuild2-20261020 protocol.json online.bases.%s "
                                 "(sha256 %s), verbatim" % (name, restore.PARENT_PROTOCOL_SHA256))
        bases[name] = spec
    arms = {}
    for name in PARENT_ARMS:
        arms[name] = dict(parent["arms"][name])
        arms[name]["parent_source"] = "the parent's arm %s, verbatim (the current row's producer)" % name
    arms["cPRF"] = derived_arm(parent["arms"]["cPIC"], "Q0 exactness on B's K600 header, rank-finder producer")
    arms["cM10RF"] = derived_arm(parent["arms"]["cM10IC"], "Q0 exactness on the M10 closure header, rank-finder producer")
    arms["cM38RF"] = derived_arm(parent["arms"]["cM38IC"],
                                 "PRIMARY candidate cold: cM38IC's configuration on the rank-finder producer")
    arms["kM38RF"] = derived_arm(parent["arms"]["kM38IC"],
                                 "PRIMARY candidate rank stage: kM38IC's configuration on the rank-finder producer")
    arms["cM38RFaa"] = dict(arms["cM38RF"], role="A/A copy of cM38RF")
    arms["kM38RFaa"] = dict(arms["kM38RF"], role="A/A copy of kM38RF")
    arms["kM38RFX"] = derived_arm(parent["arms"]["kM38IC"], (
        "PLANTED timing and exactness control: kM38RF with KIC_RANK_SOLVE=frame_plant: every rank-stage key from "
        "the linear run finder is recomputed by the rank-cut loop with lift_scan and compared key by key "
        "(rank_frame_plant_checked_inputs > 0); same relations and tables, slower rank stage"),
        rank_solve="frame_plant")
    source_of = {"cPRF": "cPIC", "cM10RF": "cM10IC"}
    for name in arms:
        if name not in PARENT_ARMS:
            arms[name]["derived_from"] = "the parent's arm %s with binary %s" % (
                source_of.get(name, "kM38IC" if name.startswith("k") else "cM38IC"), NEW_BINARY)
            if name == "kM38RFX":
                arms[name]["derived_from"] += " and rank_solve frame_plant"
    rank_seeds = {"s%03d" % i: [SEED0 + 3 * i + j for j in range(1, K + 1)] for i in range(POINTS)}
    protocol = {
        "schema": 1,
        "kind": "n83-rankfinder-paired-e2e-tier1",
        "frozen_before_any_timing": True,
        "draft_not_frozen": bool(args.draft),
        "frozen_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "question": ("Is the rank-finder producer's END-TO-END cold cost (setup + index build + rank stage + "
                     "linear algebra + one-target online) on the M38 closure base lower than the current n=83 a=1 "
                     "row's (the round-2 index-build producer of koblitz-n83-indexbuild2-20261020), on new "
                     "held-out points and new rank seeds? The rank-finder producer computes the rank stage's "
                     "probe keys (the frame loop, KIC_RANK_SOLVE=frame) with round 2's proven linear run finder "
                     "(C7), eight keys at a time, instead of lift_scan per key; every key, probe, relation, root "
                     "call, counter and rank table is the parent's, and every other stage is the parent's code. "
                     "The test uses repeated alternating pairs and a 95% paired confidence interval whose lower "
                     "bound must exceed 1 (AGENTS.md, 'CPU performance isolation gate', Tier 1)."),
        "why_this_run": ("On the parent's run 39464544962 (PR #1009) its side B (this experiment's side A) spent "
                         "4.22 of its 11.54 s end to end in the rank stage (36.5%). A local profile "
                         "(inputs/local_profile.json, diagnostic) puts about 66% of the rank stage in the frame "
                         "loop's key derivation, of which lift_scan alone is about 44 ns per key, and the linear "
                         "run finder about 27 ns per key; the parent's README names this as the follow-up of C7."),
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
                         "ratchet_rule": ("if another PR replaces the n=83 row before this one lands, this result "
                                          "is recorded as an improvement over the row it measured (this one), "
                                          "and a combined run follows")},
        "template": {"experiment": "koblitz-n83-indexbuild2-20261020", "pr": 1009,
                     "tier1_template_of_the_parent": "koblitz-n83-closure-indexlift-rep-20261020 (PR #1002)",
                     "copied_verbatim": sorted(restore.TEMPLATE)},
        "expected_effect": ("about %.3f end to end and %.3f on the rank stage at the parent run's side-B means and "
                            "the local factor (power_check.py; an estimate, not a claim)" % (
                                power["expected_ratio_at_prior_means"], power["expected_rank_stage_ratio"])),
        "sources": {
            "crypto_770f6a69": parent["sources"]["crypto_770f6a69"],
            "rankprobe_producer": parent["sources"]["rankprobe_producer"],
            "indexlift_producer": parent["sources"]["indexlift_producer"],
            "closure_producer": parent["sources"]["closure_producer"],
            "composition": parent["sources"]["composition"],
            "grandparent_source_sha256": sha256(restore.DERIVED_GRANDPARENT),
            "indexbuild_source_sha256": sha256(restore.DERIVED_IB),
            "online_source_sha256": sha256(restore.DERIVED),
            "online_source_sha256_parent": parent["sources"]["indexbuild2_source_sha256"],
            "rankfinder_source_sha256": sha256(restore.DERIVED_B),
            "rankfinder_derivation": ("make_rankfinder_source.py: %d counted replacements (%s) on the row's "
                                      "producer text; check_inverse() undoes them to the parent's bytes on every "
                                      "derivation" % (len(derivation.edits(derivation.parent_text())),
                                                      ", ".join(e[0] for e in derivation.edits(derivation.parent_text())))),
            "rank_probe_pipeline": PIPELINE,
            "index_build_pipeline": parent["sources"]["indexbuild2_pipeline"],
            "parent_protocol_sha256": restore.PARENT_PROTOCOL_SHA256,
            "verbatim_from_parent": list(restore.VERBATIM),
            "verbatim_from_template": dict(restore.TEMPLATE),
            "changed_from_parent": {
                "online/Cargo.toml": ("[[bin]] ic_online_indexbuild_r770 removed (still derived, no longer an arm), "
                                      "[[bin]] ic_online_rankfinder_r770 added (same lock, same dependencies)"),
                "verify_receipt.py, test_verify_receipt.py": ("the arm names and binaries of this experiment; the "
                                                              "planted ratio on the rank stage; one added gate "
                                                              "(rank_probe_pipeline per row)"),
                "restore.py": "one more derivation step and the parent's pins",
                "make_targets.py, check_seed_disjoint.py": "the new role and seed range",
                "make_power_prior.py, power_check.py": "the prior run and the modelled stage",
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
            "sides": {"A": ["kM38IC", "cM38IC"], "B": ["kM38RF", "cM38RF"], "Baa": ["kM38RFaa", "cM38RFaa"]},
            "planted_arms": ["kM38RF", "kM38RFX"],
            "side_rule": parent["design"]["side_rule"],
            "pair_rule": parent["design"]["pair_rule"],
            "rank_stage_design": ("same rank seed per pair, not a shared rank stage: each side runs its own rank "
                                  "process on its own binary. The change touches only how the rank stage's probe "
                                  "keys are computed, so the rank stage's work is the same in both (gated: "
                                  "identical relation digests, probe vectors, root calls and counters per seed "
                                  "across kM38IC, kM38RF, kM38RFaa and kM38RFX); the cold processes never run the "
                                  "rank stage, and timing them on each side keeps any code-layout effect of the new "
                                  "binary inside E2E instead of assuming it away"),
            "aa_rule": parent["design"]["aa_rule"],
            "planted_rule": ("a planted pair is kM38RF and kM38RFX, RANK processes run by make_schedule.py "
                             "(verbatim) with seed 7 (its planted seed) and the point, alternating, with the start "
                             "drawn from the same generator. Seed 7 is a control seed, the same in every point's "
                             "planted pair, never a primary seed"),
            "rho_rule": parent["design"]["rho_rule"],
            "segment_rule": ("O1: Q0 on cPIC, cPRF, cM10IC, cM10RF, cM38IC and cM38RF, shuffled by "
                             "random.Random(ORDER_SEED0 + 99). Then one segment P<i> per point i = 1..POINTS in "
                             "panel order. Its four sub-blocks (primary, aa, planted, rho) run in an order shuffled "
                             "by the point's generator"),
            "order_seed0": ORDER_SEED0,
            "rank_seed0": SEED0,
            "rank_seeds": rank_seeds,
            "rank_seeds_note": ("1801-1836 are new on n=83 (inputs/seed_disjointness.json: every n83 schedule and "
                                "protocol on origin/main, every origin n83 branch and the scratch worktrees; the "
                                "positive control finds the parent's 1501-1536)"),
            "rho_seed_base": RHO_SEED_BASE,
            "q0_point": parent["design"]["q0_point"],
            "q0_arms": ["cPIC", "cPRF", "cM10IC", "cM10RF", "cM38IC", "cM38RF"],
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
            ("every IC row's summary names its arm's rank_probe_pipeline: absent on side A's binary, "
             "linear_canon_lanes8 on the rank-finder binary"),
            "placement: every process's Cpus_allowed_list, read from /proc while it ran, is the one execution CPU",
            ("host identity: the CPU record (scripts/host_cpu_record.py) at the start and the end of the schedule has "
             "the same model, microcode and flags"),
            ("before any timing: check_log_table.py (verbatim). B's table is re-verified in the pinned oracle. Both "
             "closure headers are regenerated to their frozen SHA-256 and pass verify_closure.py, and the three "
             "planted corruptions are rejected. The online crate's tests pass, including rankfinder_tests (the "
             "derived frame loop against the parent's frame loop, verbatim, on every state of a small folded index "
             "for frame, frame_plant, frame_swapped and full-scan keys; the derived extract against the rank-cut "
             "extract) and the parent's indexbuild2_tests (the linear run finder against the full scan on every "
             "word of 3..20 bits and lift_scan on two-limb geometries and 2^22 + structured 83-bit words)"),
            ("every IC process (arm.py, verbatim): KIC_INDEX_CANON lift; index roots checked 0 times; the full scan "
             "self-test; the arm's index_build_pipeline (the parent's round-2 pipeline on both sides); its base's "
             "frozen base hash, columns, orbits, states, slots, root entries, logical-state and table-map digests; "
             "its base's frozen LAYOUT digests; on rank arms the arm's rank_solve, one frame per attempt, the "
             "planted check run only in kM38RFX and there on > 0 inputs"),
            "per point: one scalar across every IC process (both binaries, cold and rank) and rT, replayed as [d]G = Q in the pinned oracle",
            "per point and base: one relation and one probe count across every IC process of both binaries",
            "per base (K600, M38 and M10): one index and layout digest set across both binaries, equal to the frozen one",
            ("Q0 (O1): cPIC and cPRF give B's archived identity (1,987,852 probes); cM38IC and cM38RF, and cM10IC and "
             "cM10RF, give their closure base's frozen identity"),
            ("rank arms: full rank, 0 failed attempts, one frame per attempt, and the written factor-log table equal "
             "to the base's frozen verified table, log for log"),
            ("per M38 rank seed: rank_relations_blake3, the per-attempt probe vector, root calls and point-addition "
             "counters identical across every kM38IC, kM38RF, kM38RFaa and kM38RFX process with that seed"),
            ("probe law: kM38IC's pooled probes per relation over its %d distinct seeds (%d attempts) over "
             "r / (166 E) inside [0.80, 1.20]" % (POINTS * K, POINTS * K * 16)),
        ],
        "statistics": {
            "e2e_per_side": parent["statistics"]["e2e_per_side"],
            "primary": ("R = sum over the %d primary pairs of E2E(A) / sum over the same pairs of E2E(B). 95%% "
                        "percentile interval from a two-stage paired bootstrap, %d draws, random.Random(%d): the "
                        "points drawn with replacement, then each drawn point's pairs drawn with replacement; A and "
                        "B of a pair are always drawn together" % (POINTS * K, DRAWS, BOOT_SEED)),
            "primary_is": "the paired END-TO-END ratio over the current row; every stage ratio is co-reported and never decides",
            "stage_secondary": ("RANK-STAGE ratio, labelled a stage secondary: timing_ms.rank_stage of kM38IC over "
                                "kM38RF in the primary pairs, same bootstrap"),
            "pairing_basis": parent["statistics"]["pairing_basis"],
            "secondary": [
                "geometric mean of the per-pair ratios E2E(A)/E2E(B), with the same bootstrap",
                "rank stage kM38IC / kM38RF (stage secondary), paired",
                "cold, setup, index build, scan self-test and online cM38IC / cM38RF, paired (expected about 1: the same code)",
                "index build in the rank processes kM38IC / kM38RF, paired",
                "E2E process CPU time and process wall A / B, with the same bootstrap",
                "peak RSS and minor faults of the cold processes",
                "per-point ratio, and the ratio by pair position and by side order",
                "probe law of kM38IC and kM38RF; rank ns per probe; rho ms/step from rT; S per side; E2E cold gap IC / rT",
            ],
        },
        "controls_pass_rule": {
            "aa": ("over the %d A/A pairs: E2E(B) / E2E(Baa) and cold cM38RF / cM38RFaa, the same ratio of sums, "
                   "point estimates both inside [0.97, 1.03]" % (POINTS * K_AA)),
            "planted": ("rank stage kM38RFX / kM38RF over the %d planted pairs, 95%% bootstrap lower bound (pairs "
                        "resampled, 10,000 draws) above 1; every kM38RFX must also check > 0 rank-stage inputs "
                        "against the rank-cut keys and reproduce the frozen rank table" % (POINTS * K_PLANTED)),
            "planted_exactness": ("the three planted corruptions rejected by verify_closure.py on both closure bases "
                                  "before timing, and the crate tests passing"),
            "otherwise": "verdict invalid",
        },
        "decision_rule": {
            "improvement": "R lower bound > 1: a qualified Tier 1 end-to-end speedup of the rank-finder producer over the row",
            "regression": "R upper bound < 1",
            "not_separated": "otherwise",
            "invalid": "any gate or control fails or is unknown, or any scheduled row is missing (time-guard skips included)",
        },
        "multiplicity": "one primary statistic; every secondary is descriptive and never changes the verdict",
        "exactness_argument": {
            "parent": parent["exactness_argument"],
            "rankfinder": (
                "The rank-finder producer differs from the row's in one computation, which does not change a value. "
                "In scan_state128_frame (KIC_RANK_SOLVE=frame and frame_plant, used only by the rank stage) the "
                "parent computes every partner word's key as target_canonical::<CANON_LIFT>, i.e. "
                "lift_scan_wide(v, 83), right after the word. The derived loop pushes the same partner words in the "
                "same order with the same candidate index and pair starts, and whenever eight keys are pending "
                "computes their (canonical, shift) with lift_linear_lanes8::<83>, the parent's own C7 function, "
                "whose result equals lift_scan's for every 83-bit word: for a nonconstant word v, z_1 = !v and "
                "z_(j+1) = z_j & rotl(z_j, 1) has bit p set iff bits p..p-j are zero (cyclically), so the last "
                "nonzero z_j is Z_L, the tops of all longest zero runs, lift_scan's final run set; the candidate "
                "rotations and the order-independent choice (least rotation, ties to the smaller shift) are "
                "lift_scan's; 0 and the all-ones word give shift 0. The at most seven keys left at the end of a "
                "state take the parent's call. Every key is complete before the first lookup, the prefetch is a "
                "hint, and the probe loop is the parent's text, so probe positions, the first hit, the relation, "
                "root calls and every counter are the parent's. For any other canonicalizer or field size the "
                "parent's code runs. Checked by the crate tests against the parent's loop kept verbatim, and "
                "locally per seed on M38, M10 and K600 (inputs/local_exactness.json); gated per seed in the run."),
        },
        "evidence_change": ("none: the rank stage still runs to full rank, writes its table and checks it against the "
                            "frozen verified table; every process still runs the full scan self-test, builds, checks "
                            "and digests its own index. No sampled check is used."),
        "rejected_candidates": "none measured beyond C7; README section 2 lists what is out of scope",
        "power": {"file": "analysis/power.json", "min_delta": power["min_delta"],
                  "power_at_min_delta": power["power_at_min_delta"],
                  "rejection_rate_at_no_effect": power["type_i_at_1.00"],
                  "modelled": power["cells"]["modelled"],
                  "expected_ratio_at_prior_means": power["expected_ratio_at_prior_means"],
                  "aa_control": power["aa_control"], "law_gate": power["law_gate"],
                  "planted_control": power["planted_control"]},
        "local_diagnostics": {"profile": "inputs/local_profile.json", "exactness": "inputs/local_exactness.json",
                              "label": "cloud-agent VM, shared; correctness and sizing only",
                              "modelled_rank_stage_factor": profile["modelled"]["rank_stage_factor"]},
        "bootstrap": {"draws": DRAWS, "seed": BOOT_SEED},
    }
    (HERE / "protocol.json").write_text(json.dumps(protocol, indent=1, sort_keys=True) + "\n")
    print(str(HERE / "protocol.json"))


if __name__ == "__main__":
    main()
