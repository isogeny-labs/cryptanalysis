#!/usr/bin/env python3
"""Write the frozen protocol (`protocol.json`) of the n=83 closure + index-lift experiment.

Run once, before any timing, after `restore.py --no-pin-check` (derives the
producer and regenerates the closure headers), `make_targets.py`,
`make_power_prior.py`, `power_check.py` and the local layout test
(`inputs/local_layout_test.json`, written by `smoke/exactness_local.py
cold`: every base's index and layout digests and Q0 identity with both
index canonicalizers). `restore.py` re-checks every digest this file
records.

`koblitz-n83-closure-20261019`'s `make_protocol.py` (commit 3761fd260) with
this experiment's baseline (the index-lift row), arms (every IC arm builds
its index with lift_scan), layout gate, new rank seeds, new shuffle and
bootstrap seeds and the hardened decision rule.

The closure bases' frozen records (base hash, columns, orbits, states, root
entries, index digests, factor-log tables, Q0 identities, probe-law bands)
are read from the closure protocol, copied verbatim to
`inputs/parent_closure_protocol.json`; B's K600 record and its layout
digests from the index-lift protocol (`../koblitz-n83-indexlift-20261019`).
"""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
INDEXLIFT = HERE.parent / "koblitz-n83-indexlift-20261019"
BINARY = "ic_online_closure_indexlift_r770"
PRIMARY, SECONDARY = "M38", "M10"
BLOCKS = 16
SEED0 = 1100
BASELINE_BLOCKS = (1, 5, 9, 13)          # kPI and the planted kM38IX
SECONDARY_BLOCKS = tuple(range(1, BLOCKS + 1, 2))  # kM10I: 8 blocks


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    import restore  # noqa: E402  (this directory)

    power = json.loads((HERE / "analysis" / "power.json").read_text())
    targets = json.loads((HERE / "inputs" / "cold_targets.json").read_text())
    layout = json.loads((HERE / "inputs" / "local_layout_test.json").read_text())
    if layout.get("all_pass") is not True:
        raise SystemExit("the local layout test did not pass")
    closure = json.loads((HERE / "inputs" / "parent_closure_protocol.json").read_text())
    indexlift = json.loads((INDEXLIFT / "protocol.json").read_text())
    points = len(targets["points"])
    il = indexlift["online"]
    k600 = dict(closure["online"]["bases"]["K600"])
    for key in ("base_hash", "factor_log_table", "factor_log_table_sha256", "root_table_entries"):
        if k600[key] != il[key]:
            raise SystemExit("closure and index-lift K600 records differ in " + key)
    if k600["index_digest"]["logical_states_blake3"] != il["index_digest"]["logical_states_blake3"]:
        raise SystemExit("closure and index-lift K600 index digests differ")
    if layout["layout_digest_lift"]["K600"] != {k: il["layout_digest"][k]
                                               for k in ("stored_states_blake3", "table_slots_blake3")}:
        raise SystemExit("local K600 layout differs from the index-lift protocol's frozen layout")
    k600["layout_digest"] = dict(layout["layout_digest_lift"]["K600"], source=(
        "koblitz-n83-indexlift-20261019 protocol.json online.layout_digest (frozen there, reproduced in all 110 IC "
        "processes of run 39290913632); reproduced here with both index canonicalizers on Q0 "
        "(inputs/local_layout_test.json)"))
    k600["role"] = "B's K600 header: 600 columns, one signed Frobenius orbit each (the baseline: the index-lift row)"
    bases = {"K600": k600}
    for name in (PRIMARY, SECONDARY):
        spec = dict(closure["online"]["bases"][name])
        spec["layout_digest"] = dict(layout["layout_digest_lift"][name], source=(
            "the local layout test (inputs/local_layout_test.json): Q0, KIC_INDEX_CANON = selected and lift, one "
            "process each, identical; the same processes reproduce the closure protocol's frozen logical-state and "
            "table-map digests, root entries and Q0 identity"))
        spec["source"] = "koblitz-n83-closure-20261019 protocol.json online.bases.%s (commit 3761fd260), verbatim" % name
        bases[name] = spec
    common = {"binary": BINARY, "table": "compact", "fold": True, "index_canon": "lift", "scan_selftest": "full"}
    cold = lambda base, **kw: dict(dict(common, kind="ic_cold", base=base), **kw)  # noqa: E731
    rank = lambda base, **kw: dict(dict(common, kind="ic_rank", base=base, rank_canon="lift",  # noqa: E731
                                        rank_order="feistel", rank_probe="target"), **kw)
    arms = {
        "cPI": cold("K600", role=("BASELINE cold: the index-lift row's cold path (koblitz-n83-indexlift-20261019 arm "
                                  "cPI: lift_scan index build) on B's K600 header with B's verified table")),
        "kPI": rank("K600", rank_solve="frame",
                    role=("BASELINE rank stage: the index-lift row's rank process (arm kPI: frame loop, lift_scan, "
                          "Feistel, 16-byte compact table over the lift_scan-built folded index), 600 guided "
                          "attempts on B's K600 header")),
        "cM38I": cold("M38", role=("PRIMARY candidate cold: the same code on the M38 closure header (16 columns, 608 "
                                   "orbits in the root index, lift_scan index build) with its verified 16-log table")),
        "kM38I": rank("M38", rank_solve="frame",
                      role=("PRIMARY candidate rank stage: the same loop on the M38 closure header: 16 guided attempts "
                            "[a]G - R_c to full rank 16")),
        "cM38Iaa": cold("M38", role="A/A control: a second cold process of cM38I"),
        "kM38Iaa": rank("M38", rank_solve="frame", role="A/A control: a second rank process of kM38I"),
        "kM38IX": rank("M38", rank_solve="frame_plant",
                       role=("planted positive control: kM38I with the rank-probe producer's frame_plant (the rank-cut "
                             "loop's key derivation redone and compared on every candidate), a known per-attempt cost "
                             "of about 1.8x (closure run 39305259093: 1.830 [1.795, 1.873]) that the timing must "
                             "detect")),
        "cM10I": cold("M10", role=("pre-registered SECONDARY candidate cold: the M10 closure header (60 columns, 600 "
                                   "orbits, lift_scan index build) with its verified 60-log table; never decides")),
        "kM10I": rank("M10", rank_solve="frame",
                      role="pre-registered SECONDARY candidate rank stage (60 attempts); never decides"),
        "rT": {"kind": "rho_tuned", "binary": "rho_tuned_r770",
               "role": "A's tuned rho rT770 (Fold/64/DP6), the strongest one-target rho at n=83, same points"},
    }
    cold_arms = ["cPI", "cM38I", "cM38Iaa", "cM10I", "rT"]
    rank_blocks = []
    for b in range(1, BLOCKS + 1):
        block_arms = ["kM38I", "kM38Iaa"]
        if b in BASELINE_BLOCKS:
            block_arms = ["kPI"] + block_arms + ["kM38IX"]
        if b in SECONDARY_BLOCKS:
            block_arms.append("kM10I")
        rank_blocks.append({"id": "K%d" % b, "unit": "s%03d" % (b - 1), "rank_seed": SEED0 + b, "arms": block_arms})
    order = ["O1"]
    for i in range(1, points + 1):
        order.append("C%d" % i)
        if i <= BLOCKS:
            order.append("K%d" % i)
    protocol = {
        "schema": 1,
        "kind": "n83-closure-indexlift-e2e-cold-tier1",
        "frozen_before_any_timing": True,
        "frozen_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "question": ("Does the Z[tau]-multiplier closure (M = 38 orbits per linear-algebra column, 16 columns; "
                     "koblitz-n83-closure-20261019), applied ON TOP OF the index-lift producer (lift_scan in the "
                     "root-index build; koblitz-n83-indexlift-20261019, the current n=83 row), lower the END-TO-END "
                     "cold cost (setup + index build + rank stage + linear algebra + one-target online) of the "
                     "index-lift row on new targets and new rank seeds, with every relation checked in the group, "
                     "every column log verified, every scalar verified, the probe law kept and the index-lift "
                     "layout reproduced byte for byte?"),
        "success_criterion": "AGENTS.md 'Success criterion: iterative improvement of the index-calculus baseline'",
        "current_baseline": ("the index-lift producer (koblitz-n83-indexlift-20261019, PR #981, run 39290913632): "
                             "the rank-probe producer plus KIC_INDEX_CANON=lift; end-to-end cold 165.2 s (shared rank "
                             "stage 148.4 s + cold 16.8 s), S 6.37, gap to rT770 62.9 [52.5, 78.5]"),
        "why_this_run": ("the closure run 39305259093 measured 6.444 [6.099, 6.785] end to end against the RANK-PROBE "
                         "producer (selected index build), not against the current row; docs/ic/BASELINES.md "
                         "requires an improvement over the row on the same instances. The two changes act on "
                         "different stages (the closure on the rank stage's column count, index-lift on the index "
                         "build), so they are expected to stack; this run measures the stacked producer against "
                         "the row itself"),
        "expected_effect": ("about %.1f end to end at the parents' archived means (power_check.py, "
                            "expected_ratio_at_prior_means; an estimate, not a claim)" % (
                                power["candidates"][PRIMARY]["expected_ratio_at_prior_means"])),
        "sources": {
            "crypto_770f6a69": "770f6a6925a0d29b768bd79074f54a173e967fe7 (snapshots/r770 via ../koblitz-n83-reconcile-20261014/restore_sources.py)",
            "rankprobe_producer": ("koblitz-n83-rankprobe-20261019 make_online_source.py (make_rankprobe_source.py here, "
                                   "verbatim with its five parents), output sha256 " + __import__("make_online_source").RANKPROBE_SHA256),
            "indexlift_producer": ("koblitz-n83-indexlift-20261019 make_online_source.py (make_indexlift_source.py here, "
                                   "verbatim; PR #981), output sha256 " + __import__("make_online_source").INDEXLIFT_SHA256),
            "closure_producer": ("koblitz-n83-closure-20261019 make_online_source.py (make_closure_source.py here, "
                                 "verbatim; branch claude/n83-closure, commit 3761fd260), output sha256 " +
                                 __import__("make_online_source").CLOSURE_SHA256),
            "composition": ("make_online_source.py: the closure's four counted replacements (closure_edits, imported) "
                            "applied to the index-lift text, plus one header comment; the two edit sets commute up to "
                            "the header comments (checked on every derivation)"),
            "online_source_sha256": sha256(restore.DERIVED),
            "local_sha256": {key: sha256(path) for key, path in restore.local_files().items()},
        },
        "online": {
            "bases": bases,
            "curve_id": il["curve_id"],
            "subgroup_order": il["subgroup_order"],
            "lambda": closure["online"]["lambda"],
            "sqrt_r": il["sqrt_r"],
            "tuned_rho_config": il["tuned_rho_config"],
            "cold_targets_file": ("inputs/cold_targets.json (role closureindexlift-cold-v1; disjoint from Q0, B's "
                                  "panel, every earlier n=83 panel of the law and every panel of the concurrent lanes "
                                  "n83-rotkey, n83-k899, n83-onlineframe, n83-closure, n83-knownlog and n83-blrp, "
                                  "regenerated and checked equal to each lane's committed file; no x-coordinate of "
                                  "the panel occurs anywhere in origin/main's experiments/ or research/)"),
            "cold_interval": il["cold_interval"],
            "rank_interval": il["rank_interval"],
            "online_interval": il["online_interval"],
            "base_construction": closure["online"]["base_construction"],
        },
        "arms": arms,
        "design": {
            "cold_points": points,
            "cold_arms": cold_arms,
            "rank_arms": ["kPI", "kM38I", "kM38Iaa", "kM38IX", "kM10I"],
            "q0_arms": ["cPI", "cM38I", "cM10I"],
            "q0_point": closure["design"]["q0_point"],
            "rho_seed_base": 1010000,
            "rank_blocks": rank_blocks,
            "rank_seeds_note": ("1101-1116 are new (used before on n=83: 7, 101-102, 201-204, 301-309, 401-404, "
                                "501-504, 701, 801-816, 901-904); each seed fixes K' new rank targets [a]G - R_c on "
                                "each base"),
            "blocks_note": ("kPI and kM38IX run in blocks K1, K5, K9, K13 (4 blocks of 600 and 16 attempts); kM38I and "
                            "kM38Iaa in all 16 blocks (256 attempts each); kM10I in the 8 odd blocks (480 attempts). "
                            "The baseline's and the candidates' attempts are different targets (different columns "
                            "and bases), so the primary bootstrap resamples each rank arm on its own"),
            "segment_order": order,
            "within_segment_order": ("random.Random(2026102150 + i).shuffle (C), random.Random(2026102170 + b) (K), "
                                     "random.Random(2026102190) (O)"),
            "process_model": "one point per process, fresh process per run, one pinned CPU, one runner",
            "segment_upper_estimate_s": closure["design"]["segment_upper_estimate_s"],
            "timeout_s": closure["design"]["timeout_s"],
            "time_guard": "skip a segment (rows skipped_time_guard) if elapsed + its estimate exceeds 300 min",
            "runtime_estimate": ("from runs 39305259093 and 39290913632: build and tests about 15 min, closure headers "
                                 "and their verification about 3 min; cold segment about 55 s (cPI, cM38I, cM38Iaa, "
                                 "cM10I about 12 s each, rT 3 s); rank block with kPI about 190 s, without about 45 s; "
                                 "total about 1.1 h, up to about 2 h on a slower runner"),
        },
        "gates": [
            "every scheduled row valid (exit 0, verified, schedule match, no memory event)",
            ("receipt integrity (verify_receipt.py, fail closed): every executed row's raw producer record decodes, its "
             "SHA-256 equals the wrapper summary's raw_result_sha256, and its arm, kind, panel, point and seed equal the "
             "frozen schedule's; every gate below must be true (an unknown gate is a failure)"),
            ("before any timing: B's table re-verified in the pinned oracle (check_log_table.py); each closure header "
             "regenerated from B's header with its frozen SHA-256 and checked by verify_closure.py in the pinned "
             "oracle (identity, multipliers, every orbit representative in the prime-order subgroup and equal to "
             "[(a + b lambda) mod r]R_c, all orbits distinct up to sign and Frobenius, every member and label, base "
             "hash); its table: [L_c]G = R_c for every column and [w L_c]G = alpha(R_c) for every orbit; three "
             "planted corruptions (a label, a duplicated orbit, a log) each rejected; and the closure logs equal B's "
             "archived logs of the same R_c"),
            ("every IC process: KIC_INDEX_CANON=lift recorded, 0 index roots checked against the selected "
             "canonicalizer, the full scan self-test; lift_scan target keys, Feistel, prefetch; the 16-byte compact "
             "table with 2^26 slots over the folded index; its base's frozen base hash, columns, orbits in the root "
             "index, logical and stored states, root entries, logical-state blake3 and table-map digests; and its "
             "base's frozen LAYOUT digests stored_states_blake3 and table_slots_blake3 (index-lift's gate: B's values "
             "d8cfe443... / 5f53764e... from the index-lift protocol for K600, the local layout test's for M38 and "
             "M10); no root bloom"),
            "per point: one scalar across every IC process (all three bases, cold and rank) and rT, replayed as [d]G = Q in the pinned oracle",
            "per point and base: one relation (point indices) and one probe count across the IC processes on that base",
            ("Q0 (O1): cPI gives B's archived Feistel relation, scalar and 1,987,852 probes; cM38I and cM10I give the "
             "scalar 3141592653589793 and their base's frozen Q0 relation and probe count (the closure protocol's)"),
            ("rank arms: full rank K', 0 failed attempts, the arm's KIC_RANK_SOLVE recorded, one frame per attempt, "
             "the producer's own [L_c]G = R_c check of every log, and the written factor-log table equal to its "
             "base's frozen verified table, log for log"),
            ("per rank block: rank_relations_blake3, the per-attempt probe vector, rank_root_calls_total and the "
             "point-addition counters identical across kM38I, kM38Iaa and kM38IX"),
            ("probe law: the primary rank arm kM38I's pooled mean probes per relation over its distinct attempts (one "
             "process per block, 256 attempts), divided by law = r / (166 E) with E its base's frozen root entries, "
             "inside [0.80, 1.20] (the closure's band). The secondary kM10I's ratio and its band [0.85, 1.15] are "
             "reported in detail.probe_law_gate and decide only how the secondary is read"),
            "frame counters: kM38IX has rank_frame_plant_checked_inputs > 0, every other rank arm 0; rank_padd_plant_checked_inputs 0 everywhere",
        ],
        "controls_pass_rule": {
            "aa": ("E2E(kM38I, cM38I) / E2E(kM38Iaa, cM38Iaa) (blocks paired) and cold cM38I / cM38Iaa point estimates "
                   "both inside [0.97, 1.03]"),
            "planted": "rank stage kM38IX / kM38I (per-attempt cost, attempts paired within blocks), 95% bootstrap lower bound above 1",
            "planted_exactness": "the three planted corruptions rejected by verify_closure.py for both closure bases (workflow step before timing)",
            "otherwise": "verdict invalid",
        },
        "statistics": {
            "end_to_end_cold": ("E2E(k, c) = mean over k's rank blocks of timing_ms.rank_stage of rank arm k + mean "
                                "over the cold points of cold_in_process_ms of cold arm c; the cold processes hold "
                                "setup + online, the rank processes the rank stage, so E2E = setup + index build + "
                                "rank stage + linear algebra + one-target online"),
            "primary": ("R = E2E(kPI, cPI) / E2E(kM38I, cM38I). Bootstrap, 10,000 draws, seed 20261219: the "
                        "baseline's blocks resampled with replacement and its attempts resampled within each drawn "
                        "block; the candidate's blocks and attempts likewise, independently (different targets); each "
                        "process's non-attempt time kept; the cold points resampled, paired across cPI and cM38I"),
            "primary_is": "the END-TO-END cold ratio; the rank-stage and cold ratios are co-reported and never decide",
            "secondary": [
                "R10 = E2E(kPI, cPI) / E2E(kM10I, cM10I) (pre-registered secondary candidate; never decides)",
                "E2E(kM10I, cM10I) / E2E(kM38I, cM38I)",
                "rank stage kPI / kM38I and kPI / kM10I (whole stage, means over blocks); attempts and ns per probe per arm",
                "probe law per rank arm: pooled mean probes per relation / law with a bootstrap interval (kPI, kM38I, kM10I)",
                "cold without rank, setup, online, index build and peak RSS: cPI / cM38I, cPI / cM10I",
                "rows without gain and the point-addition counters per rank process",
                "rho ms/step from rT; S per arm; delta S cPI to cM38I; E2E cold gap IC / rT and online gaps",
            ],
        },
        "decision_rule": {
            "improvement": ("R lower bound > 1 (the closure + index-lift producer, M38, becomes the new n=83 "
                            "end-to-end cold baseline row)"),
            "regression": "R upper bound < 1",
            "not_separated": "otherwise",
            "invalid": ("any gate or control fails or is unknown, or any scheduled row is missing (including "
                        "time-guard skips)"),
        },
        "multiplicity": "one primary statistic; every secondary (M10 included) is descriptive and never changes the verdict",
        "exactness_argument": (
            closure["exactness_argument"] + " With KIC_INDEX_CANON=lift the index build keys every stored state's two "
            "normal-basis roots with lift_scan instead of the selected canonicalizer; both return the least rotation "
            "of the 83-bit word and the least shift reaching it, the stored states are computed before and "
            "independently of that call, so the table receives the same inserts in the same order and its slot array "
            "is the same word for word (index-lift's argument). The layout digests gate this per process on every "
            "base, so every relation, probe count, rank table and scalar of a lift-built index is the "
            "selected-built index's."),
        "power": {"file": "analysis/power.json", "min_delta": power["min_delta"],
                  "power_at_min_delta": power["power_at_min_delta"],
                  "rejection_rate_at_no_effect": power["type_i_at_1.00"],
                  "modelled": {c: t["cells"]["modelled"] for c, t in power["candidates"].items()},
                  "expected_ratio_at_prior_means": {c: t["expected_ratio_at_prior_means"]
                                                    for c, t in power["candidates"].items()},
                  "law_gate": {c: t["cells"]["law_gate"] for c, t in power["candidates"].items()}},
    }
    (HERE / "protocol.json").write_text(json.dumps(protocol, indent=1, sort_keys=True) + "\n")
    print(str(HERE / "protocol.json"))


if __name__ == "__main__":
    main()
