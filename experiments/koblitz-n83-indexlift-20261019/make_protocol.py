#!/usr/bin/env python3
"""Write the frozen protocol (`protocol.json`) of the n=83 index-lift experiment.

Run once, before any timing, after `make_power_prior.py`, `power_check.py`,
`make_targets.py` and `make_online_source.py`; `restore.py` re-checks every
digest it records. `koblitz-n83-rankprobe-20261019`'s `make_protocol.py`
with this experiment's arms, blocks, gates, shared rank stage and paired
bootstrap. `LAYOUT_DIGEST` is the stored layout that every IC process must
reproduce, measured once on Q0 by the local exactness run
(`smoke/exactness_cold_local.json`, before any timing; the same digests in
all four index modes).
"""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
LOG_TABLE = "../koblitz-single-target-n83-tier1-20261014/tier1_github_38523707244/precompute/factor_logs_n83_K600.json"
BINARY = "ic_online_indexlift_r770"
RANKPROBE = HERE.parent / "koblitz-n83-rankprobe-20261019"
LAYOUT_DIGEST = {
    "stored_states_blake3": None,
    "table_slots_blake3": None,
    "source": ("smoke/exactness_cold_local.json: Q0, KIC_INDEX_CANON = selected, lift, lift (sampled self-test) "
               "and lift_plant, one process each, identical in all four; also reproduced by kP and kPI in "
               "smoke/exactness_rank_local.json"),
}


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def layout_digest():
    local = json.loads((HERE / "smoke" / "exactness_cold_local.json").read_text())
    values = {json.dumps([(p["index_digest"] or {}).get(k) for k in ("stored_states_blake3", "table_slots_blake3")])
              for p in local["processes"].values()}
    if len(values) != 1 or not local["one_index_digest_set"]:
        raise SystemExit("the local index modes did not give one layout")
    stored, slots = json.loads(values.pop())
    return dict(LAYOUT_DIGEST, stored_states_blake3=stored, table_slots_blake3=slots)


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
                              "rank_canon": "lift", "rank_order": "feistel", "rank_probe": "target",
                              "rank_solve": "frame"}, **kw)
    arms = {
        "cP": cold(index_canon="selected",
                   role=("baseline cold: the rank-probe producer's cold path (koblitz-n83-rankprobe-20261019 arm "
                         "cP, the n=83 baseline once PR #980 lands): setup (index build with the selected "
                         "canonicalizer) + one-target online with the verified cached factor-log table")),
        "cPaa": cold(index_canon="selected", role="A/A control: a second process of cP"),
        "cPI": cold(index_canon="lift",
                    role=("candidate cold: cP with lift_scan canonicalizing the index build "
                          "(KIC_INDEX_CANON=lift); the pre-registered secondary cFI / cRI / cPI of three earlier "
                          "runs, here the primary")),
        "cPIT": cold(index_canon="lift", scan_selftest="sampled",
                     role=("pre-registered secondary (never decides): cPI with the Feistel scan order's "
                           "exhaustive bijection sweep skipped (KIC_SCAN_SELFTEST=sampled; the sampled inverse "
                           "check kept), about 1.9 s of setup input control in every archived cold process")),
        "cPIX": cold(index_canon="lift_plant",
                     role=("planted positive control: cPI plus the work it removes, redone: every index root's "
                           "selected canonical key and shift computed beside lift_scan's and compared (panic on "
                           "any difference), lift_scan's stored")),
        "rT": {"kind": "rho_tuned", "binary": "rho_tuned_r770",
               "role": "A's tuned rho rT770 (Fold/64/DP6), the strongest one-target rho at n=83, same points"},
        "kP": rank(index_canon="selected",
                   role=("shared rank stage, baseline index: the rank-probe producer's rank process (lift_scan, "
                         "Feistel, the 16-byte compact table over the folded index, KIC_RANK_SOLVE=frame) on the "
                         "index built with the selected canonicalizer, then one target")),
        "kPI": rank(index_canon="lift",
                    role=("shared rank stage, candidate index: kP's rank process on the index built with "
                          "lift_scan (the candidate pipeline's own rank process); the same rank code over the same "
                          "index, so it is pooled with kP into the shared rank stage and checked against it")),
    }
    cold_arms = ["cP", "cPaa", "cPI", "cPIT", "cPIX", "rT"]
    rank_arms = ["kP", "kPI"]
    rank_blocks = [{"id": "K%d" % (b + 1), "unit": "s%03d" % b, "rank_seed": 401 + b} for b in range(blocks)]
    order = ["O1"]
    per = points // blocks
    for b in range(blocks):
        order += ["C%d" % i for i in range(b * per + 1, (b + 1) * per + 1)] + ["K%d" % (b + 1)]
    order += ["C%d" % i for i in range(blocks * per + 1, points + 1)]
    protocol = {
        "schema": 1,
        "kind": "n83-indexlift-e2e-cold-tier1",
        "frozen_before_any_timing": True,
        "frozen_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "question": ("Does canonicalizing the root-index build with lift_scan (KIC_INDEX_CANON=lift) instead of "
                     "the selected canonicalizer lower the END-TO-END cold cost (setup + index build + rank stage "
                     "+ linear algebra + one-target online) of the rank-probe n=83 K600 producer on new targets, "
                     "with the stored states, the root table's layout, every relation, every probe count, every "
                     "scalar and the factor-log table unchanged?"),
        "success_criterion": "AGENTS.md 'Success criterion: iterative improvement of the index-calculus baseline'",
        "current_baseline": ("the rank-probe producer (koblitz-n83-rankprobe-20261019, run 39214027289, PR #980): "
                             "end-to-end cold 166.0 s (rank stage 143.7 s + cold 22.3 s), R over the rank-cut "
                             "producer 1.1033 [1.1010, 1.1056], S 6.39, gap to rT770 64.0 [53.7, 78.0]"),
        "history_of_the_candidate": {
            "reading": ("lift_scan in the index build has been a pre-registered secondary three times and never "
                        "the primary, so it was never promoted"),
            "state_fold_cFI": "koblitz-n83-state-fold-20261015, run 38819494806: setup about 1.33x (cF / cFI)",
            "rank_cut_cRI": ("koblitz-n83-rankcut-20261016, run 38891404048: cold without rank 1.3377; "
                             "end-to-end 1.3735 against the primary's 1.3336"),
            "rank_probe_cPI": ("koblitz-n83-rankprobe-20261019, run 39214027289: cold cP / cPI 1.3425; end-to-end "
                               "1.1424 against the primary's 1.1033; online 0.998"),
            "exactness_in_those_runs": ("all 56 archived lift-index processes (16 cFI, 20 cRI, 20 cPI) reproduced "
                                        "B's logical-state blake3 (every stored state's bytes in order, and every "
                                        "mate rebuilt from it), the table-map sum and xor and 29,878,182 entries, "
                                        "with 14,940,300 stored states, and one relation, probe count and scalar "
                                        "per point with every other IC process; no slot-order digest existed, "
                                        "which this protocol adds"),
        },
        "cost_structure_of_the_baseline": {
            "source": ("inputs/setup_profile_archived.json (make_setup_profile.py): run 39214027289, arms cP and "
                       "cPI, median cold phase over the 20 points, ms; figures/profile.*"),
            "median_cold_phase_ms": json.loads((HERE / "inputs" / "setup_profile_archived.json").read_text())["median_ms"],
            "reading": ("the index build is 88% of cold without rank; lift_scan removes about 5.7 s of it (the "
                        "selected canonicalizer on 29.9 M roots); the next setup piece is the Feistel scan "
                        "order's exhaustive bijection self-test, about 1.9 s, a check of the construction that "
                        "does not depend on the target, the base or the key the scan uses (secondary cPIT)"),
        },
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
            "layout_digest": layout_digest(),
            "factor_log_table": LOG_TABLE,
            "factor_log_table_sha256": sha256(HERE / LOG_TABLE),
            "tuned_rho_config": "snapshots/r770/research/n83_evaluation_20261012/optimization/selected_config.json",
            "cold_targets_file": ("inputs/cold_targets.json (role indexlift-cold-v1; disjoint from Q0, B's panel and "
                                  "every earlier n=83 panel of the law, including rankprobe-cold-v1 and the 64 eval "
                                  "points of n131-ref-walk-20261015)"),
            "q0_identity": rankprobe["online"]["q0_identity"],
            "cold_interval": rankprobe["online"]["cold_interval"],
            "rank_interval": rankprobe["online"]["rank_interval"],
            "online_interval": rankprobe["online"]["online_interval"],
        },
        "arms": arms,
        "design": {
            "cold_points": points,
            "cold_arms": cold_arms,
            "rank_arms": rank_arms,
            "q0_arms": ["cP", "cPI", "cPIT", "cPIX"],
            "q0_point": q0,
            "rho_seed_base": 890000,
            "rank_blocks": rank_blocks,
            "rank_blocks_source": "analysis/power.json chosen_rank_blocks",
            "rank_seeds_note": ("401.. are new (the stacked run used 101 and 102, the rank-cut run 201-204, the "
                                "rank-probe run 301-304); each seed fixes 600 new rank targets [a]G - R_j"),
            "segment_order": order,
            "within_segment_order": ("random.Random(2026101930 + block).shuffle (C), random.Random(2026102030 + block) (K), "
                                     "random.Random(2026102130) (O)"),
            "process_model": "one point per process, fresh process per run, one pinned CPU, one runner",
            "segment_upper_estimate_s": {"C": 300, "K": 900, "O": 300},
            "timeout_s": {"ic_cold": 600, "ic_rank": 2400, "rho_tuned": 600},
            "time_guard": "skip a segment (rows skipped_time_guard) if elapsed + its estimate exceeds 300 min",
            "runtime_estimate": ("from run 39214027289: build and tests about 15 min; cold segment about 105 s (cP, "
                                 "cPaa and cPIX about 22 s each, cPI about 16.6 s, cPIT about 14.7 s, rT 3 s); rank "
                                 "block about 330 s (kP and kPI about 165 s each); %d blocks; total about 1.2 h, up "
                                 "to about 1.6 h on a slower runner" % blocks),
        },
        "rank_stage_design": {
            "choice": ("shared: K = the mean over the rank blocks of each block's mean rank stage over kP and kPI; "
                       "E2E(c) = K + mean cold(c); the same K in the numerator and the denominator of the primary"),
            "why": ("only the cold path changes. KIC_INDEX_CANON is read only by the index build: the stored "
                    "states do not depend on it, and the table receives the same inserts in the same order, so "
                    "the rank stage runs identical code over an identical index (gated here byte for byte: the "
                    "stored-state and table-slot digests). A per-arm rank stage would add only the rank stage's "
                    "process-to-process drift (about +-0.3% per process in run 39214027289, 87% of the end-to-end "
                    "cost) to a ratio whose treatment is entirely in the cold term. The rank stage is still "
                    "measured in this run, because the end-to-end cost needs it on this host (no number is "
                    "imported from another run), and kPI checks on the runner that the candidate pipeline's own "
                    "rank process, on a lift_scan-built index, gives B's factor-log table with the baseline's "
                    "relations and probes"),
            "pooling": ("kP and kPI are pooled (attempt indices shared within a block) so that K is not taken from "
                        "either arm alone; the sharing control checks the pooling on the run"),
            "secondary": "E2E with each arm's own rank processes, (kP + cP) / (kPI + cPI), attempts paired",
        },
        "gates": [
            "every scheduled row valid (exit 0, verified, schedule match, no memory event)",
            ("every IC process: lift_scan, Feistel, prefetch; the 16-byte compact table with 2^26 slots over the folded "
             "index (14,940,300 stored of 29,880,000 logical states); 29,878,182 table entries; logical-state blake3 "
             "and table-map digests equal B's (online.index_digest); stored-state and table-slot blake3 equal the "
             "frozen layout (online.layout_digest: the same stored states and the same table layout, byte for "
             "byte); one index digest set across every IC process; the arm's index canonicalizer and scan "
             "self-test mode recorded; no root bloom"),
            ("planted index check: cPIX has index_plant_checked_inputs = 2 x 14,940,300 (every root of every stored "
             "state keyed by lift_scan and compared with the selected canonicalizer's key and shift); every other "
             "IC process 0"),
            "per point: one scalar across every IC process (cold and rank) and rT, replayed as [d]G = Q in the pinned oracle",
            "per point: one relation (point indices) and one probe count across every IC process on the point",
            "Q0 (O1): cP, cPI, cPIT and cPIX give the archived Feistel relation and scalar with 1,987,852 probes",
            ("rank arms: full rank, KIC_RANK_SOLVE=frame recorded, one frame per attempt, no rank-stage planted "
             "check, and the written factor-log table equal to B's archived table, log for log"),
            ("per rank block: rank_relations_blake3, the per-attempt probe vector (600 entries), "
             "rank_root_calls_total, the point-addition counters (fallback states, exceptional inputs, resolved "
             "hits, swapped pairs) and the frame builds identical across kP and kPI"),
        ],
        "controls_pass_rule": {
            "aa": ("E2E(cP) / E2E(cPaa) (shared rank stage) and cold cP / cPaa point estimates both inside "
                   "[0.97, 1.03]"),
            "sharing": ("rank stage per attempt kPI / kP (attempts paired within blocks) point estimate inside "
                        "[0.97, 1.03]: the rank stage on the lift_scan-built index costs what it costs on the "
                        "baseline index, so pooling them is honest"),
            "planted": "cold cPIX / cPI (points paired), 95% bootstrap lower bound above 1",
            "otherwise": "verdict invalid",
        },
        "statistics": {
            "end_to_end_cold": ("E2E(c) = K + mean over the cold points of cold_in_process_ms of cold arm c, K the "
                                "shared rank stage (rank_stage_design); the cold processes hold setup + online, the "
                                "rank processes the rank stage, so E2E = setup + index build + rank stage + linear "
                                "algebra + one-target online"),
            "primary": ("R = E2E(cP) / E2E(cPI). Bootstrap, 10,000 draws, seed 20261119: the rank blocks "
                        "resampled with replacement; within each drawn block the attempt indices resampled with "
                        "replacement and used for both rank processes of the block (the gate makes attempt i the "
                        "same target with the same probes in both), each process's non-attempt time kept; the "
                        "cold points resampled, paired across cP and cPI"),
            "primary_is": "the END-TO-END cold ratio; the cold, setup, index-build and online ratios are co-reported and never decide",
            "secondary": [
                "E2E with each arm's own rank processes: (kP + cP) / (kPI + cPI), attempts paired within blocks",
                ("pre-registered secondary cPIT: E2E(cP) / E2E(cPIT) and cold cPI / cPIT (the exhaustive scan "
                 "self-test skipped); reported separately, never decides"),
                "cold without rank cP / cPI, cP / cPIT, cPIX / cP; setup, index build, online, peak RSS and scan self-test cP / cPI",
                "rank stage kPI / kP per attempt and whole stage, ns per probe per arm, single-process cold of kP / kPI",
                "rho ms/step from rT; S = cost / (rho ms/step) / sqrt(r) for E2E cold, the rank stage, cold without rank and online, per arm; delta S cP to cPI; E2E cold gaps IC / rT and online gaps",
            ],
        },
        "decision_rule": {
            "improvement": "R lower bound > 1 (the index-lift producer becomes the new n=83 end-to-end cold baseline)",
            "regression": "R upper bound < 1",
            "not_separated": "otherwise",
            "invalid": "any gate or control fails, or any scheduled row is missing (including time-guard skips)",
        },
        "expected_effect": {
            "value": power["expected_e2e_ratio_from_archived_cPI"],
            "note": ("about 3.5% end to end, from run 39214027289's kP/kPaa rank stage and cP / cPI cold means; an "
                     "estimate from another run, not a claim, and not an input of the rule or the power check"),
        },
        "multiplicity": "one primary statistic; every secondary (cPIT included) is descriptive and never changes the verdict",
        "exactness_argument": (
            "KIC_INDEX_CANON changes one call in the index build: the canonical key and shift of each stored "
            "state's two normal-basis roots, (canonical, shift) = lift_scan_wide(root) instead of "
            "canonical_selected(root). The stored states are computed before and independently of that call "
            "(the S3 roots of each folded state, in the same order), so they are equal byte for byte. Both "
            "canonicalizers return the least rotation of the 83-bit word and the least shift that reaches it "
            "(83 is prime, so a word other than 0 and all-ones has one such shift, and both return 0 for those "
            "two), so every insert into the table is the same (key, packed value) in the same order, and the "
            "slot array is equal word for word. Everything downstream (the target scan, the rank stage, the "
            "relation, the probe counts, the echelon and the factor-log table) reads only the stored states and "
            "the table. Checked: on a 9-orbit base in every mode and on 400,000 random and structured words "
            "(crate tests); on the full K600 index locally (layout digests); and on the runner by cPIX on every "
            "root of every point and by the layout-digest gate on every IC process."),
        "power": {"file": "analysis/power.json", "chosen_rank_blocks": blocks, "min_delta": power["min_delta"],
                  "power_at_min_delta": power["power"]["%.3f" % power["min_delta"]]["by_blocks"].get(str(blocks)),
                  "rejection_rate_at_no_effect": power["type_i_at_1.000"],
                  "note": ("with the shared rank stage the rank stage's process drift is not in the ratio, so the "
                           "simulated rejection rate at no effect (the archived cR / cP pairs, the same cold code) "
                           "is at or below the nominal 0.025")},
    }
    (HERE / "protocol.json").write_text(json.dumps(protocol, indent=1, sort_keys=True) + "\n")
    print(str(HERE / "protocol.json"))


if __name__ == "__main__":
    main()
