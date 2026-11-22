#!/usr/bin/env python3
"""Write the frozen protocol (`protocol.json`) of the n=83 rank-probe experiment.

Run once, before any timing, after `make_power_prior.py`, `power_check.py`,
`make_targets.py` and `make_online_source.py`; `restore.py` re-checks every
digest it records. `koblitz-n83-rankcut-20261016`'s `make_protocol.py`
with this experiment's arms, blocks, gates and paired bootstrap.
"""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
LOG_TABLE = "../koblitz-single-target-n83-tier1-20261014/tier1_github_38523707244/precompute/factor_logs_n83_K600.json"
BINARY = "ic_online_rankprobe_r770"
RANKCUT = HERE.parent / "koblitz-n83-rankcut-20261016"


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    import restore  # noqa: E402  (this directory)

    power = json.loads((HERE / "analysis" / "power.json").read_text())
    targets = json.loads((HERE / "inputs" / "cold_targets.json").read_text())
    rankcut = json.loads((RANKCUT / "protocol.json").read_text())
    q0 = rankcut["design"]["q0_point"]
    points = len(targets["points"])
    blocks = power["chosen_rank_blocks"]
    if blocks is None:
        raise SystemExit("the power check found no passing block count")
    cold = lambda **kw: dict({"kind": "ic_cold", "binary": BINARY, "table": "compact", "fold": True}, **kw)  # noqa: E731
    rank = lambda **kw: dict({"kind": "ic_rank", "binary": BINARY, "table": "compact", "fold": True,  # noqa: E731
                              "rank_canon": "lift", "rank_order": "feistel", "rank_probe": "target"}, **kw)
    arms = {
        "cR": cold(role=("baseline cold: the rank-cut producer's cold path (koblitz-n83-rankcut-20261016 arm cR, "
                         "the n=83 baseline once PR #970 lands), setup + one-target online with the verified "
                         "cached factor-log table")),
        "cP": cold(role=("candidate cold: the rank-probe producer's cold path, which is the rank-cut producer's "
                         "code (KIC_RANK_SOLVE is read only by the rank stage, which a cold process skips); its own "
                         "processes, so the candidate's end-to-end cost is measured on its own rows")),
        "cPI": cold(index_canon="lift",
                    role=("pre-registered secondary (optional component, never decides): cP with lift_scan "
                          "canonicalizing the index build (KIC_INDEX_CANON=lift; the rank-cut run's cRI, 1.3377x "
                          "cold without rank, about 3% end to end)")),
        "rT": {"kind": "rho_tuned", "binary": "rho_tuned_r770",
               "role": "A's tuned rho rT770 (Fold/64/DP6), the strongest one-target rho at n=83, same points"},
        "kR": rank(rank_solve="padd",
                   role=("baseline rank stage: the rank-cut producer's (lift_scan, Feistel, the 16-byte compact "
                         "table over the folded index, partner roots by point addition, KIC_RANK_SOLVE=padd), "
                         "then one target")),
        "kP": rank(rank_solve="frame",
                   role=("candidate rank stage: kR's loop in the target's Frobenius frame "
                         "(KIC_RANK_SOLVE=frame): x(T +- phi^s(R_k)) = phi^s(x(T_s +- R_k)) with T_s = phi^(-s)(T) "
                         "tabulated once per attempt, so the two per-candidate normal-to-polynomial maps of the "
                         "conjugate root are gone; the same partner words, keys and probes; then one target")),
        "kPaa": rank(rank_solve="frame", role="A/A control: a second process of kP"),
        "kPX": rank(rank_solve="frame_plant",
                    role=("planted positive control: kP plus the work it removes, redone: the rank-cut loop's "
                          "whole key derivation (per-candidate maps, its own batched inversion and partner "
                          "formulas, canonical keys) on every candidate of every state, compared with kP's keys "
                          "field by field (panic on any difference) and discarded")),
    }
    cold_arms = ["cR", "cP", "cPI", "rT"]
    rank_arms = ["kR", "kP", "kPaa", "kPX"]
    rank_blocks = [{"id": "K%d" % (b + 1), "unit": "s%03d" % b, "rank_seed": 301 + b} for b in range(blocks)]
    # Rank blocks spread through the cold panel: O1, then C and K interleaved.
    order = ["O1"]
    per = points // blocks
    for b in range(blocks):
        order += ["C%d" % i for i in range(b * per + 1, (b + 1) * per + 1)] + ["K%d" % (b + 1)]
    order += ["C%d" % i for i in range(blocks * per + 1, points + 1)]
    protocol = {
        "schema": 1,
        "kind": "n83-rankprobe-e2e-cold-tier1",
        "frozen_before_any_timing": True,
        "frozen_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "question": ("Does running the rank-cut producer's rank-stage probe loop in the target's Frobenius frame "
                     "(T_s = phi^(-s)(T) tabulated once per rank attempt, so each candidate T +- phi^s(R_k) is "
                     "computed as phi^s(T_s +- R_k) from the stored root's own (x, y), without the two "
                     "per-candidate normal-to-polynomial maps of the conjugate root) lower the END-TO-END cold "
                     "cost (setup + index build + rank stage + linear algebra + one-target online) of the "
                     "rank-cut n=83 K600 producer on new targets and new rank seeds, with every rank relation, "
                     "every per-attempt probe count, every scalar and the factor-log table unchanged?"),
        "success_criterion": "AGENTS.md 'Success criterion: iterative improvement of the index-calculus baseline'",
        "current_baseline": ("the rank-cut producer (koblitz-n83-rankcut-20261016, run 38891404048, PR #970): "
                             "end-to-end cold 195.7 s (rank stage 173.2 s + cold 22.5 s), R over the stacked "
                             "producer 1.3336 [1.3300, 1.3377], S 7.52, gap to rT770 65.7 [55.4, 80.2]; its rank "
                             "stage is 88.5% of end-to-end cold"),
        "cost_structure_of_the_baseline": {
            "source": "run 38891404048, arm kR (four processes, rank seeds 201-204)",
            "attempts": 600, "rank": 600, "mean_probes_per_attempt": 1790030, "ns_per_probe_rank": 161.10,
            "reading": ("the attempts and the probes per attempt are fixed by exactness (the gates keep them "
                        "identical), so the lever is the wall time per probe"),
            "local_profile": ("smoke/profile_local.json (cloud-agent VM, diagnostic): median cumulative ns per probe "
                              "of the rank-cut loop over 15 interleaved rounds of 6,000 states: root y 4.1, + "
                              "per-candidate input maps and prefix products 29.3, + batched inversion 50.0, + lambda "
                              "products, normal-basis maps and partners 89.1, + lift_scan keys of both partners "
                              "143.4, + prefetch and key store 200.5, + lookups and hit check 258.0"),
        },
        "sources": {
            "crypto_770f6a69": "770f6a6925a0d29b768bd79074f54a173e967fe7 (snapshots/r770 via ../koblitz-n83-reconcile-20261014/restore_sources.py)",
            "rankcut_producer": ("koblitz-n83-rankcut-20261016 make_online_source.py (make_rankcut_source.py here, "
                                 "verbatim with its four parents), output sha256 "
                                 "c390733ec3a96243d06bf0b121d61b1973f5e34b5e5a2767c3506364d1f8bc2f"),
            "online_source_sha256": sha256(restore.DERIVED),
            "local_sha256": {key: sha256(path) for key, path in restore.local_files().items()},
        },
        "online": {
            "base": "snapshots/r770/experiments/koblitz-single-target-n83-20261006/base_n83_K600.jsonl",
            "base_hash": "d4a4da26d6e7cb09367de922d9806631fe49989f70d378cae76f347f8d76a9f7",
            "curve_id": "EC1N83Ce1h35c7ced6b497",
            "subgroup_order": "8569786107849059",
            "sqrt_r": 92573139.235,
            "orbit_columns": 600,
            "regular_states": 29880000,
            "stored_states_folded": 14940300,
            "root_table_entries": 29878182,
            "root_table_slots": {"unfolded": 1 << 27, "folded": 1 << 26},
            "root_filter_log2_bits": 28,
            "index_digest": rankcut["online"]["index_digest"],
            "factor_log_table": LOG_TABLE,
            "factor_log_table_sha256": sha256(HERE / LOG_TABLE),
            "tuned_rho_config": "snapshots/r770/research/n83_evaluation_20261012/optimization/selected_config.json",
            "cold_targets_file": ("inputs/cold_targets.json (role rankprobe-cold-v1; disjoint from Q0, B's panel and "
                                  "every earlier n=83 panel of the law, including rankcut-cold-v1 and the 64 eval "
                                  "points of n131-ref-walk-20261015)"),
            "q0_identity": rankcut["online"]["q0_identity"],
            "cold_interval": rankcut["online"]["cold_interval"],
            "rank_interval": rankcut["online"]["rank_interval"],
            "online_interval": rankcut["online"]["online_interval"],
        },
        "arms": arms,
        "design": {
            "cold_points": points,
            "cold_arms": cold_arms,
            "rank_arms": rank_arms,
            "q0_arms": ["cR", "cP"],
            "q0_point": q0,
            "rho_seed_base": 880000,
            "rank_blocks": rank_blocks,
            "rank_blocks_source": "analysis/power.json chosen_rank_blocks",
            "rank_seeds_note": ("301.. are new (the stacked run used 101 and 102, the rank-cut run 201-204); each "
                                "seed fixes 600 new rank targets [a]G - R_j"),
            "segment_order": order,
            "within_segment_order": ("random.Random(2026101910 + block).shuffle (C), random.Random(2026102010 + block) (K), "
                                     "random.Random(2026102110) (O)"),
            "process_model": "one point per process, fresh process per run, one pinned CPU, one runner",
            "segment_upper_estimate_s": {"C": 240, "K": 1800, "O": 200},
            "timeout_s": {"ic_cold": 600, "ic_rank": 2400, "rho_tuned": 600},
            "time_guard": "skip a segment (rows skipped_time_guard) if elapsed + its estimate exceeds 300 min",
            "runtime_estimate": ("from run 38891404048: build and tests about 15 min; cold segment about 70 s (cR, cP "
                                 "about 23 s each, cPI about 17 s, rT 3 s); rank block about 950 s (kR about 200 s, "
                                 "kP and kPaa about 185 s if the local per-probe ratio holds, kPX about 350 s); "
                                 "%d blocks; total about 1.9 h, up to about 2.5 h on a slower runner" % blocks),
        },
        "gates": [
            "every scheduled row valid (exit 0, verified, schedule match, no memory event)",
            ("every IC process: lift_scan, Feistel, prefetch; the 16-byte compact table with 2^26 slots over the folded "
             "index (14,940,300 stored of 29,880,000 logical states); 29,878,182 table entries; logical-state blake3 "
             "and table-map digests equal B's (online.index_digest); no root bloom"),
            "per point: one scalar across every IC process (cold and rank) and rT, replayed as [d]G = Q in the pinned oracle",
            "per point: one relation (point indices) and one probe count across every IC process on the point",
            "Q0 (O1): cR and cP give the archived Feistel relation and scalar with 1,987,852 probes",
            ("rank arms: full rank, the arm's KIC_RANK_SOLVE recorded, and the written factor-log table equal to B's "
             "archived table, log for log"),
            ("per rank block: rank_relations_blake3, the per-attempt probe vector (600 entries), "
             "rank_root_calls_total and the point-addition counters (rank_padd_fallback_states, "
             "rank_padd_irregular_inputs, rank_padd_resolved_hits, rank_padd_swapped_pairs) identical across kR, "
             "kP, kPaa and kPX (the candidate keeps every relation, every probe and every pair order of the "
             "baseline, not only the table)"),
            ("frame counters: kR builds no frame and checks nothing; kP, kPaa and kPX build exactly one frame per "
             "rank attempt; kPX has rank_frame_plant_checked_inputs > 0 (every candidate of its rank stage compared "
             "with the rank-cut keys) and kP / kPaa have 0; rank_padd_plant_checked_inputs is 0 everywhere"),
        ],
        "controls_pass_rule": {
            "aa": ("E2E(kP, cP) / E2E(kPaa, cR) (blocks paired) and cold cP / cR (the same cold code) point "
                   "estimates both inside [0.97, 1.03]"),
            "planted": "rank stage kPX / kP (per-attempt cost, attempts paired within blocks), 95% bootstrap lower bound above 1",
            "otherwise": "verdict invalid",
        },
        "statistics": {
            "end_to_end_cold": ("E2E(k, c) = mean over the rank blocks of timing_ms.rank_stage of rank arm k + mean "
                                "over the cold points of cold_in_process_ms of cold arm c; the cold processes hold "
                                "setup + online, the rank processes the rank stage, so E2E = setup + index build + "
                                "rank stage + linear algebra + one-target online"),
            "primary": ("R = E2E(kR, cR) / E2E(kP, cP). Bootstrap, 10,000 draws, seed 20261019: the rank blocks "
                        "resampled with replacement; within each drawn block the attempt indices resampled with "
                        "replacement and used for both kR and kP (the gate makes attempt i the same target with "
                        "the same probes in both), each process's non-attempt time kept; the cold points "
                        "resampled, paired across cR and cP"),
            "primary_is": "the END-TO-END cold ratio; the rank-stage and online ratios are co-reported and never decide",
            "secondary": [
                "rank stage kR/kP: whole-stage ratio and per-attempt cost ratio (paired bootstrap), ns per probe per arm, kP/kPaa",
                "per-attempt ratio by probe-count tercile (does the gain depend on the attempt length)",
                "cold without rank, setup, online and peak RSS cR/cP (expected 1: same code)",
                ("pre-registered secondary cPI (lift_scan in the index build, on top of the candidate): "
                 "E2E(kR, cR) / E2E(kP, cPI) and cold cP / cPI; reported separately, never decides"),
                "the point-addition and frame counters per rank process",
                "rho ms/step from rT; S = cost / (rho ms/step) / sqrt(r) for E2E cold, cold without rank and online, per arm; delta S cR to cP; E2E cold gap IC / rT and online gaps to rT",
            ],
        },
        "decision_rule": {
            "improvement": "R lower bound > 1 (the rank-probe producer becomes the new n=83 end-to-end cold baseline)",
            "regression": "R upper bound < 1",
            "not_separated": "otherwise",
            "invalid": "any gate or control fails, or any scheduled row is missing (including time-guard skips)",
        },
        "multiplicity": "one primary statistic; every secondary (cPI included) is descriptive and never changes the verdict",
        "exactness_argument": (
            "E is defined over F_2, so the Frobenius phi(x, y) = (x^2, y^2) is a group automorphism of E(F_2^83) "
            "and T +- phi^s(R) = phi^s(phi^(-s)(T) +- R). The rank-cut loop computes, for every shift s and stored "
            "root R_k (its y recovered by the half-trace), the partners x(T +- R_{k,s}) with R_{k,s} = phi^s(R_k) "
            "by one point addition from the polynomial-basis (x, y) of R_{k,s}. The frame loop computes "
            "x(T_s +- R_k) with T_s = phi^(-s)(T) by the same addition formulas (lambda = (y(T_s) + y(R_k)) / D, "
            "lambda' = lambda + x(R_k) / D, D = x(T_s) + x(R_k), x = lambda^2 + lambda + x(T_s) + x(R_k) + a) and "
            "applies phi^s, a rotation of the normal-basis word. The two are the same field elements, so the "
            "emitted normal-basis partner words are equal bit for bit, in the same order (minus, plus, with the "
            "same recovered y), hence the same canonical keys, partner shifts, candidate indices and probe "
            "positions. The exceptional inputs coincide (x(R_{k,s}) = x(T) iff x(R_k) = x(T_s); x(R_{k,s}) = 0 "
            "iff x(R_k) = 0; x(T) = 0 iff x(T_s) = 0) and are solved by the S3 solver on the rank-cut loop's S3 "
            "input, formed on demand; a root failing the curve check falls back to the compact loop exactly as "
            "in the rank-cut loop; at every root-table hit the rank-cut loop's exact S3-order resolution runs "
            "unchanged on the same S3 input. So the first hit, the lift, the relation and the probe count of "
            "every attempt are the rank-cut loop's (hence the S3 loop's); the echelon and the factor-log table are "
            "B's. Tested on a 9-orbit base (every loop, both orders, the swapped emission order; the frame keys "
            "against the rank-cut keys; the Frobenius identity) and checked key by key on every candidate of every "
            "kPX rank stage."),
        "power": {"file": "analysis/power.json", "chosen_rank_blocks": blocks, "min_delta": power["min_delta"],
                  "power_at_min_delta": power["power"]["%.2f" % power["min_delta"]]["by_blocks"].get(str(blocks)),
                  "rejection_rate_at_no_effect": power["type_i_at_1.00"],
                  "note": ("the simulated rejection rate at no effect (E2E ratio 1.00) is above the nominal 0.025: "
                           "the prior's per-process A/A ratios (0.9969-1.0031 over four blocks) are a process-level "
                           "drift that four resampled blocks only partly resolve; an end-to-end effect of 1.02 or "
                           "more is detected with power 1.00, and the A/A control (E2E kP+cP / kPaa+cR inside "
                           "[0.97, 1.03]) checks the drift on the run itself")},
    }
    (HERE / "protocol.json").write_text(json.dumps(protocol, indent=1, sort_keys=True) + "\n")
    print(str(HERE / "protocol.json"))


if __name__ == "__main__":
    main()
