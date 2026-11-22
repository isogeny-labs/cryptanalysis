#!/usr/bin/env python3
"""Write the frozen protocol (`protocol.json`) of the n=83 index-build experiment.

Run once, before any timing, after `restore.py --no-pin-check` (which derives
both producers, regenerates the closure headers and checks every parent
digest), `make_targets.py`, `check_panel_disjoint.py`, `check_seed_disjoint.py`,
`profile/summarize.py`, `make_power_prior.py` and `power_check.py`.
`restore.py` re-checks every digest this file records.

The bases, side A's arms (the row's producer) and the per-process gates are
the parent's (`koblitz-n83-closure-indexlift-20261019`, PR #997), read from
its frozen `protocol.json` (SHA-256 pinned in `restore.py`). Side B's arms are
the same configurations on the derived producer `ic_online_indexbuild_r770`
(`make_indexbuild_source.py`). The design, pairing, bootstrap, A/A control,
Tier 1 records and fail-closed verifier follow the Tier 1 template
(`koblitz-n83-closure-indexlift-rep-20261020`, PR #1002).
"""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
POINTS = 12
K = 3            # alternating primary pairs per point
K_AA = 2         # alternating A/A pairs per point
K_PLANTED = 1    # alternating planted pairs per point
SEED0 = 1400     # rank seed of pair j at point i: SEED0 + 3 i + j (1401 .. 1436)
ORDER_SEED0 = 2026102050
RHO_SEED_BASE = 1030000
DRAWS = 10000
BOOT_SEED = 20261030
NEW_BINARY = "ic_online_indexbuild_r770"
PARENT_ARMS = ("cPI", "cM10I", "cM38I", "kM38I", "rT")
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
    import make_indexbuild_source as derivation  # noqa: E402

    PIPELINE = derivation.PIPELINE
    parent = restore.parent_protocol()
    power = json.loads((HERE / "analysis" / "power.json").read_text())
    profile = json.loads((HERE / "inputs" / "local_profile.json").read_text())
    targets = json.loads((HERE / "inputs" / "cold_targets.json").read_text())
    disjoint = json.loads((HERE / "inputs" / "panel_disjointness.json").read_text())
    seeds_new = json.loads((HERE / "inputs" / "seed_disjointness.json").read_text())
    if disjoint.get("disjoint") is not True or seeds_new.get("new") is not True:
        raise SystemExit("the panel or the rank seeds are not new on n=83")
    if not seeds_new["positive_control"]["finds_template_schedule"]:
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
        spec["parent_source"] = ("koblitz-n83-closure-indexlift-20261019 protocol.json online.bases.%s "
                                 "(sha256 %s), verbatim" % (name, restore.PARENT_PROTOCOL_SHA256))
        bases[name] = spec
    arms = {}
    for name in PARENT_ARMS:
        arms[name] = dict(parent["arms"][name])
        arms[name]["parent_source"] = "the parent's arm %s, verbatim (the row's producer)" % name
    arms["cPIB"] = derived_arm(parent["arms"]["cPI"], "Q0 exactness on B's K600 header, derived producer")
    arms["cM10IB"] = derived_arm(parent["arms"]["cM10I"], "Q0 exactness on the M10 closure header, derived producer")
    arms["cM38IB"] = derived_arm(parent["arms"]["cM38I"],
                                 "PRIMARY candidate cold: cM38I's configuration on the derived index-build producer")
    arms["kM38IB"] = derived_arm(parent["arms"]["kM38I"],
                                 "PRIMARY candidate rank stage: kM38I's configuration on the derived producer")
    arms["cM38IBaa"] = dict(arms["cM38IB"], role="A/A copy of cM38IB")
    arms["kM38IBaa"] = dict(arms["kM38IB"], role="A/A copy of kM38IB")
    arms["cM38IBX"] = derived_arm(parent["arms"]["cM38I"], (
        "PLANTED timing and exactness control: cM38IB with KIC_INDEX_CANON=lift_plant, which also runs the "
        "selected canonicalizer on every index root and asserts it equals lift_scan (2 x stored states checks); "
        "same layout digests, slower index build"), index_canon="lift_plant")
    for name in arms:
        if name not in PARENT_ARMS:
            arms[name]["derived_from"] = "the parent's arm %s with binary %s" % (
                {"cPIB": "cPI", "cM10IB": "cM10I"}.get(name, "kM38I" if name.startswith("k") else "cM38I"),
                NEW_BINARY)
    rank_seeds = {"s%03d" % i: [SEED0 + 3 * i + j for j in range(1, K + 1)] for i in range(POINTS)}
    protocol = {
        "schema": 1,
        "kind": "n83-indexbuild-paired-e2e-tier1",
        "frozen_before_any_timing": True,
        "frozen_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "question": ("Is the derived index-build producer's END-TO-END cold cost (setup + index build + rank stage + "
                     "linear algebra + one-target online) on the M38 closure base lower than the current n=83 a=1 "
                     "row's (the closure + index-lift M38I producer), on new held-out points and new rank seeds? "
                     "The derived producer builds the same root index (the same stored states, slot words, "
                     "relations and probes) with one field inversion per state row and a prefetched look-ahead "
                     "insert loop, and computes the same exhaustive scan self-test eight images at a time. The test "
                     "uses repeated alternating pairs and a 95% paired confidence interval whose lower bound must "
                     "exceed 1 (AGENTS.md, 'CPU performance isolation gate', Tier 1)."),
        "why_this_run": ("On the Tier 1 template run 39359922687 (PR #1002) side B (this experiment's side A) spent "
                         "about 15.6 of its 21.7 s end to end in the index build and 1.7 s in the scan self-test; "
                         "the rank stage is 3.7 s. A local profile (inputs/local_profile.json, diagnostic) puts about "
                         "6.5 s of a 16.9 s build in one field inversion per stored state and about 5.3 s in the "
                         "table insert's cache, TLB and first-touch misses."),
        "success_criterion": "AGENTS.md 'Success criterion: iterative improvement of the index-calculus baseline'",
        "tier_rule": ("AGENTS.md 'CPU performance evidence tiers', Tier 1: same pinned exposed CPU, same workload and "
                      "limits; code and workload hashes, paired order, raw failures, correctness, process CPU time, "
                      "memory, cgroup throttling and memory failures, steal time and scheduling counters recorded; "
                      "repeated alternating pairs and a 95% paired confidence interval whose lower bound exceeds 1"),
        "baseline_row": {"experiment": "koblitz-n83-closure-indexlift-20261019", "pr": 997, "merge": "e55510070",
                         "producer_sha256": parent["sources"]["online_source_sha256"],
                         "tier1_qualification": {"experiment": "koblitz-n83-closure-indexlift-rep-20261020",
                                                 "pr": 1002, "branch_commit": "3f5dfdfa1",
                                                 "run": "https://github.com/aburan28/cryptanalysis/actions/runs/39359922687",
                                                 "primary": "7.4133 [7.1999, 7.6362] over the index-lift row"},
                         "parent_protocol_sha256": restore.PARENT_PROTOCOL_SHA256},
        "template": {"experiment": "koblitz-n83-closure-indexlift-rep-20261020", "pr": 1002,
                     "commit": "3f5dfdfa1",
                     "copied_verbatim": sorted(restore.TEMPLATE)},
        "expected_effect": ("about %.2f end to end, %.2f cold and %.2f on the index build at the template run's means "
                            "and the local profile's factors (power_check.py; an estimate, not a claim)" % (
                                power["expected_ratio_at_prior_means"], power["expected_cold_ratio_at_prior_means"],
                                power["expected_index_build_ratio"])),
        "sources": {
            "crypto_770f6a69": parent["sources"]["crypto_770f6a69"],
            "rankprobe_producer": parent["sources"]["rankprobe_producer"],
            "indexlift_producer": parent["sources"]["indexlift_producer"],
            "closure_producer": parent["sources"]["closure_producer"],
            "composition": parent["sources"]["composition"],
            "online_source_sha256": sha256(restore.DERIVED),
            "online_source_sha256_parent": parent["sources"]["online_source_sha256"],
            "indexbuild_source_sha256": sha256(restore.DERIVED_B),
            "indexbuild_derivation": ("make_indexbuild_source.py: %d counted replacements (%s) on the row's producer "
                                      "text; check_inverse() undoes them to the parent's bytes on every derivation" % (
                                          len(derivation.EDITS), ", ".join(e[0] for e in derivation.EDITS))),
            "indexbuild_pipeline": PIPELINE,
            "parent_protocol_sha256": restore.PARENT_PROTOCOL_SHA256,
            "verbatim_from_parent": list(restore.VERBATIM),
            "verbatim_from_template": dict(restore.TEMPLATE),
            "changed_from_parent": {
                "arm.py": "the index_build_pipeline gate and the planted lift_plant check count",
                "online/Cargo.toml": "one added [[bin]], ic_online_indexbuild_r770 (same lock, same dependencies)",
            },
            "local_sha256": {key: sha256(path) for key, path in restore.local_files().items()},
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
                                  "(make_targets.py EARLIER_ROLES; role-agnostic x/y scan in "
                                  "inputs/panel_disjointness.json, 0 hits)" % (targets["role"], POINTS)),
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
            "sides": {"A": ["kM38I", "cM38I"], "B": ["kM38IB", "cM38IB"], "Baa": ["kM38IBaa", "cM38IBaa"]},
            "planted_arms": ["cM38IB", "cM38IBX"],
            "side_rule": ("a side is two fresh processes run back to back, its rank process and then its cold "
                          "process, both on the pair's point. The rank process runs the rank stage with the pair's "
                          "rank seed (no cached table) and then solves the point; the cold process loads the base's "
                          "verified table and solves the point"),
            "pair_rule": ("a primary pair is one A side and one B side with the same point and the same rank seed. "
                          "Each point's K pairs run as 2K sides in strict alternation, ABAB... or BABA..., and the "
                          "starting side is drawn from random.Random(ORDER_SEED0 + i). Pair j is sides 2j-1 and 2j"),
            "rank_stage_design": ("same rank seed per pair, not a shared rank stage: each side runs its own rank "
                                  "process on its own binary. The index build changes only how the index is "
                                  "computed, so the rank stage's work is the same in both (gated: identical "
                                  "relation digests, probe vectors, root calls and counters per seed across kM38I, "
                                  "kM38IB and kM38IBaa); timing it on each side keeps any code-layout effect of the "
                                  "new binary on the rank loop inside E2E instead of assuming it away"),
            "aa_rule": ("an A/A pair is one B side and one Baa side with the same point and the rank seed of primary "
                        "pair j (j = 1..K_AA). The 2 K_AA sides alternate strictly, with the start drawn from the "
                        "same generator"),
            "planted_rule": ("a planted pair is cM38IB and cM38IBX, cold processes only, alternating, with the start "
                             "drawn from the same generator"),
            "rho_rule": "one rT process per point, seed rho_seed_base + point seed",
            "segment_rule": ("O1: Q0 on cPI, cPIB, cM10I, cM10IB, cM38I and cM38IB, shuffled by "
                             "random.Random(ORDER_SEED0 + 99). Then one segment P<i> per point i = 1..POINTS in "
                             "panel order. Its four sub-blocks (primary, aa, planted, rho) run in an order shuffled "
                             "by the point's generator"),
            "order_seed0": ORDER_SEED0,
            "rank_seed0": SEED0,
            "rank_seeds": rank_seeds,
            "rank_seeds_note": ("1401-1436 are new on n=83 (inputs/seed_disjointness.json: every n83 schedule and "
                                "protocol on origin/main, every origin n83 branch and the scratch worktrees; the "
                                "positive control finds the template's 1201-1230)"),
            "rho_seed_base": RHO_SEED_BASE,
            "q0_point": parent["design"]["q0_point"],
            "q0_arms": ["cPI", "cPIB", "cM10I", "cM10IB", "cM38I", "cM38IB"],
            "process_model": "one point per process, fresh process per run, one pinned CPU, one runner",
            "segment_upper_estimate_s": {"O": 300, "P": 700},
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
             "indexbuild_tests (the derived state loop, insert loop and self-test against the parent's, verbatim, "
             "with planted non-bijections)"),
            ("every IC process (arm.py): KIC_INDEX_CANON as the arm (lift; lift_plant in cM38IBX only); index roots "
             "checked against the selected canonicalizer 0 times, or 2 x stored states in cM38IBX; the full scan "
             "self-test; the arm's index_build_pipeline (none for the row's producer); its base's frozen base hash, "
             "columns, orbits, states, slots, root entries, logical-state and table-map digests; and its base's "
             "frozen LAYOUT digests (stored_states_blake3, table_slots_blake3)"),
            "per point: one scalar across every IC process (both binaries, cold and rank) and rT, replayed as [d]G = Q in the pinned oracle",
            "per point and base: one relation and one probe count across every IC process of both binaries",
            "per base (K600, M38 and M10): one index and layout digest set across both binaries, equal to the frozen one",
            ("Q0 (O1): cPI and cPIB give B's archived identity (1,987,852 probes); cM38I and cM38IB, and cM10I and "
             "cM10IB, give their closure base's frozen identity"),
            ("rank arms: full rank, 0 failed attempts, one frame per attempt, and the written factor-log table equal "
             "to the base's frozen verified table, log for log"),
            ("per M38 rank seed: rank_relations_blake3, the per-attempt probe vector, root calls and point-addition "
             "counters identical across every kM38I, kM38IB and kM38IBaa process with that seed"),
            ("probe law: kM38I's pooled probes per relation over its %d distinct seeds (%d attempts) over "
             "r / (166 E) inside [0.80, 1.20]" % (POINTS * K, POINTS * K * 16)),
        ],
        "statistics": {
            "e2e_per_side": ("E2E(side) = timing_ms.rank_stage of the side's rank process + cold_in_process_ms of the "
                             "side's cold process: setup (including the index build and the scan self-test) + "
                             "rank stage + linear algebra + one-target online, the row's definition"),
            "primary": ("R = sum over the %d primary pairs of E2E(A) / sum over the same pairs of E2E(B). 95%% "
                        "percentile interval from a two-stage paired bootstrap, %d draws, random.Random(%d): the "
                        "points drawn with replacement, then each drawn point's pairs drawn with replacement; A and "
                        "B of a pair are always drawn together" % (POINTS * K, DRAWS, BOOT_SEED)),
            "primary_is": "the paired END-TO-END ratio; every stage ratio is co-reported and never decides",
            "stage_secondary": ("INDEX-BUILD STAGE ratio, labelled a stage secondary: timing_ms.index_build of cM38I "
                                "over cM38IB in the primary pairs, same bootstrap; also over the rank processes"),
            "pairing_basis": ("AGENTS.md Tier 1: 'run both variants on the same pinned exposed CPU with the same "
                              "workload and limits' and 'require repeated alternating pairs'. A pair is the two "
                              "variants on the same point with the same rank seed, adjacent in time on one CPU, in "
                              "alternating order"),
            "secondary": [
                "geometric mean of the per-pair ratios E2E(A)/E2E(B), with the same bootstrap",
                "cold, setup, index build (stage secondary), scan self-test and online cM38I / cM38IB, paired",
                "rank stage kM38I / kM38IB, paired (expected about 1: the same rank work)",
                "index build in the rank processes kM38I / kM38IB, paired",
                "E2E process CPU time and process wall A / B, with the same bootstrap",
                "peak RSS and minor faults of the cold processes",
                "per-point ratio, and the ratio by pair position and by side order",
                "probe law of kM38I and kM38IB; rho ms/step from rT; S per side; E2E cold gap IC / rT",
            ],
        },
        "controls_pass_rule": {
            "aa": ("over the %d A/A pairs: E2E(B) / E2E(Baa) and cold cM38IB / cM38IBaa, the same ratio of sums, "
                   "point estimates both inside [0.97, 1.03]" % (POINTS * K_AA)),
            "planted": ("index build cM38IBX / cM38IB over the %d planted pairs, 95%% bootstrap lower bound (pairs "
                        "resampled, 10,000 draws) above 1; every cM38IBX must also reproduce the frozen layout "
                        "digests and check 2 x stored states roots" % (POINTS * K_PLANTED)),
            "planted_exactness": ("the three planted corruptions rejected by verify_closure.py on both closure bases "
                                  "before timing, and indexbuild_tests (planted non-bijections) passing"),
            "otherwise": "verdict invalid",
        },
        "decision_rule": {
            "improvement": "R lower bound > 1: a qualified Tier 1 end-to-end speedup of the derived producer over the row",
            "regression": "R upper bound < 1",
            "not_separated": "otherwise",
            "invalid": "any gate or control fails or is unknown, or any scheduled row is missing (time-guard skips included)",
        },
        "multiplicity": "one primary statistic; every secondary is descriptive and never changes the verdict",
        "exactness_argument": {
            "parent": parent["exactness_argument"],
            "indexbuild": (
                "The derived producer differs from the row's in three computations, none of which changes a value. "
                "(1) State loop: S3Solver128::roots computes prepare, one inversion of the denominator a*ps (zero "
                "takes the scalar fallback) and finish. RootBatch128::solve computes the same prepare, inverts the "
                "product of the row's non-zero denominators once and recovers each inverse as (prefix product) x "
                "(inverse of the running product), which is that denominator's field inverse because inverses in "
                "GF(2^83) are unique; finish then returns the same two roots in the same order. States are pushed in "
                "the parent's (left, right, relative) order, so stored_states_blake3 is the parent's. (2) Insert "
                "loop: index_canonical128 is a pure function of the root (plus the planted counter, called once per "
                "root in the same order), so computing it 32 roots early changes no key or shift; the prefetch is a "
                "hint without architectural effect; insert_if_absent is called with the same (key, value) sequence "
                "into the same table, so every slot word, and table_slots_blake3, is the parent's. (3) Self-test: "
                "the parent returns false iff some image of [0, domain) is >= domain or an in-range image repeats, "
                "else visited == len; the lanes loop evaluates the same apply on the same indices and the same "
                "checks on the images in index order, eight applies ahead of their checks, so it returns the same "
                "boolean. Relations, probes, the rank stage and the online scan read only the index and the "
                "self-test verdict, so they are the parent's. Gated per process and per base on K600, M38 and M10."),
        },
        "evidence_change": ("none: every process still runs the full exhaustive scan self-test on its own state count "
                            "and both keys, and still builds, checks and digests its own index. The sampled self-test "
                            "option (a once-per-binary-and-base full check plus per-process samples) is described in "
                            "the README as a separate, evidence-changing candidate and is not used"),
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
