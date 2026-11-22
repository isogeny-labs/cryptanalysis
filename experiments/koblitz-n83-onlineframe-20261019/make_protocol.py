#!/usr/bin/env python3
"""Write the frozen protocol (`protocol.json`) of the n=83 online-frame experiment.

Run once, before any timing, after `make_power_prior.py`, `power_check.py`,
`make_targets.py` and `make_online_source.py`; `restore.py` re-checks every
digest it records. `koblitz-n83-rankprobe-20261019`'s `make_protocol.py`
with this experiment's arms, primary (online), gates and bootstrap.
"""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
LOG_TABLE = "../koblitz-single-target-n83-tier1-20261014/tier1_github_38523707244/precompute/factor_logs_n83_K600.json"
BINARY = "ic_online_onlineframe_r770"
RANKPROBE = HERE.parent / "koblitz-n83-rankprobe-20261019"
RANK_SEED = 701
SUCCESS_CRITERION_QUOTE = (
    "AGENTS.md, 'Success criterion: iterative improvement of the index-calculus baseline': \"the success "
    "criterion is a verified, measured improvement over the current index-calculus baseline. Every such "
    "improvement is a success and is reported as one.\" and, under 'Improvement': \"A stage-level win is "
    "reported as a stage improvement and becomes a pipeline improvement once it moves end-to-end `S`.\"")


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    import restore  # noqa: E402  (this directory)

    power = json.loads((HERE / "analysis" / "power.json").read_text())
    targets = json.loads((HERE / "inputs" / "cold_targets.json").read_text())
    rankprobe = json.loads((RANKPROBE / "protocol.json").read_text())
    q0 = rankprobe["design"]["q0_point"]
    points = len(targets["points"])
    if power["chosen_points"] is None or points != power["chosen_points"]:
        raise SystemExit("the panel size differs from the power check's chosen size")
    cold = lambda **kw: dict({"kind": "ic_cold", "binary": BINARY, "table": "compact", "fold": True}, **kw)  # noqa: E731
    arms = {
        "cS": cold(online_solve="s3",
                   role=("baseline: the rank-probe producer's cold path (koblitz-n83-rankprobe-20261019 arm cP, run "
                         "39214027289, the n=83 baseline row), setup + one-target online with the verified cached "
                         "factor-log table; its online scan is the batched S3 solve per candidate "
                         "(KIC_ONLINE_SOLVE=s3, the producer's default)")),
        "cF": cold(online_solve="frame",
                   role=("candidate: the same cold path with the online target scan on the rank stage's frame loop "
                         "(KIC_ONLINE_SOLVE=frame: x(T +- phi^s(R_k)) = phi^s(x(T_s +- R_k)), T_s = phi^(-s)(T) "
                         "tabulated once per target, partner roots by point addition, the S3 order resolved at a "
                         "hit)")),
        "cFaa": cold(online_solve="frame", role="A/A control: a second process of cF"),
        "cFX": cold(online_solve="frame_s3plant",
                    role=("planted positive control: cF plus the work it removes, redone: the S3 loop (batched S3 "
                          "solve of every candidate, its keys and its probe loop on a private counter) on every "
                          "state the scan reaches, compared with the frame loop's relation, probe counter, root "
                          "calls, relation checks and per-candidate keys (panic on any difference) and discarded")),
        "rT": {"kind": "rho_tuned", "binary": "rho_tuned_r770",
               "role": "A's tuned rho rT770 (Fold/64/DP6), the strongest one-target rho at n=83, same points"},
        "kP": {"kind": "ic_rank", "binary": BINARY, "table": "compact", "fold": True, "rank_canon": "lift",
               "rank_order": "feistel", "rank_probe": "target", "rank_solve": "frame", "online_solve": "s3",
               "role": ("shared rank stage K for the end-to-end secondary only: the rank-probe producer's rank "
                        "process (KIC_RANK_SOLVE=frame), unchanged code, one block; then one target with the "
                        "baseline online scan")},
    }
    cold_arms = ["cS", "cF", "cFaa", "cFX", "rT"]
    rank_blocks = [{"id": "K1", "unit": "s%03d" % (points // 2 - 1), "rank_seed": RANK_SEED}]
    order = ["O1"] + ["C%d" % i for i in range(1, points // 2 + 1)] + ["K1"] + \
        ["C%d" % i for i in range(points // 2 + 1, points + 1)]
    protocol = {
        "schema": 1,
        "kind": "n83-onlineframe-online-tier1",
        "frozen_before_any_timing": True,
        "frozen_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "question": ("Does running the one-target online scan of the rank-probe n=83 K600 producer on the rank "
                     "stage's frame loop (partner roots of T +- phi^s(R_k) by point addition in the target's "
                     "Frobenius frame, T_s = phi^(-s)(T) tabulated once, the S3 order resolved only at a root-table "
                     "hit) instead of the batched S3 solve per candidate lower the ONLINE time on new public "
                     "points, with every relation, probe count, root call, relation check and scalar unchanged?"),
        "success_criterion": SUCCESS_CRITERION_QUOTE,
        "success_criterion_reading": (
            "The primary decides a stage improvement of the online phase. Under the quoted rule an online "
            "improvement (primary lower bound > 1) is a verified, measured improvement over the baseline and a "
            "success; with no end-to-end regression (end-to-end secondary upper bound >= 1) it improves the "
            "baseline row's online S and online gap to rho and is recorded as a stage improvement. It is "
            "reported as a pipeline improvement only if the end-to-end secondary's lower bound also exceeds 1 "
            "('once it moves end-to-end S'). An end-to-end regression (upper bound < 1) blocks promotion."),
        "current_baseline": ("the rank-probe producer (koblitz-n83-rankprobe-20261019, run 39214027289, PR #980): "
                             "end-to-end cold 166.0 s (rank stage 143.7 s + cold 22.3 s, of which online 303.8 ms), "
                             "S 6.390 / online 0.01169, gap to rT770 64.0 [53.7, 78.0] end to end, online 0.129 "
                             "[0.085, 0.183]; online 221.4 ns per probe on the S3 loop against the rank stage's "
                             "141.5 ns per probe on the frame loop"),
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
            "cold_targets_file": ("inputs/cold_targets.json (role onlineframe-v1, %d points; disjoint from Q0, B's "
                                  "panel, every earlier n=83 panel of the law, the 64 eval points of "
                                  "n131-ref-walk-20261015, and the parallel branches' indexlift-cold-v1, "
                                  "rotkey-cold-v1 and k899-cold-v1)" % points),
            "q0_identity": rankprobe["online"]["q0_identity"],
            "cold_interval": rankprobe["online"]["cold_interval"],
            "rank_interval": rankprobe["online"]["rank_interval"],
            "online_interval": rankprobe["online"]["online_interval"],
        },
        "arms": arms,
        "design": {
            "cold_points": points,
            "cold_arms": cold_arms,
            "rank_arms": ["kP"],
            "q0_arms": ["cS", "cF", "cFX"],
            "q0_point": q0,
            "rho_seed_base": 900000,
            "rank_blocks": rank_blocks,
            "rank_seeds_note": ("701 is new (stacked 101-102, rank cut 201-204, rank probe 301-304, index lift and "
                                "rotation key 401-404 / 501.., K899 diagnostic 8991); it fixes 600 new rank targets"),
            "segment_order": order,
            "within_segment_order": ("random.Random(2026201910 + block).shuffle (C), random.Random(2026202010 + block) "
                                     "(K), random.Random(2026202110) (O)"),
            "process_model": "one point per process, fresh process per run, one pinned CPU, one runner",
            "segment_upper_estimate_s": {"C": 300, "K": 1200, "O": 300},
            "timeout_s": {"ic_cold": 600, "ic_rank": 2400, "rho_tuned": 600},
            "time_guard": "skip a segment (rows skipped_time_guard) if elapsed + its estimate exceeds 300 min",
            "runtime_estimate": ("from run 39214027289: build and tests about 20 min; a cold segment about 95 s "
                                 "(cS, cF, cFaa, cFX about 22.5 s each, rT about 3 s); the rank block about 170 s; "
                                 "%d points: about 1.7 h of schedule, about 2.1 h in all, up to about 2.8 h on a "
                                 "slower runner" % points),
        },
        "gates": [
            "every scheduled row valid (exit 0, verified, schedule match, no memory event)",
            ("every IC process: lift_scan, Feistel, prefetch; the 16-byte compact table with 2^26 slots over the folded "
             "index (14,940,300 stored of 29,880,000 logical states); 29,878,182 table entries; logical-state blake3 "
             "and table-map digests equal B's (online.index_digest); no root bloom"),
            "every IC process records the arm's online_solve in the target record and the summary",
            ("per point: one scalar across every IC process and rT, replayed as [d]G = Q in the pinned oracle; one "
             "relation (point indices, x codes and pinned intermediates), one probe count, one root-call count and "
             "one relation-check count across every IC process on the point (cS, cF, cFaa, cFX, and kP on its unit)"),
            "Q0 (O1): cS, cF and cFX give the archived Feistel relation and scalar with 1,987,852 probes",
            ("online counters: cS builds no frame and every online counter is 0; cF, cFaa and cFX build exactly one "
             "frame; only cFX checks states and candidates against the S3 loop, and it checks at least one; cF and "
             "cFaa check none"),
            ("the shared rank process kP: full rank, rank_solve frame, one frame per rank attempt, and the written "
             "factor-log table equal to B's archived table, log for log"),
        ],
        "controls_pass_rule": {
            "aa": "online cF / cFaa and cold cF / cFaa point estimates both inside [0.97, 1.03]",
            "planted": "online cFX / cF (points paired), 95% bootstrap lower bound above 1",
            "otherwise": "verdict invalid",
        },
        "statistics": {
            "primary": ("R_on = mean over the points of online_ms(cS) / mean over the points of online_ms(cF) "
                        "(online_ms = the producer's target_query_begin .. recovery_check_end interval of the one "
                        "target in its cold process). Bootstrap, 10,000 draws, seed 20261020: the points resampled "
                        "with replacement, paired across cS and cF; percentile 95% interval"),
            "primary_is": "the ONLINE ratio; the end-to-end cold ratio is a pre-registered secondary that never decides",
            "end_to_end_secondary": (
                "E2E(c) = K + mean over the points of cold_in_process_ms(c), with the SAME shared rank stage K = "
                "timing_ms.rank_stage of the one kP process in the numerator and the denominator (the reasoning of "
                "koblitz-n83-indexlift-20261019, origin/claude/n83-indexlift, README 'The rank stage: shared, and "
                "why': the rank stage runs identical code over an identical index, so its cost is not a treatment "
                "effect, and per-arm rank processes would add only their process drift; here the rank stage's code "
                "is byte for byte the rank-probe producer's and KIC_ONLINE_SOLVE is read only by the online scan). "
                "R_e2e = E2E(cS) / E2E(cF); bootstrap 10,000 draws, seed 20261021: kP's 600 attempts resampled "
                "(its non-attempt time kept) and the points resampled, paired across cS and cF. Expected about "
                "1.0006 (0.1 s of about 166 s); end-to-end regression iff its upper bound < 1"),
            "secondary": [
                "online ns per probe per IC arm; online cS / cF by probe-count tercile of the points",
                "cold, setup, index build and peak RSS cS / cF (expected 1: same setup code)",
                "online cF / cFaa (A/A) and cFX / cF (planted) intervals",
                "the online counters per arm (frames built, fallback states, exceptional inputs, resolved hits, swapped pairs, planted checks)",
                ("rho ms/step from rT; S = cost / (rho ms/step) / sqrt(r) per arm: online, cold, end-to-end cold "
                 "with K; delta S online and end to end cS to cF; online gaps cS / rT and cF / rT and end-to-end "
                 "gaps to rT"),
            ],
        },
        "decision_rule": {
            "improvement": ("R_on lower bound > 1: an online stage improvement; with the end-to-end secondary's upper "
                            "bound >= 1 (no end-to-end regression) the candidate's online S and online gap replace "
                            "the baseline row's, recorded as a stage improvement; a pipeline improvement only if "
                            "the end-to-end lower bound also exceeds 1 (see success_criterion_reading)"),
            "regression": "R_on upper bound < 1",
            "not_separated": "otherwise",
            "invalid": "any gate or control fails, or any scheduled row is missing (including time-guard skips)",
        },
        "multiplicity": "one primary statistic; every secondary (the end-to-end ratio included) is descriptive and never changes the verdict",
        "exactness_argument": (
            "The online scan and the rank stage call the same search, extract128::<CANON_LIFT, ORDER_FEISTEL, P> on "
            "one target point: the same folded index, the same Feistel state order keyed by the target's public "
            "hash, the same per-state candidates (shift outer, stored root inner), and a return at the first lifted "
            "relation. The online scan is a first hit for one target Q; a rank attempt is a first hit for one "
            "target [a]G - R_j. Only the probe loop P differs: PIPE_COMPACT (the S3 loop: x(R_{k,s}) mapped to "
            "the polynomial basis and the two roots of the third summation polynomial S3(x(R_{k,s}), x(T), X) "
            "solved in a batch) or PIPE_FRAME (the rank stage's loop). E is defined over F_2, so phi(x, y) = "
            "(x^2, y^2) is a group automorphism and T +- phi^s(R_k) = phi^s(T_s +- R_k) with T_s = phi^(-s)(T); "
            "the roots of S3(x(R_{k,s}), x(T), X) are exactly x(T + R_{k,s}) and x(T - R_{k,s}). The frame loop "
            "computes these two field elements by point addition from (x, y) of R_k and of T_s (tabulated once per "
            "target) and applies phi^s as a rotation of the normal-basis word, so each candidate's two partner "
            "words, canonical keys and shifts are the S3 loop's, possibly in the other order. The exceptional "
            "inputs (x(R_k) = x(T_s), x(R_k) = 0, x(T_s) = 0) and roots failing the curve check go to the S3 "
            "solver exactly as in the S3 loop. At a root-table hit the frame loop forms the S3 input, solves it "
            "and evaluates the pair in the S3 order at the S3 loop's probe positions, so the first lifted relation, "
            "its probe count, root calls and relation checks are the S3 loop's. This is the rank-probe "
            "experiment's exactness result for PIPE_FRAME against PIPE_COMPACT (its tests and four Tier 1 rank "
            "blocks), applied to the online target; here it is tested on a 9-orbit base through extract128, and "
            "cFX compares the S3 loop with the frame loop on every state of every scan it runs."),
        "power": {"file": "analysis/power.json", "chosen_points": power["chosen_points"],
                  "min_delta": power["min_delta"],
                  "power_at_min_delta": power["power"]["%.2f" % power["min_delta"]]["by_points"].get(str(points)),
                  "rejection_rate_at_no_effect": power["type_i_at_1.00"],
                  "note": ("prior: run 39214027289's cR / cP online times on its 20 cold points (two processes of the "
                           "same online code, per-point A/A ratio 0.992-1.018); 64 points is the frozen minimum, "
                           "more than power needs, so the A/A and planted controls and the exactness gates cover "
                           "more targets")},
    }
    (HERE / "protocol.json").write_text(json.dumps(protocol, indent=1, sort_keys=True) + "\n")
    print(str(HERE / "protocol.json"))


if __name__ == "__main__":
    main()
