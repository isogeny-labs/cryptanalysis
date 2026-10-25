#!/usr/bin/env python3
"""Write the frozen protocol (`protocol.json`) of the round-2 n=83 index-build experiment.

Run once, before any timing, after `restore.py --no-pin-check` (which derives
both producers, regenerates the closure headers and checks every parent
digest), `make_targets.py`, `check_panel_disjoint.py`, `check_seed_disjoint.py`,
`profile/summarize2.py`, `make_power_prior.py` and `power_check.py`.
`restore.py` re-checks every digest this file records. `--draft` writes a
protocol without the power and profile fields, for the local exactness runs
before the power check; it is never the frozen protocol.

The bases, side A's arms (the current row, the parent's index-build
producer) and the per-process gates are the parent's
(`koblitz-n83-indexbuild-20261020`, PR #1006), read from its frozen
`protocol.json` (SHA-256 pinned in `restore.py`). Side B's arms are the same
configurations on the round-2 producer `ic_online_indexbuild2_r770`
(`make_indexbuild2_source.py`). The design, pairing, bootstrap, A/A control,
Tier 1 records and fail-closed verifier are the parent's, which follow the
Tier 1 template (`koblitz-n83-closure-indexlift-rep-20261020`, PR #1002).
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
SEED0 = 1500     # rank seed of pair j at point i: SEED0 + 3 i + j (1501 .. 1536)
ORDER_SEED0 = 2026102070
RHO_SEED_BASE = 1040000
DRAWS = 10000
BOOT_SEED = 20261040
NEW_BINARY = "ic_online_indexbuild2_r770"
PARENT_ARMS = ("cPIB", "cM10IB", "cM38IB", "kM38IB", "rT")
DEADLINE_MIN = 165


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def derived_arm(parent_arm, role, **override):
    arm = dict(parent_arm, binary=NEW_BINARY, index_build_pipeline=PIPELINE, role=role)
    arm.update(override)
    return arm


def main():
    global PIPELINE
    import restore  # noqa: E402  (this directory)
    import make_indexbuild2_source as derivation  # noqa: E402

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--draft", action="store_true")
    args = parser.parse_args()
    PIPELINE = derivation.PIPELINE
    parent = restore.parent_protocol()
    if args.draft:
        power = {"expected_ratio_at_prior_means": 0.0, "expected_cold_ratio_at_prior_means": 0.0,
                 "expected_index_build_ratio": 0.0, "design": {"points": POINTS, "primary_pairs_per_point": K,
                                                               "aa_pairs_per_point": K_AA,
                                                               "planted_pairs_per_point": K_PLANTED},
                 "runtime": {"job_total_min": 0, "schedule_min": 0, "job_total_min_on_a_1.5x_slower_host": 0,
                             "job_limit_min": 0}, "min_delta": None, "power_at_min_delta": None,
                 "type_i_at_1.00": None, "cells": {"modelled": None}, "aa_control": None, "law_gate": None,
                 "planted_control": None}
        profile = {"breakdown_median_ms": {"index_build_total_ms": None}}
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
        spec["parent_source"] = ("koblitz-n83-indexbuild-20261020 protocol.json online.bases.%s "
                                 "(sha256 %s), verbatim" % (name, restore.PARENT_PROTOCOL_SHA256))
        bases[name] = spec
    arms = {}
    for name in PARENT_ARMS:
        arms[name] = dict(parent["arms"][name])
        arms[name]["parent_source"] = "the parent's arm %s, verbatim (the current row's producer)" % name
    arms["cPIC"] = derived_arm(parent["arms"]["cPIB"], "Q0 exactness on B's K600 header, round-2 producer")
    arms["cM10IC"] = derived_arm(parent["arms"]["cM10IB"], "Q0 exactness on the M10 closure header, round-2 producer")
    arms["cM38IC"] = derived_arm(parent["arms"]["cM38IB"],
                                 "PRIMARY candidate cold: cM38IB's configuration on the round-2 index-build producer")
    arms["kM38IC"] = derived_arm(parent["arms"]["kM38IB"],
                                 "PRIMARY candidate rank stage: kM38IB's configuration on the round-2 producer")
    arms["cM38ICaa"] = dict(arms["cM38IC"], role="A/A copy of cM38IC")
    arms["kM38ICaa"] = dict(arms["kM38IC"], role="A/A copy of kM38IC")
    arms["cM38ICX"] = derived_arm(parent["arms"]["cM38IBX"], (
        "PLANTED timing and exactness control: cM38IC with KIC_INDEX_CANON=lift_plant: every index key from the "
        "linear run finder is also checked against lift_scan and the selected canonicalizer (2 x stored states "
        "checks); same layout digests, slower index build"))
    source_of = {"cPIC": "cPIB", "cM10IC": "cM10IB", "cM38ICX": "cM38IBX"}
    for name in arms:
        if name not in PARENT_ARMS:
            arms[name]["derived_from"] = "the parent's arm %s with binary %s" % (
                source_of.get(name, "kM38IB" if name.startswith("k") else "cM38IB"), NEW_BINARY)
    rank_seeds = {"s%03d" % i: [SEED0 + 3 * i + j for j in range(1, K + 1)] for i in range(POINTS)}
    protocol = {
        "schema": 1,
        "kind": "n83-indexbuild2-paired-e2e-tier1",
        "frozen_before_any_timing": True,
        "draft_not_frozen": bool(args.draft),
        "frozen_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "question": ("Is the round-2 index-build producer's END-TO-END cold cost (setup + index build + rank stage + "
                     "linear algebra + one-target online) on the M38 closure base lower than the current n=83 a=1 "
                     "row's (the index-build producer of koblitz-n83-indexbuild-20261020), on new held-out points and "
                     "new rank seeds? The round-2 producer builds the same root index (the same stored states, slot "
                     "words, relations and probes) with seven field products per state instead of eleven (C9) and "
                     "the index keys from the linear run finder, eight roots at a time (C7); the self-test, its "
                     "coverage and every other stage are the parent's. The test uses repeated alternating pairs and "
                     "a 95% paired confidence interval whose lower bound must exceed 1 (AGENTS.md, 'CPU performance "
                     "isolation gate', Tier 1)."),
        "why_this_run": ("On the parent's run 39383739494 (PR #1006) its side B (this experiment's side A) spent "
                         "7.25 of its 14.21 s end to end in the index build, 1.53 s in the scan self-test and 4.43 s "
                         "in the rank stage. A local profile (inputs/local_profile.json, diagnostic) splits the "
                         "remaining build into the state loop's field arithmetic and the insert loop, whose "
                         "lift_scan canonicalization is not hidden behind the prefetched inserts."),
        "success_criterion": "AGENTS.md 'Success criterion: iterative improvement of the index-calculus baseline'",
        "tier_rule": ("AGENTS.md 'CPU performance evidence tiers', Tier 1: same pinned exposed CPU, same workload and "
                      "limits; code and workload hashes, paired order, raw failures, correctness, process CPU time, "
                      "memory, cgroup throttling and memory failures, steal time and scheduling counters recorded; "
                      "repeated alternating pairs and a 95% paired confidence interval whose lower bound exceeds 1"),
        "baseline_row": {"experiment": "koblitz-n83-indexbuild-20261020", "pr": 1006, "merge": "f0c5f8857",
                         "producer_sha256": parent["sources"]["indexbuild_source_sha256"],
                         "binary": "ic_online_indexbuild_r770",
                         "tier1_qualification": {"run": "https://github.com/aburan28/cryptanalysis/actions/runs/39383739494",
                                                 "primary": "1.7406 [1.7129, 1.7676] over the closure + index-lift row"},
                         "parent_protocol_sha256": restore.PARENT_PROTOCOL_SHA256},
        "template": {"experiment": "koblitz-n83-indexbuild-20261020", "pr": 1006,
                     "tier1_template_of_the_parent": "koblitz-n83-closure-indexlift-rep-20261020 (PR #1002)",
                     "copied_verbatim": sorted(restore.TEMPLATE)},
        "expected_effect": ("about %.3f end to end, %.3f cold and %.3f on the index build at the parent run's side-B "
                            "means and the local factor (power_check.py; an estimate, not a claim)" % (
                                power["expected_ratio_at_prior_means"], power["expected_cold_ratio_at_prior_means"],
                                power["expected_index_build_ratio"])),
        "sources": {
            "crypto_770f6a69": parent["sources"]["crypto_770f6a69"],
            "rankprobe_producer": parent["sources"]["rankprobe_producer"],
            "indexlift_producer": parent["sources"]["indexlift_producer"],
            "closure_producer": parent["sources"]["closure_producer"],
            "composition": parent["sources"]["composition"],
            "grandparent_source_sha256": sha256(restore.DERIVED_GRANDPARENT),
            "online_source_sha256": sha256(restore.DERIVED),
            "online_source_sha256_parent": parent["sources"]["indexbuild_source_sha256"],
            "indexbuild2_source_sha256": sha256(restore.DERIVED_B),
            "indexbuild2_derivation": ("make_indexbuild2_source.py: %d counted replacements (%s) on the row's "
                                       "producer text; check_inverse() undoes them to the parent's bytes on every "
                                       "derivation" % (len(derivation.EDITS), ", ".join(e[0] for e in derivation.EDITS))),
            "indexbuild2_pipeline": PIPELINE,
            "parent_pipeline": parent["sources"]["indexbuild_pipeline"],
            "parent_protocol_sha256": restore.PARENT_PROTOCOL_SHA256,
            "verbatim_from_parent": list(restore.VERBATIM),
            "verbatim_from_template": dict(restore.TEMPLATE),
            "changed_from_parent": {
                "online/Cargo.toml": ("[[bin]] ic_online_closure_indexlift_r770 removed (still derived, no longer "
                                      "an arm), [[bin]] ic_online_indexbuild2_r770 added (same lock, same "
                                      "dependencies)"),
                "verify_receipt.py, test_verify_receipt.py": "the arm names and binaries of this experiment",
                "restore.py": "one more derivation step and the parent's pins",
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
                                  "(make_targets.py EARLIER_ROLES, including the parent's indexbuild-cold-v1; "
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
            "sides": {"A": ["kM38IB", "cM38IB"], "B": ["kM38IC", "cM38IC"], "Baa": ["kM38ICaa", "cM38ICaa"]},
            "planted_arms": ["cM38IC", "cM38ICX"],
            "side_rule": parent["design"]["side_rule"],
            "pair_rule": parent["design"]["pair_rule"],
            "rank_stage_design": ("same rank seed per pair, not a shared rank stage: each side runs its own rank "
                                  "process on its own binary. The round-2 change touches only how the index is "
                                  "computed, so the rank stage's work is the same in both (gated: identical "
                                  "relation digests, probe vectors, root calls and counters per seed across kM38IB, "
                                  "kM38IC and kM38ICaa); timing it on each side keeps any code-layout effect of the "
                                  "new binary on the rank loop inside E2E instead of assuming it away"),
            "aa_rule": parent["design"]["aa_rule"],
            "planted_rule": ("a planted pair is cM38IC and cM38ICX, cold processes only, alternating, with the start "
                             "drawn from the same generator"),
            "rho_rule": parent["design"]["rho_rule"],
            "segment_rule": ("O1: Q0 on cPIB, cPIC, cM10IB, cM10IC, cM38IB and cM38IC, shuffled by "
                             "random.Random(ORDER_SEED0 + 99). Then one segment P<i> per point i = 1..POINTS in "
                             "panel order. Its four sub-blocks (primary, aa, planted, rho) run in an order shuffled "
                             "by the point's generator"),
            "order_seed0": ORDER_SEED0,
            "rank_seed0": SEED0,
            "rank_seeds": rank_seeds,
            "rank_seeds_note": ("1501-1536 are new on n=83 (inputs/seed_disjointness.json: every n83 schedule and "
                                "protocol on origin/main, every origin n83 branch and the scratch worktrees; the "
                                "positive control finds the parent's 1401-1436)"),
            "rho_seed_base": RHO_SEED_BASE,
            "q0_point": parent["design"]["q0_point"],
            "q0_arms": ["cPIB", "cPIC", "cM10IB", "cM10IC", "cM38IB", "cM38IC"],
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
            "placement: every process's Cpus_allowed_list, read from /proc while it ran, is the one execution CPU",
            ("host identity: the CPU record (scripts/host_cpu_record.py) at the start and the end of the schedule has "
             "the same model, microcode and flags"),
            ("before any timing: check_log_table.py (verbatim). B's table is re-verified in the pinned oracle. Both "
             "closure headers are regenerated to their frozen SHA-256 and pass verify_closure.py, and the three "
             "planted corruptions are rejected. Each closure table passes [L_c]G = R_c and [w L_c]G = alpha(R_c), "
             "and the closure logs equal B's archived logs. The online crate's tests pass, including "
             "indexbuild2_tests (the round-2 state loop and lane keys against the parent's loops, verbatim; the "
             "linear run finder against the full scan on every word of 3..20 bits and lift_scan on two-limb "
             "geometries and 2^22 + structured 83-bit words) and the parent's indexbuild_tests"),
            ("every IC process (arm.py, verbatim): KIC_INDEX_CANON as the arm (lift; lift_plant in cM38ICX only); "
             "index roots checked against the selected canonicalizer 0 times, or 2 x stored states in cM38ICX; the "
             "full scan self-test; the arm's index_build_pipeline (the parent's on side A, this one on side B); its "
             "base's frozen base hash, columns, orbits, states, slots, root entries, logical-state and table-map "
             "digests; and its base's frozen LAYOUT digests (stored_states_blake3, table_slots_blake3)"),
            "per point: one scalar across every IC process (both binaries, cold and rank) and rT, replayed as [d]G = Q in the pinned oracle",
            "per point and base: one relation and one probe count across every IC process of both binaries",
            "per base (K600, M38 and M10): one index and layout digest set across both binaries, equal to the frozen one",
            ("Q0 (O1): cPIB and cPIC give B's archived identity (1,987,852 probes); cM38IB and cM38IC, and cM10IB and "
             "cM10IC, give their closure base's frozen identity"),
            ("rank arms: full rank, 0 failed attempts, one frame per attempt, and the written factor-log table equal "
             "to the base's frozen verified table, log for log"),
            ("per M38 rank seed: rank_relations_blake3, the per-attempt probe vector, root calls and point-addition "
             "counters identical across every kM38IB, kM38IC and kM38ICaa process with that seed"),
            ("probe law: kM38IB's pooled probes per relation over its %d distinct seeds (%d attempts) over "
             "r / (166 E) inside [0.80, 1.20]" % (POINTS * K, POINTS * K * 16)),
        ],
        "statistics": {
            "e2e_per_side": parent["statistics"]["e2e_per_side"],
            "primary": ("R = sum over the %d primary pairs of E2E(A) / sum over the same pairs of E2E(B). 95%% "
                        "percentile interval from a two-stage paired bootstrap, %d draws, random.Random(%d): the "
                        "points drawn with replacement, then each drawn point's pairs drawn with replacement; A and "
                        "B of a pair are always drawn together" % (POINTS * K, DRAWS, BOOT_SEED)),
            "primary_is": "the paired END-TO-END ratio over the current row; every stage ratio is co-reported and never decides",
            "stage_secondary": ("INDEX-BUILD STAGE ratio, labelled a stage secondary: timing_ms.index_build of cM38IB "
                                "over cM38IC in the primary pairs, same bootstrap; also over the rank processes"),
            "pairing_basis": parent["statistics"]["pairing_basis"],
            "secondary": [
                "geometric mean of the per-pair ratios E2E(A)/E2E(B), with the same bootstrap",
                "cold, setup, index build (stage secondary), scan self-test and online cM38IB / cM38IC, paired",
                "rank stage kM38IB / kM38IC, paired (expected about 1: the same rank work)",
                "index build in the rank processes kM38IB / kM38IC, paired",
                "E2E process CPU time and process wall A / B, with the same bootstrap",
                "peak RSS and minor faults of the cold processes",
                "per-point ratio, and the ratio by pair position and by side order",
                "probe law of kM38IB and kM38IC; rho ms/step from rT; S per side; E2E cold gap IC / rT",
            ],
        },
        "controls_pass_rule": {
            "aa": ("over the %d A/A pairs: E2E(B) / E2E(Baa) and cold cM38IC / cM38ICaa, the same ratio of sums, "
                   "point estimates both inside [0.97, 1.03]" % (POINTS * K_AA)),
            "planted": ("index build cM38ICX / cM38IC over the %d planted pairs, 95%% bootstrap lower bound (pairs "
                        "resampled, 10,000 draws) above 1; every cM38ICX must also reproduce the frozen layout "
                        "digests and check 2 x stored states roots" % (POINTS * K_PLANTED)),
            "planted_exactness": ("the three planted corruptions rejected by verify_closure.py on both closure bases "
                                  "before timing, and the crate tests (the parent's planted non-bijections) passing"),
            "otherwise": "verdict invalid",
        },
        "decision_rule": {
            "improvement": "R lower bound > 1: a qualified Tier 1 end-to-end speedup of the round-2 producer over the row",
            "regression": "R upper bound < 1",
            "not_separated": "otherwise",
            "invalid": "any gate or control fails or is unknown, or any scheduled row is missing (time-guard skips included)",
        },
        "multiplicity": "one primary statistic; every secondary is descriptive and never changes the verdict",
        "exactness_argument": {
            "parent": parent["exactness_argument"],
            "indexbuild2": (
                "The round-2 producer differs from the row's in two computations, neither of which changes a value. "
                "(C9) State loop: for a regular state (l != r, l != 0, r != 0; exactly the states whose parent "
                "denominator a*ps is non-zero, since squaring is injective and GF(2^83) has no zero divisors) the "
                "parent computes a = (l+r)^2, p = l r, ps = p^2, c = ps + b, inv = (a ps)^-1, q = p (ps inv) = p/a "
                "and d = (c a)(a inv) = c a/ps. The round-2 loop computes q = p ((l+r)^-1)^2 and d = c (l^-1 + "
                "r^-1)^2, the same field elements because a/ps = ((l+r)/(l r))^2 = (1/l + 1/r)^2. Every inverse is a "
                "field inverse (1/l and 1/r: the inverse of a representative squared k times is the inverse of its "
                "k-th Frobenius shift, each checked by a product at build time; 1/(l+r): Montgomery's trick over "
                "four interleaved chains, the inverse of a non-zero element being unique), and field elements have "
                "one reduced representation, so q and d are bit for bit the parent's; the trace test, the half "
                "trace, the root order and the to_normal images then are the parent's. An irregular state takes "
                "s3_x_roots_128(gf, b, l, r), which is what the parent's finish returns for a zero denominator. "
                "States are pushed in the parent's (left, right, relative) order, so stored_states_blake3 is the "
                "parent's. (C7) Insert loop: for a nonconstant 83-bit word v, z_1 = !v and z_(j+1) = z_j & "
                "rotl(z_j, 1) has bit p set iff bits p..p-j are zero (cyclically), so the last nonzero z_j is Z_L "
                "(L the longest zero run), the tops of all longest zero runs, which is the run set lift_scan's "
                "greedy lifting ends with (lift2/src/lib.rs). The candidate rotations s = N-1-p and the choice "
                "(least rotation, ties to the smaller shift, an order-independent minimum) are lift_scan's, and 0 "
                "and the all-ones word return shift 0 as in lift_scan; so the key and shift equal lift_scan's for "
                "every word. In the eight-lane form a lane that reaches its Z_L keeps it by a select while the "
                "other lanes continue; the word 0 starts at z = 0. Keys are computed once per root in increasing "
                "root order (eight at a time, the tail one at a time by the parent's call), the planted counter is "
                "incremented once per root in lift_plant, the prefetch is a hint, and insert_if_absent receives the "
                "parent's (key, value) sequence, so every slot word, and table_slots_blake3, is the parent's. "
                "Relations, probes, the rank stage and the online scan read only the index and the self-test "
                "verdict, so they are the parent's. Checked locally on every stored root of K600, M38 and M10 "
                "(inputs/local_exactness.json) and gated per process and per base in the run."),
        },
        "evidence_change": ("none: every process still runs the full exhaustive scan self-test (the parent's "
                            "eight-image loop, unchanged) on its own state count and both keys, and still builds, "
                            "checks and digests its own index. No sampled check is used."),
        "rejected_candidates": "README section 2: C6 (bucketed insert), C8 (carry-less multiply codegen), S3 (branch-free self-test)",
        "power": {"file": "analysis/power.json", "min_delta": power["min_delta"],
                  "power_at_min_delta": power["power_at_min_delta"],
                  "rejection_rate_at_no_effect": power["type_i_at_1.00"],
                  "modelled": power["cells"]["modelled"],
                  "expected_ratio_at_prior_means": power["expected_ratio_at_prior_means"],
                  "aa_control": power["aa_control"], "law_gate": power["law_gate"],
                  "planted_control": power["planted_control"]},
        "local_diagnostics": {"profile": "inputs/local_profile.json", "exactness": "inputs/local_exactness.json",
                              "label": "cloud-agent VM, shared; correctness and candidate ranking only",
                              "profile_index_build_ms": profile["breakdown_median_ms"]["index_build_total_ms"]},
        "bootstrap": {"draws": DRAWS, "seed": BOOT_SEED},
    }
    (HERE / "protocol.json").write_text(json.dumps(protocol, indent=1, sort_keys=True) + "\n")
    print(str(HERE / "protocol.json"))


if __name__ == "__main__":
    main()
