#!/usr/bin/env python3
"""Write the frozen protocol (`protocol.json`) of the n=83 Z[tau]-closure experiment.

Run once, before any timing, after `restore.py --no-pin-check` (derives the
producer and regenerates the closure headers), `make_targets.py`,
`make_power_prior.py`, `power_check.py` and the local decisive test
(`inputs/local_decisive_test.json`, which supplies each closure base's index
digests, root entries, Q0 identity and the choice of the primary).
`restore.py` re-checks every digest this file records.
`koblitz-n83-rankprobe-20261019`'s `make_protocol.py` with this
experiment's bases, arms, blocks, gates and bootstrap.
"""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
RANKPROBE = HERE.parent / "koblitz-n83-rankprobe-20261019"
B_LOG_TABLE = "../koblitz-single-target-n83-tier1-20261014/tier1_github_38523707244/precompute/factor_logs_n83_K600.json"
BINARY = "ic_online_closure_r770"
PRIMARY, SECONDARY = "M38", "M10"
BLOCKS = 16
SEED0 = 800
BASELINE_BLOCKS = (1, 5, 9, 13)          # kP and the planted kM38X
SECONDARY_BLOCKS = tuple(range(1, BLOCKS + 1, 2))  # kM10: 8 blocks
LAW_BANDS = {"M38": [0.80, 1.20], "M10": [0.85, 1.15]}


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    import restore  # noqa: E402  (this directory)

    power = json.loads((HERE / "analysis" / "power.json").read_text())
    targets = json.loads((HERE / "inputs" / "cold_targets.json").read_text())
    local = json.loads((HERE / "inputs" / "local_decisive_test.json").read_text())["bases"]
    rankprobe = json.loads((RANKPROBE / "protocol.json").read_text())
    q0 = rankprobe["design"]["q0_point"]
    points = len(targets["points"])
    k600 = rankprobe["online"]
    bases = {
        "K600": {
            "path": k600["base"], "header_sha256": sha256(HERE / k600["base"]),
            "base_hash": k600["base_hash"], "orbit_columns": 600, "index_orbits": 600, "norm_cap": None,
            "factor_base_points": 99600, "regular_states": 29880000, "stored_states_folded": 14940300,
            "root_table_entries": 29878182, "root_table_slots": 1 << 26, "index_digest": k600["index_digest"],
            "factor_log_table": B_LOG_TABLE, "factor_log_table_sha256": sha256(HERE / B_LOG_TABLE),
            "factor_log_table_check": "check_log_table.py (B's table in the pinned oracle, as the rank-probe run)",
            "q0_identity": k600["q0_identity"],
            "role": "B's K600 header: 600 columns, one signed Frobenius orbit each (the baseline)",
        },
    }
    for name in (PRIMARY, SECONDARY):
        rec = local[name]
        columns, cap = restore.CLOSURE_BASES[name]
        orbits = rec["verify_closure"]["base_check"]["notes"]["orbits"]
        regular = 83 * orbits * orbits
        if rec["index_digest"]["logical_states"] != regular:
            raise SystemExit("local record of %s does not have 83 * orbits^2 states" % name)
        bases[name] = {
            "path": str(restore.closure_path(name).relative_to(HERE)),
            "header_sha256": sha256(restore.closure_path(name)),
            "builder": "make_closure_base.py --columns %d --norm %d (from B's K600 header, in restore.py)" % (columns, cap),
            "base_hash": rec["base_hash"], "orbit_columns": columns, "index_orbits": orbits, "norm_cap": cap,
            "orbits_per_column": orbits // columns, "factor_base_points": 2 * 83 * orbits,
            "regular_states": regular, "stored_states_folded": None,
            "root_table_entries": rec["root_table_entries"], "root_table_slots": 1 << 26,
            "index_digest": dict(rec["index_digest"], source=(
                "the local decisive test (inputs/local_decisive_test.json): identical over %d local rank processes "
                "(seeds 301-3%02d); a function of the orbit representatives only" % (
                    len(rec["blocks"]), len(rec["blocks"])))),
            "factor_log_table": "inputs/factor_logs_n83_closure_%s.json" % name,
            "factor_log_table_sha256": sha256(HERE / "inputs" / ("factor_logs_n83_closure_%s.json" % name)),
            "factor_log_table_check": ("verify_closure.py --base --table --planted (pinned oracle): the base's every "
                                       "orbit, member and label, [L_c]G = R_c for every column, [w L_c]G = alpha(R_c) "
                                       "for every orbit; and the logs equal B's archived logs of R_0..R_{K'-1}"),
            "logs_equal_B_first_columns": rec["closure_logs_equal_B_first_K_logs"],
            "q0_identity": {"scalar": rec["q0"]["scalar"], "probes_folded": rec["q0"]["probes"],
                            "relation": rec["q0"]["relation"],
                            "source": "the local decisive test (rank process, seeds 301-3%02d, identical)" % len(rec["blocks"])},
            "law_probes_per_relation": rec["law_probes_per_relation"],
            "law_band": LAW_BANDS[name],
            "role": ("Z[tau]-multiplier closure: %d columns x %d orbits (alpha = a + b tau, a odd > 0, "
                     "a^2 + ab + 2b^2 <= %d); column c's orbits are alpha(R_c) for B's R_c" % (
                         columns, orbits // columns, cap)),
        }
    # Stored (folded) states of the local decisive test's processes (stored_states in their summaries).
    stored_local = {"M38": 15341360, "M10": 14940300}
    for name in (PRIMARY, SECONDARY):
        bases[name]["stored_states_folded"] = stored_local[name]
    cold = lambda base, **kw: dict({"kind": "ic_cold", "binary": BINARY, "table": "compact", "fold": True,  # noqa: E731
                                    "base": base}, **kw)
    rank = lambda base, **kw: dict({"kind": "ic_rank", "binary": BINARY, "table": "compact", "fold": True,  # noqa: E731
                                    "base": base, "rank_canon": "lift", "rank_order": "feistel",
                                    "rank_probe": "target"}, **kw)
    arms = {
        "cP": cold("K600", role=("baseline cold: the rank-probe producer's cold path on B's K600 header with B's "
                                 "verified table (koblitz-n83-rankprobe-20261019 arm cP, the n=83 baseline)")),
        "kP": rank("K600", rank_solve="frame",
                   role=("baseline rank stage: the rank-probe producer's (frame loop, lift_scan, Feistel, 16-byte "
                         "compact table over the folded index), 600 guided attempts on B's K600 header")),
        "cM38": cold("M38", role=("PRIMARY candidate cold: the same code on the M38 closure header (16 columns, 608 "
                                  "orbits in the root index) with its verified 16-log table")),
        "kM38": rank("M38", rank_solve="frame",
                     role=("PRIMARY candidate rank stage: the same loop on the M38 closure header: 16 guided attempts "
                           "[a]G - R_c to full rank 16")),
        "cM38aa": cold("M38", role="A/A control: a second cold process of cM38"),
        "kM38aa": rank("M38", rank_solve="frame", role="A/A control: a second rank process of kM38"),
        "kM38X": rank("M38", rank_solve="frame_plant",
                      role=("planted positive control: kM38 with the rank-probe producer's frame_plant (the rank-cut "
                            "loop's key derivation redone and compared on every candidate), a known per-attempt "
                            "cost of about 2x that the timing must detect")),
        "cM10": cold("M10", role=("pre-registered SECONDARY candidate cold: the M10 closure header (60 columns, 600 "
                                  "orbits) with its verified 60-log table; never decides")),
        "kM10": rank("M10", rank_solve="frame", role="pre-registered SECONDARY candidate rank stage (60 attempts); never decides"),
        "rT": {"kind": "rho_tuned", "binary": "rho_tuned_r770",
               "role": "A's tuned rho rT770 (Fold/64/DP6), the strongest one-target rho at n=83, same points"},
    }
    cold_arms = ["cP", "cM38", "cM38aa", "cM10", "rT"]
    rank_blocks = []
    for b in range(1, BLOCKS + 1):
        block_arms = ["kM38", "kM38aa"]
        if b in BASELINE_BLOCKS:
            block_arms = ["kP"] + block_arms + ["kM38X"]
        if b in SECONDARY_BLOCKS:
            block_arms.append("kM10")
        rank_blocks.append({"id": "K%d" % b, "unit": "s%03d" % (b - 1), "rank_seed": SEED0 + b, "arms": block_arms})
    order = ["O1"]
    for i in range(1, points + 1):
        order.append("C%d" % i)
        if i <= BLOCKS:
            order.append("K%d" % i)
    protocol = {
        "schema": 1,
        "kind": "n83-closure-e2e-cold-tier1",
        "frozen_before_any_timing": True,
        "frozen_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "question": ("Does grouping the ~600 Frobenius orbits of the n=83 a=1 root index into K' = 600 / M "
                     "linear-algebra columns by the Z[tau]-multiplier closure (orbit (c, alpha) = alpha(R_c), log "
                     "(a + b lambda) log R_c; M = 38 at norm <= 64, primary; M = 10 at norm <= 16, secondary) lower "
                     "the END-TO-END cold cost (setup + index build + rank stage + linear algebra + one-target online) "
                     "of the rank-probe producer on new targets and new rank seeds, with every relation checked in "
                     "the group, every column log verified, every scalar verified, and the probe law kept?"),
        "success_criterion": "AGENTS.md 'Success criterion: iterative improvement of the index-calculus baseline'",
        "current_baseline": ("the rank-probe producer (koblitz-n83-rankprobe-20261019, run 39214027289, PR #980): "
                             "end-to-end cold 166.0 s (rank stage 143.7 s + cold 22.3 s), S 6.390, gap to rT770 64.0 "
                             "[53.7, 78.0]; its rank stage is 86.6% of end-to-end cold (600 attempts, 1.69 M probes each)"),
        "concurrent_lanes": ("claude/n83-indexlift (run 39290913632, lift_scan in the index build; verdict pending at "
                             "freeze) changes the cold path and stacks with this change; claude/n83-k899, "
                             "claude/n83-rotkey and claude/n83-onlineframe are local or diagnostic. This protocol is "
                             "frozen against the rank-probe row; its arms do not contain any of those changes"),
        "primary_choice": {
            "primary": PRIMARY, "secondary": SECONDARY,
            "rule": ("chosen from the local decisive test before freezing: both closures passed (full rank, 0 "
                     "failures, 0 rows without gain, every column log verified and equal to B's, Q0 solved); the "
                     "pooled probe law was %.3f +- %.3f (M38, %d attempts) and %.3f +- %.3f (M10, %d attempts); M38 "
                     "is primary because it needs 16 relations instead of 60 at the same law (modelled end to end "
                     "about 26 s against 37 s), the larger expected improvement" % (
                         local["M38"]["pooled_mean_probes_over_law"], local["M38"]["pooled_se"],
                         local["M38"]["pooled_attempts"], local["M10"]["pooled_mean_probes_over_law"],
                         local["M10"]["pooled_se"], local["M10"]["pooled_attempts"])),
        },
        "sources": {
            "crypto_770f6a69": "770f6a6925a0d29b768bd79074f54a173e967fe7 (snapshots/r770 via ../koblitz-n83-reconcile-20261014/restore_sources.py)",
            "rankprobe_producer": ("koblitz-n83-rankprobe-20261019 make_online_source.py (make_rankprobe_source.py here, "
                                   "verbatim with its five parents), output sha256 "
                                   "d4394df35d065afbfb05022eac3006492239cc64b94de16fba501322cb578bb5"),
            "online_source_sha256": sha256(restore.DERIVED),
            "local_sha256": {key: sha256(path) for key, path in restore.local_files().items()},
        },
        "online": {
            "bases": bases,
            "curve_id": k600["curve_id"],
            "subgroup_order": k600["subgroup_order"],
            "lambda": "2998004823950457",
            "sqrt_r": k600["sqrt_r"],
            "tuned_rho_config": k600["tuned_rho_config"],
            "cold_targets_file": ("inputs/cold_targets.json (role closure-cold-v1; disjoint from Q0, B's panel, every "
                                  "earlier n=83 panel of the law, rankprobe-cold-v1 and the concurrent lanes' "
                                  "indexlift-cold-v1, k899-cold-v1, rotkey-cold-v1 and onlineframe-v1)"),
            "cold_interval": k600["cold_interval"],
            "rank_interval": k600["rank_interval"],
            "online_interval": k600["online_interval"],
            "base_construction": ("not charged to any arm (the convention of both n=83 rows: B's header is loaded, "
                                  "and so is each closure header; each closure header holds B's first K' orbits plus "
                                  "(M - 1) K' images alpha(R_c), two small scalar multiplications each, |a| <= 7, "
                                  "|b| <= 6)"),
        },
        "arms": arms,
        "design": {
            "cold_points": points,
            "cold_arms": cold_arms,
            "rank_arms": ["kP", "kM38", "kM38aa", "kM38X", "kM10"],
            "q0_arms": ["cP", "cM38", "cM10"],
            "q0_point": q0,
            "rho_seed_base": 910000,
            "rank_blocks": rank_blocks,
            "rank_seeds_note": ("801-816 are new (stacked 101-102, rank cut 201-204, rank probe 301-304, the K899 and "
                                "index-lift lanes 401-404, rotkey 501-504, onlineframe 701; the local decisive test "
                                "used 301-309 on the closure bases only); each seed fixes K' new rank targets "
                                "[a]G - R_c on each base"),
            "blocks_note": ("kP and kM38X run in blocks K1, K5, K9, K13 (4 blocks of 600 and 16 attempts); kM38 and "
                            "kM38aa in all 16 blocks (256 attempts each); kM10 in the 8 odd blocks (480 attempts). "
                            "The baseline's and the candidates' attempts are different targets (different columns "
                            "and bases), so the primary bootstrap resamples each rank arm on its own"),
            "segment_order": order,
            "within_segment_order": ("random.Random(2026101950 + i).shuffle (C), random.Random(2026101970 + b) (K), "
                                     "random.Random(2026101990) (O)"),
            "process_model": "one point per process, fresh process per run, one pinned CPU, one runner",
            "segment_upper_estimate_s": {"C": 360, "K": 900, "O": 300},
            "timeout_s": {"ic_cold": 600, "ic_rank": 1800, "rho_tuned": 600},
            "time_guard": "skip a segment (rows skipped_time_guard) if elapsed + its estimate exceeds 300 min",
            "runtime_estimate": ("from run 39214027289: build and tests about 15 min, closure headers and their "
                                 "verification about 3 min; cold segment about 95 s (cP, cM38, cM38aa, cM10 about 23 s "
                                 "each, rT 3 s); rank block with kP about 250 s, without about 70 s; total about 1.3 h, "
                                 "up to about 2 h on a slower runner"),
        },
        "gates": [
            "every scheduled row valid (exit 0, verified, schedule match, no memory event)",
            ("before any timing: B's table re-verified in the pinned oracle (check_log_table.py); each closure header "
             "regenerated from B's header with its frozen SHA-256 and checked by verify_closure.py in the pinned "
             "oracle: identity, multipliers (a odd > 0, norm <= cap), every orbit representative in the prime-order "
             "subgroup and equal to [(a + b lambda) mod r]R_c, all orbits distinct up to sign and Frobenius, every "
             "member and label (+-phi^k(alpha(R_c)), (c, +-(a + b lambda) lambda^k)), base hash; its table: "
             "[L_c]G = R_c for every column and [w L_c]G = alpha(R_c) for every orbit; three planted corruptions "
             "(a label, a duplicated orbit, a log) each rejected; and the closure logs equal B's archived logs of "
             "the same R_c (logs are unique, so this is a cross-check across independent rank stages)"),
            ("every IC process: lift_scan, Feistel, prefetch; the 16-byte compact table with 2^26 slots over the folded "
             "index; its base's frozen base hash, columns, orbits in the root index, logical and stored states, root "
             "entries, logical-state blake3 and table-map digests (online.bases; B's for K600, the local decisive "
             "test's for M38 and M10); no root bloom"),
            "per point: one scalar across every IC process (all three bases, cold and rank) and rT, replayed as [d]G = Q in the pinned oracle",
            "per point and base: one relation (point indices) and one probe count across the IC processes on that base",
            ("Q0 (O1): cP gives B's archived Feistel relation, scalar and 1,987,852 probes; cM38 and cM10 give the "
             "scalar 3141592653589793 and their base's frozen Q0 relation and probe count"),
            ("rank arms: full rank K', 0 failed attempts, the arm's KIC_RANK_SOLVE recorded, one frame per attempt, "
             "the producer's own [L_c]G = R_c check of every log, and the written factor-log table equal to its "
             "base's frozen verified table, log for log"),
            ("per rank block: rank_relations_blake3, the per-attempt probe vector, rank_root_calls_total and the "
             "point-addition counters identical across kM38, kM38aa and kM38X"),
            ("probe law (replaces B's index-digest gate as the check that the closure keeps the root index's law): "
             "the primary rank arm kM38's pooled mean probes per relation over its distinct attempts (one process per "
             "block, 256 attempts), divided by law = r / (166 E) with E its base's frozen root entries, inside "
             "[0.80, 1.20] (about 3.3 standard errors at the baseline's attempt CV 0.97). The secondary kM10's ratio "
             "and its band [0.85, 1.15] (480 attempts) are reported in detail.probe_law_gate and decide only how the "
             "secondary is read, never the primary's validity"),
            "frame counters: kM38X has rank_frame_plant_checked_inputs > 0, every other rank arm 0; rank_padd_plant_checked_inputs 0 everywhere",
        ],
        "controls_pass_rule": {
            "aa": ("E2E(kM38, cM38) / E2E(kM38aa, cM38aa) (blocks paired) and cold cM38 / cM38aa point estimates both "
                   "inside [0.97, 1.03]"),
            "planted": "rank stage kM38X / kM38 (per-attempt cost, attempts paired within blocks), 95% bootstrap lower bound above 1",
            "planted_exactness": "the three planted corruptions rejected by verify_closure.py for both closure bases (workflow step before timing)",
            "otherwise": "verdict invalid",
        },
        "statistics": {
            "end_to_end_cold": ("E2E(k, c) = mean over k's rank blocks of timing_ms.rank_stage of rank arm k + mean "
                                "over the cold points of cold_in_process_ms of cold arm c; the cold processes hold "
                                "setup + online, the rank processes the rank stage, so E2E = setup + index build + "
                                "rank stage + linear algebra + one-target online"),
            "primary": ("R = E2E(kP, cP) / E2E(kM38, cM38). Bootstrap, 10,000 draws, seed 20261019: the baseline's "
                        "blocks resampled with replacement and its attempts resampled within each drawn block; the "
                        "candidate's blocks and attempts likewise, independently (different targets); each process's "
                        "non-attempt time kept; the cold points resampled, paired across cP and cM38"),
            "primary_is": "the END-TO-END cold ratio; the rank-stage and cold ratios are co-reported and never decide",
            "secondary": [
                "R10 = E2E(kP, cP) / E2E(kM10, cM10) (pre-registered secondary candidate; never decides)",
                "E2E(kM10, cM10) / E2E(kM38, cM38)",
                "rank stage kP / kM38 and kP / kM10 (whole stage, means over blocks); attempts and ns per probe per arm",
                "probe law per rank arm: pooled mean probes per relation / law with a bootstrap interval (kP, kM38, kM10)",
                "cold without rank, setup, online and peak RSS: cP / cM38, cP / cM10 (expected near 1: same index size)",
                "rows without gain and the point-addition counters per rank process",
                "rho ms/step from rT; S per arm; delta S cP to cM38; E2E cold gap IC / rT and online gaps",
            ],
        },
        "decision_rule": {
            "improvement": "R lower bound > 1 (the M38 closure producer becomes the new n=83 end-to-end cold baseline)",
            "regression": "R upper bound < 1",
            "not_separated": "otherwise",
            "invalid": "any gate or control fails, or any scheduled row is missing (including time-guard skips)",
        },
        "multiplicity": "one primary statistic; every secondary (M10 included) is descriptive and never changes the verdict",
        "exactness_argument": (
            "Frobenius phi acts on the prime-order subgroup as multiplication by lambda (lambda^2 - lambda + 2 = 0 "
            "mod r), so for alpha = a + b tau, alpha(R) = [a]R + [b]phi(R) = [(a + b lambda) mod r]R, and every member "
            "+-phi^k(alpha(R_c)) of orbit (c, alpha) has discrete log +-(a + b lambda) lambda^k log R_c. The header "
            "carries exactly these labels; verify_closure.py re-derives every member and label from the orbit "
            "representative and checks each representative against [w]R_c and, with the table, against [w L_c]G, "
            "in the pinned oracle. A relation found by the unchanged S3 search is checked in the group by the "
            "unchanged lift (four base points summing to the attempt's point), so its row sum_i coeff_i L_{c_i} = a "
            "(+ L_c for the guided column) holds exactly; full rank gives the unique logs, checked [L_c]G = R_c in "
            "process and equal to B's archived logs of the same R_c. A target's scalar is checked [d]G = Q in "
            "process and replayed in the oracle, and must equal the baseline's and the tuned rho's. The root index, "
            "probe loop and scan are the rank-probe producer's code, built from the closure's orbit representatives."),
        "power": {"file": "analysis/power.json", "min_delta": power["min_delta"],
                  "power_at_min_delta": power["power_at_min_delta"],
                  "rejection_rate_at_no_effect": power["type_i_at_1.00"],
                  "modelled": {c: t["cells"]["modelled"] for c, t in power["candidates"].items()},
                  "law_gate": {c: t["cells"]["law_gate"] for c, t in power["candidates"].items()}},
    }
    (HERE / "protocol.json").write_text(json.dumps(protocol, indent=1, sort_keys=True) + "\n")
    print(str(HERE / "protocol.json"))


if __name__ == "__main__":
    main()
