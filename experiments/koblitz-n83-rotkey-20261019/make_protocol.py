#!/usr/bin/env python3
"""Write the frozen protocol (`protocol.json`) of the n=83 rotation-key experiment.

Run once, before any timing, after `make_power_prior.py`, `power_check.py`,
`make_targets.py` and `make_online_source.py`; `restore.py` re-checks every
digest it records. `koblitz-n83-rankprobe-20261019`'s `make_protocol.py`
with this experiment's arms, blocks, gates and paired bootstrap.
"""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
LOG_TABLE = "../koblitz-single-target-n83-tier1-20261014/tier1_github_38523707244/precompute/factor_logs_n83_K600.json"
BINARY = "ic_online_rotkey_r770"
RANKPROBE = HERE.parent / "koblitz-n83-rankprobe-20261019"


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    import restore  # noqa: E402  (this directory)

    power = json.loads((HERE / "analysis" / "power.json").read_text())
    targets = json.loads((HERE / "inputs" / "cold_targets.json").read_text())
    rankprobe = json.loads((RANKPROBE / "protocol.json").read_text())
    q0 = rankprobe["design"]["q0_point"]
    points = len(targets["points"])
    blocks = power["chosen_rank_blocks"]
    if blocks is None:
        raise SystemExit("the power check found no passing block count")
    cold = lambda **kw: dict({"kind": "ic_cold", "binary": BINARY, "table": "compact", "fold": True}, **kw)  # noqa: E731
    rank = lambda **kw: dict({"kind": "ic_rank", "binary": BINARY, "table": "compact", "fold": True,  # noqa: E731
                              "rank_canon": "lift", "rank_order": "feistel", "rank_probe": "target"}, **kw)
    arms = {
        "cP": cold(role=("baseline cold: the rank-probe producer's cold path (koblitz-n83-rankprobe-20261019 arm cP, "
                         "the n=83 baseline, PR #980), setup + one-target online with the verified cached "
                         "factor-log table")),
        "cK": cold(role=("candidate cold: the rotation-key producer's cold path, which is the rank-probe producer's "
                         "code (KIC_RANK_SOLVE is read only by the rank stage, which a cold process skips); its own "
                         "processes, so the candidate's end-to-end cost is measured on its own rows")),
        "rT": {"kind": "rho_tuned", "binary": "rho_tuned_r770",
               "role": "A's tuned rho rT770 (Fold/64/DP6), the strongest one-target rho at n=83, same points"},
        "kP": rank(rank_solve="frame",
                   role=("baseline rank stage: the rank-probe producer's (lift_scan keys, Feistel, the 16-byte "
                         "compact table over the folded index, the rank-cut loop in the target's Frobenius frame, "
                         "KIC_RANK_SOLVE=frame), then one target")),
        "kK": rank(rank_solve="rotkey",
                   role=("candidate rank stage: kP's loop keyed by the rotation-invariant key rotkey(v) = v^83 in "
                         "F2[X]/(X^83+1) (KIC_RANK_SOLVE=rotkey): a rotation-key copy of the compact table built "
                         "inside the rank-stage interval, keys of a state's partners in one carry-less batch, "
                         "lift_scan only at a hit (verified against the compact table); the same partner words, "
                         "probes and hits; then one target")),
        "kKaa": rank(rank_solve="rotkey", role="A/A control: a second process of kK"),
        "kKX": rank(rank_solve="rotkey_plant",
                    role=("planted positive control: kK plus the work it removes, redone: lift_scan of every "
                          "partner word, its compact-table lookup and the rotation key of the canonical word, "
                          "checked equal to kK's key and to its rotation-key lookup on every probe (panic on any "
                          "difference) and discarded")),
    }
    cold_arms = ["cP", "cK", "rT"]
    rank_arms = ["kP", "kK", "kKaa", "kKX"]
    rank_blocks = [{"id": "K%d" % (b + 1), "unit": "s%03d" % b, "rank_seed": 501 + b} for b in range(blocks)]
    # Rank blocks spread through the cold panel: O1, then C and K interleaved.
    order = ["O1"]
    per = points // blocks
    for b in range(blocks):
        order += ["C%d" % i for i in range(b * per + 1, (b + 1) * per + 1)] + ["K%d" % (b + 1)]
    order += ["C%d" % i for i in range(blocks * per + 1, points + 1)]
    smoke = json.loads((HERE / "smoke" / "design_inputs.json").read_text())
    protocol = {
        "schema": 1,
        "kind": "n83-rotkey-e2e-cold-tier1",
        "frozen_before_any_timing": True,
        "frozen_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "question": ("Does keying the rank-probe producer's rank-stage probes by a rotation-invariant key "
                     "(rotkey(v) = v^83 in F2[X]/(X^83+1), a complete invariant of the Frobenius rotation class of "
                     "the normal-basis word, computed by 5 squarings and 3 multiplications with pclmulqdq) instead "
                     "of the least rotation (lift_scan), with lift_scan run only at a table hit, lower the "
                     "END-TO-END cold cost (setup + index build + rank stage + linear algebra + one-target online) "
                     "of the rank-probe n=83 K600 producer on new targets and new rank seeds, with every rank "
                     "relation, every per-attempt probe count, every scalar and the factor-log table unchanged?"),
        "success_criterion": "AGENTS.md 'Success criterion: iterative improvement of the index-calculus baseline'",
        "current_baseline": ("the rank-probe producer (koblitz-n83-rankprobe-20261019, run 39214027289, PR #980): "
                             "end-to-end cold 166.0 s (rank stage 143.7 s + cold 22.3 s), R over the rank-cut "
                             "producer 1.1033 [1.1010, 1.1056], S 6.390, gap to rT770 64.0 [53.7, 78.0]; its rank "
                             "stage is 86.6% of end-to-end cold"),
        "cost_structure_of_the_baseline": {
            "source": "run 39214027289, arm kP (four processes, rank seeds 301-304)",
            "attempts": 600, "rank": 600, "mean_probes_per_attempt": 1690645, "ns_per_probe_rank": 141.54,
            "reading": ("the attempts and the probes per attempt are fixed by exactness (the gates keep them "
                        "identical), so the lever is the wall time per probe; lift_scan of both partners is the "
                        "largest piece of a probe in the rank-probe experiment's local profile (54-62 ns of 233)"),
        },
        "design_inputs_local": smoke,
        "sources": {
            "crypto_770f6a69": "770f6a6925a0d29b768bd79074f54a173e967fe7 (snapshots/r770 via ../koblitz-n83-reconcile-20261014/restore_sources.py)",
            "rankprobe_producer": ("koblitz-n83-rankprobe-20261019 make_online_source.py (make_rankprobe_source.py "
                                   "here, verbatim with its five parents), output sha256 "
                                   "d4394df35d065afbfb05022eac3006492239cc64b94de16fba501322cb578bb5"),
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
            "index_digest": rankprobe["online"]["index_digest"],
            "factor_log_table": LOG_TABLE,
            "factor_log_table_sha256": sha256(HERE / LOG_TABLE),
            "tuned_rho_config": "snapshots/r770/research/n83_evaluation_20261012/optimization/selected_config.json",
            "cold_targets_file": ("inputs/cold_targets.json (role rotkey-cold-v1; disjoint from Q0, B's panel and "
                                  "every earlier n=83 panel of the law, including rankcut-cold-v1, rankprobe-cold-v1, "
                                  "indexlift-cold-v1 (seeds 0..63) and the 64 eval points of n131-ref-walk-20261015)"),
            "q0_identity": rankprobe["online"]["q0_identity"],
            "cold_interval": rankprobe["online"]["cold_interval"],
            "rank_interval": (rankprobe["online"]["rank_interval"] + "; in kK, kKaa and kKX it also holds the "
                              "build of the rotation-key table (rank_rotkey_build_ms), so the candidate is charged "
                              "for it"),
            "online_interval": rankprobe["online"]["online_interval"],
        },
        "arms": arms,
        "design": {
            "cold_points": points,
            "cold_arms": cold_arms,
            "rank_arms": rank_arms,
            "q0_arms": ["cP", "cK"],
            "q0_point": q0,
            "rho_seed_base": 880000,
            "rank_blocks": rank_blocks,
            "rank_blocks_source": "analysis/power.json chosen_rank_blocks",
            "rank_seeds_note": ("501.. are new (the stacked run used 101 and 102, the rank-cut run 201-204, the "
                                "rank-probe run 301-304, the parallel index-lift experiment registers 401-404); each "
                                "seed fixes 600 new rank targets [a]G - R_j"),
            "segment_order": order,
            "within_segment_order": ("random.Random(2026102010 + block).shuffle (C), random.Random(2026102110 + block) (K), "
                                     "random.Random(2026102210) (O)"),
            "process_model": "one point per process, fresh process per run, one pinned CPU, one runner",
            "segment_upper_estimate_s": {"C": 200, "K": 1800, "O": 200},
            "timeout_s": {"ic_cold": 600, "ic_rank": 2400, "rho_tuned": 600},
            "time_guard": "skip a segment (rows skipped_time_guard) if elapsed + its estimate exceeds 300 min",
            "runtime_estimate": ("from run 39214027289: build and tests about 15 min; cold segment about 50 s (cP, cK "
                                 "about 23 s each, rT 3 s); rank block about 900 s (kP about 165 s, kK and kKaa "
                                 "less if the local per-probe ratio holds, kKX about 250 s); %d blocks; total about "
                                 "1.6 h, up to about 2.2 h on a slower runner" % blocks),
        },
        "gates": [
            "every scheduled row valid (exit 0, verified, schedule match, no memory event)",
            ("every IC process: lift_scan, Feistel, prefetch; the 16-byte compact table with 2^26 slots over the folded "
             "index (14,940,300 stored of 29,880,000 logical states); 29,878,182 table entries; logical-state blake3 "
             "and table-map digests equal B's (online.index_digest); no root bloom"),
            "per point: one scalar across every IC process (cold and rank) and rT, replayed as [d]G = Q in the pinned oracle",
            "per point: one relation (point indices) and one probe count across every IC process on the point",
            "Q0 (O1): cP and cK give the archived Feistel relation and scalar with 1,987,852 probes",
            ("rank arms: full rank, the arm's KIC_RANK_SOLVE recorded, and the written factor-log table equal to B's "
             "archived table, log for log"),
            ("per rank block: rank_relations_blake3, the per-attempt probe vector (600 entries), "
             "rank_root_calls_total and the point-addition counters (rank_padd_fallback_states, "
             "rank_padd_irregular_inputs, rank_padd_resolved_hits, rank_padd_swapped_pairs) identical across kP, "
             "kK, kKaa and kKX (the candidate keeps every relation, every probe and every pair order of the "
             "baseline, not only the table)"),
            ("frame counters: every rank arm builds exactly one frame per rank attempt; "
             "rank_frame_plant_checked_inputs and rank_padd_plant_checked_inputs are 0 everywhere"),
            ("rotation-key counters: kP builds no rotation-key table and verifies and checks nothing; kK, kKaa and kKX "
             "build exactly one table, with rank_rotkey_compact_entries = rank_rotkey_table_entries = 29,878,182 "
             "(rank_rotkey_collisions 0: no two stored classes share a key), the pclmulqdq kernel, and at least one "
             "verified hit per attempt (every rotation-key hit is checked against the compact table in the "
             "producer, panic otherwise); rank_rotkey_hit_verifies identical across kK, kKaa and kKX per block; kKX "
             "has rank_rotkey_plant_checked_probes > 0 (every probe of its rank stage compared with lift_scan and "
             "the compact table) and kK / kKaa have 0"),
        ],
        "controls_pass_rule": {
            "aa": ("E2E(kK, cK) / E2E(kKaa, cP) (blocks paired) and cold cK / cP (the same cold code) point "
                   "estimates both inside [0.97, 1.03]"),
            "planted": "rank stage kKX / kK (per-attempt cost, attempts paired within blocks), 95% bootstrap lower bound above 1",
            "otherwise": "verdict invalid",
        },
        "statistics": {
            "end_to_end_cold": ("E2E(k, c) = mean over the rank blocks of timing_ms.rank_stage of rank arm k + mean "
                                "over the cold points of cold_in_process_ms of cold arm c; the cold processes hold "
                                "setup + online, the rank processes the rank stage (with the rotation-key table "
                                "build in kK), so E2E = setup + index build + rank stage + linear algebra + "
                                "one-target online"),
            "primary": ("R = E2E(kP, cP) / E2E(kK, cK). Bootstrap, 10,000 draws, seed 20261020: the rank blocks "
                        "resampled with replacement; within each drawn block the attempt indices resampled with "
                        "replacement and used for both kP and kK (the gate makes attempt i the same target with "
                        "the same probes in both), each process's non-attempt time kept (it holds the "
                        "rotation-key table build); the cold points resampled, paired across cP and cK"),
            "primary_is": "the END-TO-END cold ratio; the rank-stage and online ratios are co-reported and never decide",
            "secondary": [
                "rank stage kP/kK: whole-stage ratio and per-attempt cost ratio (paired bootstrap), ns per probe per arm, kK/kKaa",
                "per-attempt ratio by probe-count tercile (does the gain depend on the attempt length)",
                "the rotation-key table build time per rank process (rank_rotkey_build_ms)",
                "cold without rank, setup, online and peak RSS cP/cK (expected 1: same code)",
                "the point-addition, frame and rotation-key counters per rank process",
                "rho ms/step from rT; S = cost / (rho ms/step) / sqrt(r) for E2E cold, cold without rank and online, per arm; delta S cP to cK; E2E cold gap IC / rT and online gaps to rT",
            ],
        },
        "decision_rule": {
            "improvement": "R lower bound > 1 (the rotation-key producer becomes the new n=83 end-to-end cold baseline)",
            "regression": "R upper bound < 1",
            "not_separated": "otherwise",
            "invalid": "any gate or control fails, or any scheduled row is missing (including time-guard skips)",
        },
        "multiplicity": "one primary statistic; every secondary is descriptive and never changes the verdict",
        "exactness_argument": (
            "A normal-basis word v of GF(2^83) is an element of R = F2[X]/(X^83+1) and the Frobenius rotates it, "
            "i.e. multiplies it by a power of X. rotkey(v) = v^83 in R. Invariant: (X^s v)^83 = X^(83 s) v^83 = "
            "v^83. Complete: X^83+1 = (X+1) Phi_83 with coprime factors and Phi_83 irreducible over F2 (2 has order "
            "82 mod 83: 2^41 = -1 mod 83), so R = F2 x F_{2^82}; v^83 = w^83 forces equal parity (a^83 = a in F2) "
            "and xi^83 = eta^83 in F_{2^82}, so xi = eta = 0 or xi/eta is an 83rd root of unity, and those are "
            "exactly the powers of X (order 83 in F_{2^82}^*); hence v = X^s w. So rotkey(v) = rotkey(w) iff "
            "lift_scan(v).0 = lift_scan(w).0, and the rotation-key table built from the compact table (key "
            "rotkey(c) for every stored canonical word c, the same packed value) is the same key -> value map: "
            "rotkey is injective on the stored canonical words, so no entry is merged or shadowed (the build "
            "reports compact entries - rotation-key entries, which the gate requires to be 0). The rotkey loop "
            "emits the frame loop's partner words in the frame loop's order (the same code) and looks up "
            "rotkey(partner) where the frame loop looks up lift_scan(partner).0, so every probe has the same hit "
            "status and, at a hit, the same packed value; the partner shift is then computed by lift_scan on the "
            "hit partner (the frame loop computed it for every partner), the hit is checked against the compact "
            "table (panic on a difference), and the frame loop's exact S3-order resolution, lift and relation "
            "check run unchanged. Hence the same first hit, lift, relation and probe count in every attempt, the "
            "same echelon and B's factor-log table. The definition of the probe count is unchanged: hits are "
            "resolved in the same order, so the probe-count identity is part of the gate, not an assumption. "
            "Tested: exhaustively at n = 11, 13, 19 (complete) and n = 7, 17 (2 not primitive: classes merge, the "
            "negative control); the carry-less kernel against the reference product and under rotation on random "
            "words; the rotation-key table against the compact table on every stored key of a 9-orbit base; "
            "the rotkey and rotkey_plant loops against the frame and S3 loops on 40 planted targets (both orders, "
            "folded and unfolded); and key by key against lift_scan and the compact table on every probe of every "
            "kKX rank stage."),
        "power": {"file": "analysis/power.json", "chosen_rank_blocks": blocks, "min_delta": power["min_delta"],
                  "power_at_min_delta": power["power"]["%.2f" % power["min_delta"]]["by_blocks"].get(str(blocks)),
                  "rejection_rate_at_no_effect": power["type_i_at_1.00"],
                  "note": power["note"]},
    }
    (HERE / "protocol.json").write_text(json.dumps(protocol, indent=1, sort_keys=True) + "\n")
    print(str(HERE / "protocol.json"))


if __name__ == "__main__":
    main()
