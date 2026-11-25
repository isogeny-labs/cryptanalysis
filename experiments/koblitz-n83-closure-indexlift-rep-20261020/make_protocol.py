#!/usr/bin/env python3
"""Write the frozen protocol (`protocol.json`) of the n=83 closure + index-lift replication.

Run once, before any timing. Run it after `restore.py --no-pin-check` (which
derives the producer, regenerates the closure headers and checks every
parent digest), `make_targets.py`, `check_panel_disjoint.py`,
`make_power_prior.py` and `power_check.py`. `restore.py` re-checks every
digest this file records.

The producer, the bases, the arm configurations and the per-process gates
are the parent's (`koblitz-n83-closure-indexlift-20261019`, PR #997). They
are read from the parent's frozen `protocol.json`, whose SHA-256 is pinned
in `restore.py`, and copied verbatim. Five things change:

* the panel: 10 new held-out points (`inputs/cold_targets.json`);
* the rank seeds: 1201-1230, new on n=83;
* the design: repeated alternating pairs (AGENTS.md, "CPU performance
  isolation gate", Tier 1);
* the primary: the paired end-to-end ratio, with a two-stage paired
  bootstrap;
* the receipt: the CPU record (`scripts/host_cpu_record.py`), the placement
  of every process and the scheduling counters.

The M10 secondary is not timed. Its base stays in `online.bases` because
`check_log_table.py` (verbatim) verifies both closure bases before timing.
"""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
POINTS = 10
K = 3            # alternating primary pairs per point
K_AA = 2         # alternating A/A pairs per point
K_PLANTED = 1    # alternating planted pairs per point
SEED0 = 1200     # rank seed of pair j at point i: SEED0 + 3 i + j (1201 .. 1230)
ORDER_SEED0 = 2026102000
RHO_SEED_BASE = 1020000
DRAWS = 10000
BOOT_SEED = 20261020
ARMS = ("cPI", "kPI", "cM38I", "kM38I", "cM38Iaa", "kM38Iaa", "kM38IX", "rT")


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    import restore  # noqa: E402  (this directory)

    parent = restore.parent_protocol()
    power = json.loads((HERE / "analysis" / "power.json").read_text())
    targets = json.loads((HERE / "inputs" / "cold_targets.json").read_text())
    disjoint = json.loads((HERE / "inputs" / "panel_disjointness.json").read_text())
    if disjoint.get("disjoint") is not True:
        raise SystemExit("the panel is not disjoint from every earlier n=83 panel")
    if len(targets["points"]) != POINTS:
        raise SystemExit("panel size differs from the design")
    pd = power["design"]
    if (pd["points"], pd["primary_pairs_per_point"], pd["aa_pairs_per_point"], pd["planted_pairs_per_point"]) != \
            (POINTS, K, K_AA, K_PLANTED):
        raise SystemExit("power.json was computed for another design")
    bases = {}
    for name, spec in parent["online"]["bases"].items():
        spec = dict(spec)
        spec["replication_source"] = ("koblitz-n83-closure-indexlift-20261019 protocol.json online.bases.%s "
                                      "(sha256 %s), verbatim" % (name, restore.PARENT_PROTOCOL_SHA256))
        bases[name] = spec
    bases["M10"]["replication_note"] = ("not timed in this replication; kept because check_log_table.py (verbatim) "
                                        "verifies both closure bases and their planted corruptions before timing")
    arms = {name: dict(parent["arms"][name]) for name in ARMS}
    for name in ARMS:
        arms[name]["replication_source"] = "the parent's arm %s, verbatim" % name
    rank_seeds = {"s%03d" % i: [SEED0 + 3 * i + j for j in range(1, K + 1)] for i in range(POINTS)}
    protocol = {
        "schema": 1,
        "kind": "n83-closure-indexlift-replication-paired-e2e-tier1",
        "frozen_before_any_timing": True,
        "frozen_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "question": ("Replication of PR #997 under the Tier 1 rule. Is the closure + index-lift M38I producer's "
                     "END-TO-END cold cost (setup + index build + rank stage + linear algebra + one-target online) "
                     "lower than the index-lift row's on new held-out points and new rank seeds? The test uses "
                     "repeated alternating pairs and a 95% paired confidence interval whose lower bound must exceed "
                     "1 (AGENTS.md, 'CPU performance isolation gate', Tier 1). Every relation is checked in the "
                     "group, every column log and scalar verified, the probe law kept, and the index-lift layout "
                     "reproduced byte for byte."),
        "why_this_run": ("PR #997 (merged e55510070) made this producer the n=83 a=1 row: 7.6558 [7.2192, 8.1103], "
                         "run 39335956567. Its primary had one cM38I and one cPI cold observation per point (20 "
                         "points) and separate rank blocks (4 kPI, 16 kM38I). Neither the cold arms nor the rank "
                         "arms were repeated alternating primary pairs, so the row does not rest on a qualified Tier 1 "
                         "speedup (the owner's qualification notes on claude/n83-knownlog and claude/n83-onlineframe "
                         "make the same point for PRs #986 and #988). This run replicates it properly."),
        "success_criterion": "AGENTS.md 'Success criterion: iterative improvement of the index-calculus baseline'",
        "tier_rule": ("AGENTS.md 'CPU performance evidence tiers', Tier 1: same pinned exposed CPU, same workload and "
                      "limits; code and workload hashes, paired order, raw failures, correctness, process CPU time, "
                      "memory, cgroup throttling and memory failures, steal time and scheduling counters recorded; "
                      "repeated alternating pairs and a 95% paired confidence interval whose lower bound exceeds 1"),
        "replicates": {"experiment": "koblitz-n83-closure-indexlift-20261019", "pr": 997, "merge": "e55510070",
                       "run": "https://github.com/aburan28/cryptanalysis/actions/runs/39335956567",
                       "parent_protocol_sha256": restore.PARENT_PROTOCOL_SHA256,
                       "parent_primary": "7.6558 [7.2192, 8.1103] (one observation per point and arm)"},
        "expected_effect": ("about %.2f end to end at the parent run's means (power_check.py "
                            "expected_ratio_at_prior_means; an estimate, not a claim)" %
                            power["expected_ratio_at_prior_means"]),
        "sources": {
            "crypto_770f6a69": parent["sources"]["crypto_770f6a69"],
            "rankprobe_producer": parent["sources"]["rankprobe_producer"],
            "indexlift_producer": parent["sources"]["indexlift_producer"],
            "closure_producer": parent["sources"]["closure_producer"],
            "composition": parent["sources"]["composition"],
            "online_source_sha256": sha256(restore.DERIVED),
            "online_source_sha256_parent": parent["sources"]["online_source_sha256"],
            "parent_protocol_sha256": restore.PARENT_PROTOCOL_SHA256,
            "verbatim_from_parent": list(restore.VERBATIM),
            "code_change": "none: the producer, the derivation, arm.py and check_log_table.py are the parent's bytes",
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
                                  "(make_targets.py EARLIER_ROLES; role-agnostic x-coordinate scan in "
                                  "inputs/panel_disjointness.json)" % (targets["role"], POINTS)),
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
            "sides": {"A": ["kPI", "cPI"], "B": ["kM38I", "cM38I"], "Baa": ["kM38Iaa", "cM38Iaa"]},
            "side_rule": ("a side is two fresh processes run back to back, its rank process and then its cold "
                          "process, both on the pair's point. The rank process runs the rank stage with the pair's "
                          "rank seed and then solves the point. The cold process loads the base's verified table "
                          "and solves the point"),
            "pair_rule": ("a primary pair is one A side and one B side with the same point and the same rank seed. "
                          "Each point's K pairs run as 2K sides in strict alternation, ABAB... or BABA..., and the "
                          "starting side is drawn from random.Random(ORDER_SEED0 + i). Pair j is sides 2j-1 and 2j"),
            "aa_rule": ("an A/A pair is one B side and one Baa side with the same point and the rank seed of primary "
                        "pair j (j = 1..K_AA). The 2 K_AA sides alternate strictly, with the start drawn from the "
                        "same generator"),
            "planted_rule": ("a planted pair is kM38I and kM38IX, rank processes only, with the rank seed of primary "
                             "pair K. They alternate, and the start is drawn from the same generator"),
            "rho_rule": "one rT process per point, seed rho_seed_base + point seed",
            "segment_rule": ("O1: Q0 on cPI and cM38I, shuffled by random.Random(ORDER_SEED0 + 99). Then one segment "
                             "P<i> per point i = 1..POINTS in panel order. Its four sub-blocks (primary, aa, planted, "
                             "rho) run in an order shuffled by the point's generator"),
            "order_seed0": ORDER_SEED0,
            "rank_seed0": SEED0,
            "rank_seeds": rank_seeds,
            "rank_seeds_note": ("1201-1230 are new on n=83. Used before: 7, 29, 101-102, 201-204, 301-309, 401-404, "
                                "501-504, 701, 801-816, 901-904 and 1101-1116 (every protocol on origin and in the "
                                "scratch worktrees). Each seed fixes K' new rank targets [a]G - R_c on each base"),
            "rho_seed_base": RHO_SEED_BASE,
            "q0_point": parent["design"]["q0_point"],
            "q0_arms": ["cPI", "cM38I"],
            "process_model": "one point per process, fresh process per run, one pinned CPU, one runner",
            "segment_upper_estimate_s": {"O": 300, "P": 1300},
            "timeout_s": parent["design"]["timeout_s"],
            "time_guard": ("before each segment: skip it (rows skipped_time_guard) if the elapsed job time plus the "
                           "larger of its upper estimate and 1.1x the longest segment of its panel so far exceeds "
                           "285 min. A skipped row makes the run invalid"),
            "runtime_estimate": ("power.json runtime: about %.0f min for the job (%.0f min schedule), about %.0f min on "
                                 "a 1.5x slower host; the job limit is 300 min" % (
                                     power["runtime"]["job_total_min"], power["runtime"]["schedule_min"],
                                     power["runtime"]["job_total_min_on_a_1.5x_slower_host"])),
        },
        "gates": [
            "every scheduled row present and valid (exit 0, verified, schedule match, no memory event), no time-guard skip",
            ("receipt integrity (verify_receipt.py, fail closed): every executed row's raw producer record decodes, "
             "its SHA-256 equals the wrapper summary's raw_result_sha256, and its arm, kind, panel, point and seed "
             "equal the frozen schedule's. Each row's serial, arm, point, seed, segment, command line and stdout "
             "file equal the schedule's. Rows ran in schedule order. runner_start.json records this protocol's, "
             "this schedule's, arm.py's and run_schedule.py's SHA-256 and no smoke subset. Every row ran the binary "
             "runner_start.json records, unchanged at the end. An unknown gate is a failure"),
            ("placement: every process's Cpus_allowed_list, read from /proc while it ran, is the one execution CPU"),
            ("host identity: the CPU record (scripts/host_cpu_record.py) at the start and the end of the schedule has "
             "the same model, microcode and flags"),
            ("before any timing: check_log_table.py (verbatim). B's table is re-verified in the pinned oracle. Both "
             "closure headers are regenerated to their frozen SHA-256 and pass verify_closure.py, and the three "
             "planted corruptions are rejected. Each closure table passes [L_c]G = R_c and [w L_c]G = alpha(R_c), "
             "and the closure logs equal B's archived logs"),
            ("every IC process (arm.py, verbatim): KIC_INDEX_CANON=lift; 0 index roots checked against the selected "
             "canonicalizer; the full scan self-test; its base's frozen base hash, columns, orbits, states, slots, "
             "root entries, logical-state and table-map digests; and its base's frozen LAYOUT digests "
             "(stored_states_blake3, table_slots_blake3)"),
            "per point: one scalar across every IC process (both bases, cold and rank) and rT, replayed as [d]G = Q in the pinned oracle",
            "per point and base: one relation and one probe count across every IC process",
            "per base: one index and layout digest set, equal to the frozen one",
            "Q0 (O1): cPI gives B's archived identity (1,987,852 probes); cM38I gives the closure protocol's frozen identity",
            ("rank arms: full rank, 0 failed attempts, one frame per attempt, and the written factor-log table equal "
             "to the base's frozen verified table, log for log"),
            ("per M38 rank seed: rank_relations_blake3, the per-attempt probe vector, root calls and point-addition "
             "counters identical across every kM38I, kM38Iaa and kM38IX process with that seed"),
            ("probe law: kM38I's pooled probes per relation over its 30 distinct seeds (480 attempts) over "
             "r / (166 E) inside [0.80, 1.20]"),
        ],
        "statistics": {
            "e2e_per_side": ("E2E(side) = timing_ms.rank_stage of the side's rank process + cold_in_process_ms of the "
                             "side's cold process. The cold process holds setup + index build + online, the rank "
                             "stage holds the rank attempts and the linear algebra. So E2E = setup + index build + "
                             "rank stage + linear algebra + one-target online, the row's definition"),
            "primary": ("R = sum over the %d primary pairs of E2E(A) / sum over the same pairs of E2E(B). 95%% "
                        "percentile interval from a two-stage paired bootstrap, %d draws, random.Random(%d): the "
                        "points drawn with replacement, then each drawn point's pairs drawn with replacement; A and "
                        "B of a pair are always drawn together" % (POINTS * K, DRAWS, BOOT_SEED)),
            "primary_is": "the paired END-TO-END ratio; the rank-stage and cold ratios are co-reported and never decide",
            "pairing_basis": ("AGENTS.md Tier 1: 'run both variants on the same pinned exposed CPU with the same "
                              "workload and limits' and 'require repeated alternating pairs'. A pair is the two "
                              "variants on the same point with the same rank seed, adjacent in time on one CPU, in "
                              "alternating order. docs/IC_BENCHMARK_TIERS.md uses the same unit (the same point, "
                              "alternating order, one allocation)"),
            "secondary": [
                "geometric mean of the per-pair ratios E2E(A)/E2E(B), with the same bootstrap",
                "rank stage kPI / kM38I and cold cPI / cM38I, both paired, with the same bootstrap",
                "E2E process CPU time (user + system of both processes of each side) A / B, with the same bootstrap",
                "E2E process wall time (both processes of each side) A / B, with the same bootstrap",
                "per-point ratio, and the ratio by pair position in the sequence (first, second, ...) and by side order",
                "setup, index build, online and peak RSS cPI / cM38I over the primary pairs",
                "probe law of kPI and kM38I; rows without gain; point-addition counters",
                "rho ms/step from rT; S per arm; E2E cold gap IC / rT",
            ],
        },
        "controls_pass_rule": {
            "aa": ("over the %d A/A pairs: E2E(B) / E2E(Baa) and cold cM38I / cM38Iaa, the same ratio of sums, "
                   "point estimates both inside [0.97, 1.03]" % (POINTS * K_AA)),
            "planted": ("kM38IX / kM38I per attempt over the %d planted pairs (attempts paired within pairs), 95%% "
                        "bootstrap lower bound above 1" % (POINTS * K_PLANTED)),
            "planted_exactness": "the three planted corruptions rejected by verify_closure.py on both closure bases before timing",
            "otherwise": "verdict invalid",
        },
        "decision_rule": {
            "improvement": "R lower bound > 1: a qualified Tier 1 end-to-end speedup of the M38I producer over the index-lift row",
            "regression": "R upper bound < 1",
            "not_separated": "otherwise",
            "invalid": "any gate or control fails or is unknown, or any scheduled row is missing (time-guard skips included)",
        },
        "multiplicity": "one primary statistic; every secondary is descriptive and never changes the verdict",
        "exactness_argument": parent["exactness_argument"],
        "power": {"file": "analysis/power.json", "min_delta": power["min_delta"],
                  "power_at_min_delta": power["power_at_min_delta"],
                  "rejection_rate_at_no_effect": power["type_i_at_1.00"],
                  "modelled": power["cells"]["modelled"],
                  "expected_ratio_at_prior_means": power["expected_ratio_at_prior_means"],
                  "aa_control": power["aa_control"], "law_gate": power["law_gate"],
                  "planted_control": power["planted_control"]},
        "bootstrap": {"draws": DRAWS, "seed": BOOT_SEED},
    }
    (HERE / "protocol.json").write_text(json.dumps(protocol, indent=1, sort_keys=True) + "\n")
    print(str(HERE / "protocol.json"))


if __name__ == "__main__":
    main()
