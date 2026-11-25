#!/usr/bin/env python3
"""Write the frozen protocol (`protocol.json`) of the n=83 field-ops-2 on D4 experiment.

Run once, before any timing, after `restore.py --no-pin-check`, `local_identity.py`,
`make_targets.py`, `check_panel_disjoint.py`, `check_seed_disjoint.py`,
`make_power_prior.py` and `power_check.py`. `restore.py` re-checks every digest this file records.

The question. Two merged n=83 changes are stacked: the D4 closure base (K' = 4, 400 orbits,
`koblitz-n83-k4c400-20261107`, the current headline row's base) and the field-ops-2 producer
R1 (`koblitz-n83-fieldops2-20261107`, a constant reduce shift at n = 83). BOTH sides run the D4
base with the same header and table; only the binary differs. Side A is the field-ops
producer `ic_online_fieldops_r770` (the headline row), side B the field-ops-2 producer
`ic_online_fieldops2_r770`.
"""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
FO2 = HERE.parent / "koblitz-n83-fieldops2-20261107"
K4 = HERE.parent / "koblitz-n83-k4c400-20261107"
POINTS = 12
K = 3            # alternating primary pairs per point
K_AA = 2         # alternating A/A pairs per point
K_PLANTED = 1    # alternating planted pairs per point
SEED0 = 2600     # rank seed of pair j at point i: SEED0 + 3 i + j (2601 .. 2636)
ORDER_SEED0 = 2026110880
RHO_SEED_BASE = 1090000
DRAWS = 10000
BOOT_SEED = 20261081
DEADLINE_MIN = 165
BINARY_A, BINARY_B = "ic_online_fieldops_r770", "ic_online_fieldops2_r770"
OWNER_RULING = ("Owner ruling, 2026-11-07, given in chat: a closure base with K' >= 4 unknown-log columns counts "
                "as an index-calculus row. K' = 0 stays a known-log reference row.")


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    import restore  # noqa: E402  (this directory)

    fo2 = json.loads((FO2 / "protocol.json").read_text())
    k4 = json.loads((K4 / "protocol.json").read_text())
    if sha256(FO2 / "protocol.json") != restore.FO2_PROTOCOL_SHA256 or sha256(K4 / "protocol.json") != restore.K4_PROTOCOL_SHA256:
        raise SystemExit("a parent protocol differs from its pinned digest")
    power = json.loads((HERE / "analysis" / "power.json").read_text())
    ident = json.loads((HERE / "inputs" / "local_identity.json").read_text())
    targets = json.loads((HERE / "inputs" / "cold_targets.json").read_text())
    disjoint = json.loads((HERE / "inputs" / "panel_disjointness.json").read_text())
    seeds_new = json.loads((HERE / "inputs" / "seed_disjointness.json").read_text())
    if not ident["all_pass"]:
        raise SystemExit("the local identity test did not pass")
    if disjoint.get("disjoint") is not True or seeds_new.get("new") is not True:
        raise SystemExit("the panel or the rank seeds are not new on n=83")
    if not seeds_new["positive_control"]["finds_parent_schedule"]:
        raise SystemExit("the seed scan's positive control failed")
    if len(targets["points"]) != POINTS:
        raise SystemExit("panel size differs from the design")

    # ---- the one base: D4, verbatim from the k4c400 protocol (frozen, and reproduced by every process of run 42425640847)
    d4 = dict(k4["online"]["bases"]["D4"])
    d4["parent_source"] = ("koblitz-n83-k4c400-20261107 protocol.json online.bases.D4 (sha256 %s), every field "
                           "verbatim; both producers reproduce it locally (inputs/local_identity.json)"
                           % restore.K4_PROTOCOL_SHA256)
    d4_verify = json.loads((HERE / "inputs" / "local_verify_closure_D4.json").read_text())
    if d4_verify["status"] != "PASS" or d4_verify["base_hash"] != d4["base_hash"]:
        raise SystemExit("the D4 closure verification is missing, failed or is for another base")
    if sha256(HERE / d4["path"]) != d4["header_sha256"] or sha256(HERE / d4["factor_log_table"]) != d4["factor_log_table_sha256"]:
        raise SystemExit("the D4 header or table differs from the frozen identity")
    if not (d4["orbits_per_column"] == 100 and d4["index_orbits"] == 400 and d4["orbit_columns"] == 4):
        raise SystemExit("D4 is not 4 columns x 100 orbits")

    # ---- arms: the field-ops-2 protocol's arm configurations (A: parent's binary, B: R1) on the D4 base
    arms = {"rT": dict(fo2["arms"]["rT"], parent_source="the field-ops-2 protocol's arm rT, verbatim")}

    def d4_arm(src, role, **override):
        arm = dict(fo2["arms"][src], base="D4", role=role)
        for key in ("parent_source", "derived_from"):
            arm.pop(key, None)
        arm.update(override)
        arm["derived_from"] = "the field-ops-2 arm %s on base D4 (binary %s)" % (src, arm["binary"])
        return arm

    arms["kD4FO"] = d4_arm("kM38FO", "SIDE A rank stage: the field-ops producer on the D4 base")
    arms["cD4FO"] = d4_arm("cM38FO", "SIDE A cold: the field-ops producer on the D4 base")
    arms["kD4R1"] = d4_arm("kM38R1", "SIDE B rank stage: the field-ops-2 producer (R1) on the D4 base")
    arms["cD4R1"] = d4_arm("cM38R1", "SIDE B cold: the field-ops-2 producer (R1) on the D4 base")
    arms["kD4R1aa"] = dict(arms["kD4R1"], role="A/A copy of kD4R1")
    arms["cD4R1aa"] = dict(arms["cD4R1"], role="A/A copy of cD4R1")
    arms["cD4R1X"] = d4_arm("cM38R1X", ("PLANTED timing and exactness control: cD4R1 with KIC_INDEX_CANON=lift_plant: "
                                        "every index key is also checked against lift_scan and the selected "
                                        "canonicalizer (2 x stored states checks); same layout digests, slower index "
                                        "build"), index_canon="lift_plant")
    for name in ("kD4FO", "cD4FO"):
        assert arms[name]["binary"] == BINARY_A and "n83_const_reduce_shift" not in arms[name]["field_ops_pipeline"]
    for name in ("kD4R1", "cD4R1", "kD4R1aa", "cD4R1aa", "cD4R1X"):
        assert arms[name]["binary"] == BINARY_B and arms[name]["field_ops_pipeline"].endswith("+n83_const_reduce_shift")
    for name in arms:
        if name != "rT":
            assert arms[name]["index_build_pipeline"] == arms["kD4FO"]["index_build_pipeline"]
            assert arms[name]["rank_probe_pipeline"] == arms["kD4FO"]["rank_probe_pipeline"]
    rank_seeds = {"s%03d" % i: [SEED0 + 3 * i + j for j in range(1, K + 1)] for i in range(POINTS)}
    pw = power
    p = {
        "schema": 1,
        "kind": "n83-fo2d4-paired-e2e-tier1",
        "frozen_before_any_timing": True,
        "draft_not_frozen": False,
        "frozen_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "owner_ruling": {"date": "2026-11-07", "verbatim_in_chat": OWNER_RULING,
                         "consequence": "D4 (K' = 4) is an index-calculus row (k4c400, merged)",
                         "recorded_in": ["koblitz-n83-k4c400-20261107/protocol.json", "docs/ic/BASELINES.md"]},
        "question": ("Is the END-TO-END cold cost (setup + index build + rank stage + linear algebra + one-target online) "
                     "of the field-ops-2 producer R1 (ic_online_fieldops2_r770, a constant reduce shift at n = 83) lower "
                     "than the field-ops producer's (ic_online_fieldops_r770), BOTH on the D4 closure base (K' = 4, 400 "
                     "orbits), the current headline row's base? The two merged n=83 changes are stacked: only the "
                     "binary differs between the sides, and the base, header, table, points and rank seeds are the "
                     "same. Repeated alternating pairs and a 95% two-stage paired bootstrap lower bound above 1 "
                     "decide (AGENTS.md, 'CPU performance isolation gate', Tier 1)."),
        "why_this_run": ("R1 was measured against the field-ops producer on the M38 base only (1.0256 [1.0236, "
                         "1.0278], run 42424680756, mostly index build); D4 was measured against M38 on the field-ops "
                         "producer only (2.0014 [1.8777, 2.1308], run 42425640847). Ratios from different runs do not "
                         "compose, and D4 shifts the mix of stages (index build 40% of E2E instead of 55%, self-test on "
                         "the smaller domain, 4 rank attempts), so the stacked effect is measured, not multiplied. "
                         "Expected effect is about 2-3% [pcc:unverified]; this is an expectation, not a measurement."),
        "success_criterion": "AGENTS.md 'Success criterion: iterative improvement of the index-calculus baseline'",
        "tier_rule": fo2["tier_rule"],
        "baseline_row": {"experiment": "koblitz-n83-k4c400-20261107", "landed": "on main",
                         "run": "https://github.com/isogeny-labs/cryptanalysis/actions/runs/42425640847",
                         "binary": BINARY_A, "base": "D4",
                         "primary": "2.0014 [1.8777, 2.1308] over the M38 row on the same binary (side B of that run)",
                         "k4c400_protocol_sha256": restore.K4_PROTOCOL_SHA256,
                         "ratchet_rule": ("the row measured here is D4 on the field-ops producer; if this result's lower "
                                          "bound exceeds 1 and every gate passes, D4 on R1 is the next headline row, "
                                          "recorded with its delta against D4 on the field-ops producer")},
        "template": {"experiment": "koblitz-n83-k4c400-20261107", "landed": "on main",
                     "copied_verbatim": sorted(restore.VERBATIM)},
        "sources": {
            "producer": ("both producers are the field-ops-2 experiment's, derived and pinned by ITS restore.py (every "
                         "pin of its protocol.json): side A built from its online/ crate, side B from its online-b/ crate, "
                         "both with -C target-feature=+pclmulqdq; this experiment builds and runs them unchanged"),
            "fieldops2_protocol_sha256": restore.FO2_PROTOCOL_SHA256,
            "k4c400_protocol_sha256": restore.K4_PROTOCOL_SHA256,
            "fieldops_source_sha256": fo2["sources"]["online_source_sha256"],
            "fieldops2_source_sha256": fo2["sources"]["fieldops2_source_sha256"],
            "crypto_770f6a69": fo2["sources"]["crypto_770f6a69"],
            "field_ops_pipeline_side_A": arms["kD4FO"]["field_ops_pipeline"],
            "field_ops_pipeline_side_B": arms["kD4R1"]["field_ops_pipeline"],
            "rank_probe_pipeline": arms["kD4FO"]["rank_probe_pipeline"],
            "index_build_pipeline": arms["kD4FO"]["index_build_pipeline"],
            "closure_headers_sha256": {"D4": d4["header_sha256"]},
            "builds": {"side_A": "field-ops-2 experiment's online/ crate: %s and rho_tuned_r770" % BINARY_A,
                       "side_B": "field-ops-2 experiment's online-b/ crate: %s" % BINARY_B},
            "fieldops2_files_pinned": {key: sha256(path) for key, path in restore.fieldops2_files().items()},
            "local_sha256": {key: sha256(path) for key, path in restore.local_files().items()},
        },
        "online": {
            "bases": {"D4": d4},
            "curve_id": fo2["online"]["curve_id"],
            "subgroup_order": fo2["online"]["subgroup_order"],
            "lambda": fo2["online"]["lambda"],
            "sqrt_r": fo2["online"]["sqrt_r"],
            "tuned_rho_config": "../koblitz-n83-fieldops2-20261107/" + fo2["online"]["tuned_rho_config"],
            "cold_targets_file": ("inputs/cold_targets.json (role %s, %d points), disjoint from Q0, B's panel and every "
                                  "earlier n=83 panel including the k4c400 panel (make_targets.py EARLIER_ROLES; "
                                  "role-agnostic x/y scan in inputs/panel_disjointness.json, 0 hits)"
                                  % (targets["role"], POINTS)),
            "cold_interval": fo2["online"]["cold_interval"],
            "rank_interval": fo2["online"]["rank_interval"],
            "online_interval": fo2["online"]["online_interval"],
            "base_construction": ("D4: make_closure_base.py --columns 4 --norm 165 (the field-ops builder, unchanged), "
                                  "regenerated by restore.py to the SHA-256 the k4c400 experiment froze, verified by "
                                  "verify_closure.py before timing; not charged to any arm"),
        },
        "arms": arms,
        "design": {
            "points": POINTS, "primary_pairs_per_point": K, "aa_pairs_per_point": K_AA,
            "planted_pairs_per_point": K_PLANTED,
            "sides": {"A": ["kD4FO", "cD4FO"], "B": ["kD4R1", "cD4R1"], "Baa": ["kD4R1aa", "cD4R1aa"]},
            "planted_arms": ["cD4R1", "cD4R1X"],
            "side_rule": fo2["design"]["side_rule"],
            "pair_rule": ("a primary pair is one A side and one B side with the same point and the same rank seed. "
                          "Each point's K pairs run as 2K sides in strict alternation, ABAB... or BABA..., the starting "
                          "side drawn from random.Random(ORDER_SEED0 + i)"),
            "rank_stage_design": ("same rank seed per pair, not a shared rank stage: each side runs its own rank process on "
                                  "its own binary on the SAME D4 base. R1 changes how field products and squares are "
                                  "computed, not which values, so the rank work is the same on both sides (gated: identical "
                                  "relation digests, probe vectors, root calls and counters per seed across kD4FO, kD4R1 "
                                  "and kD4R1aa); the rank stage is timed on each side, and so are the cold processes"),
            "aa_rule": ("the A/A pairs compare B with Baa: kD4R1 / cD4R1 against kD4R1aa / cD4R1aa, the same arm twice, "
                        "alternating, same point and seed"),
            "planted_rule": ("a planted pair is cD4R1 and cD4R1X, cold processes only, alternating, with the start drawn "
                             "from the same generator"),
            "rho_rule": fo2["design"]["rho_rule"],
            "segment_rule": ("O1: Q0 on cD4FO and cD4R1, shuffled by random.Random(ORDER_SEED0 + 99). Then one segment "
                             "P<i> per point i = 1..POINTS in panel order. Its four sub-blocks (primary, aa, planted, "
                             "rho) run in an order shuffled by the point's generator"),
            "order_seed0": ORDER_SEED0,
            "rank_seed0": SEED0,
            "rank_seeds": rank_seeds,
            "rank_seeds_note": ("2601-2636 are new on n=83 (inputs/seed_disjointness.json; the positive control finds the "
                                "k4c400 schedule's 2501-2560). They are outside 2201-2236 (field-ops-2), 2301-2360 and "
                                "2501-2560 (k4c400). %d distinct seeds give %d D4 attempts (4 per seed) per binary for the "
                                "probe-law gate" % (POINTS * K, POINTS * K * 4)),
            "rho_seed_base": RHO_SEED_BASE,
            "q0_point": fo2["design"]["q0_point"],
            "q0_arms": ["cD4FO", "cD4R1"],
            "process_model": "one point per process, fresh process per run, one pinned CPU, one runner",
            "segment_upper_estimate_s": {"O": 100, "P": 300},
            "timeout_s": fo2["design"]["timeout_s"],
            "time_guard": ("before each segment: skip it (rows skipped_time_guard) if the elapsed job time plus the "
                           "larger of its upper estimate and 1.1x the longest segment of its panel so far exceeds "
                           "%d min. A skipped row makes the run invalid" % DEADLINE_MIN),
            "deadline_min": DEADLINE_MIN,
            "runtime_estimate": ("power.json schedule_minutes_modelled: about %.0f min for the 12 x 3 schedule (process "
                                 "walls of the k4c400 run); time guard %d min, job limit 180 min"
                                 % (power["schedule_minutes_modelled"]["12x3_e2e"], DEADLINE_MIN)),
        },
        "primary_choice": {
            "primary": "end to end (rank stage + cold process), not cold only",
            "why": ("The headline row is defined by its end-to-end cost, and R1 touches the rank stage as well as the cold "
                    "process, so a cold-only primary would measure another quantity. The A/A pairs of the k4c400 run "
                    "(identical work, same seed) put the per-pair noise of an E2E ratio at sd %.4f in log (cold %.4f), "
                    "so E2E is no noisier than cold; at 12 x 3 pairs the E2E design resolves a 1.010 effect with power "
                    "%.3f and 1.005 with %.3f (cold only: %.3f and %.3f), while a cold-only schedule would save about "
                    "%.0f min. The saving does not justify changing the estimand. Cold is co-reported as a secondary."
                    % (power["noise_of_one_pair_log_ratio_from_k4c400_AA_pairs"]["e2e"]["sd"],
                       power["noise_of_one_pair_log_ratio_from_k4c400_AA_pairs"]["cold"]["sd"],
                       pw["designs"]["e2e_12x3"]["1.010"]["power"], pw["designs"]["e2e_12x3"]["1.005"]["power"],
                       pw["designs"]["cold_12x3"]["1.010"]["power"], pw["designs"]["cold_12x3"]["1.005"]["power"],
                       power["schedule_minutes_modelled"]["12x3_e2e"] - power["schedule_minutes_modelled"]["12x3_cold_only"])),
            "frozen_before_data": True},
        "gates": [
            "every scheduled row present and valid (exit 0, verified, schedule match, no memory event), no time-guard skip",
            ("receipt integrity (verify_receipt.py, fail closed): every executed row's raw producer record decodes, "
             "its SHA-256 equals the wrapper summary's raw_result_sha256, and its arm, kind, panel, point and seed "
             "equal the frozen schedule's; serial, arm, point, seed, segment, command line and stdout file equal the "
             "schedule's; rows ran in schedule order; runner_start.json records this protocol's, this schedule's, "
             "arm.py's and run_schedule.py's SHA-256 and no smoke subset; every row ran its ARM's binary (by name "
             "and by the digest runner_start.json lists), unchanged at the end. An unknown gate is a failure"),
            ("every IC row's summary names its arm's rank_probe_pipeline and field_ops_pipeline (%s on side A; the same "
             "plus +n83_const_reduce_shift on side B)" % arms["kD4FO"]["field_ops_pipeline"]),
            "placement: every process's Cpus_allowed_list, read from /proc while it ran, is the one execution CPU",
            "host identity: the CPU record at the start and the end of the schedule has the same model, microcode and flags",
            ("before any timing: check_log_table.py: D4's header and table pass verify_closure.py --base --table "
             "--planted in the pinned oracle (three planted corruptions rejected), both SHA-256 pinned; the field-ops-2 "
             "crates' tests pass on both sides"),
            ("every IC process (arm.py): KIC_INDEX_CANON as the arm (lift; lift_plant in cD4R1X only); index roots "
             "checked 0 times, or 2 x stored states in cD4R1X; the full scan self-test; the arm's index_build_pipeline and "
             "field_ops_pipeline; D4's frozen base hash, columns, orbits, orbits per column, multiplier list, states, "
             "slots, root entries, logical-state and table-map digests; its frozen LAYOUT digests; cold: the frozen "
             "cached table's input digest; rank: the arm's rank_solve, K' relations, one frame per attempt"),
            "per point: one scalar across every IC process (both binaries, cold and rank) and rT, replayed as [d]G = Q in the pinned oracle",
            "per point: one relation and one probe count across every IC process of BOTH binaries",
            "one index and layout digest set across every process of both binaries, equal to D4's frozen one",
            "Q0 (O1): cD4FO and cD4R1 both give D4's frozen identity (inputs/local_identity.json)",
            "rank arms: full rank (K' relations), 0 failed attempts, 0 rows without gain, one frame per attempt, and the written factor-log table equal to D4's frozen verified table, log for log",
            "per rank seed: rank_relations_blake3, per-attempt probe vector, root calls and point-addition counters identical across every kD4FO, kD4R1 and kD4R1aa process with that seed",
            ("probe law (both binaries gated): pooled probes per relation of kD4FO and of kD4R1 over their %d distinct seeds "
             "(%d attempts each) over r / (166 E_D4), each inside [0.80, 1.20]; each over at least 64 attempts"
             % (POINTS * K, POINTS * K * 4)),
        ],
        "statistics": {
            "e2e_per_side": fo2["statistics"]["e2e_per_side"],
            "primary": ("R = sum over the %d primary pairs of E2E(A) / sum over the same pairs of E2E(B). 95%% "
                        "percentile interval from a two-stage paired bootstrap, %d draws, random.Random(%d): the "
                        "points drawn with replacement, then each drawn point's pairs drawn with replacement; A and "
                        "B of a pair are always drawn together" % (POINTS * K, DRAWS, BOOT_SEED)),
            "primary_is": "the paired END-TO-END ratio of the field-ops producer over R1, both on D4; every stage ratio is co-reported and never decides",
            "stage_secondary": ("four STAGE ratios, labelled stage secondaries, never deciding, in the primary pairs "
                                "with the same bootstrap: index build (timing_ms.index_build of the cold process) cD4FO / "
                                "cD4R1, scan self-test cD4FO / cD4R1, rank stage kD4FO / kD4R1, online cD4FO / cD4R1"),
            "pairing_basis": fo2["statistics"]["pairing_basis"],
            "secondary": [
                "geometric mean of the per-pair ratios E2E(A)/E2E(B), with the same bootstrap",
                "index build, scan self-test, rank stage and online (stage secondaries, labelled), paired",
                "cold, setup cD4FO / cD4R1, paired (the cold-only ratio the primary_choice compared)",
                "index build in the rank processes, paired",
                "E2E process CPU time and process wall A / B, with the same bootstrap",
                "peak RSS and minor faults of the cold processes",
                "per-point ratio, and the ratio by pair position and by side order",
                "observed coefficient of variation of the rank stage, online and E2E per side",
                "probe law of kD4FO and kD4R1; rank ns per probe; rho ms/step from rT; S per side; E2E cold gap over rT",
                "section 5a band: band_model.py (see `section_5a`)",
            ],
        },
        "section_5a": {
            "rule": ("AGENTS.md section 5a: every arm's unpriced native work, the matched rho's included, is priced at "
                     "0, 0.1 and 1 GAE per operation, and two arms are ranked only where the order holds across the "
                     "band (band.py of koblitz-n83-opcounts-20261023, run unchanged)"),
            "what_is_counted": ("rho: counted in this run (rT's own charges_setup_and_solve in every rT process). IC: "
                                "neither producer emits operation counts, so the IC units are a MODEL from the archived "
                                "counted run 39882571652, applied to THIS run's measured probes and attempts per side. "
                                "Both sides do identical group-operation work (gated), so the model gives A and B the SAME "
                                "units: it prices the D4 row against rho at the in-run gap and cannot see a field-"
                                "arithmetic speed-up. That is a property of the accounting, not a finding"),
            "script": "band_model.py", "reported": ["gap to rT at w = 0, 0.1, 1 for A and B",
                                                     "A vs B order across the band (identical by construction)"],
            "limit": ("factor-base construction and the linear algebra are not charged beyond la_*; no model "
                      "uncertainty; rho's scalar multiplications stay a bound (0 to 2 (r_bits - 1) GAE)")},
        "controls_pass_rule": {
            "aa": ("over the %d A/A pairs (B against Baa, identical work): the END-TO-END ratio of sums and the COLD ratio of "
                   "sums point estimates each inside [0.97, 1.03] (the field-ops-2 rule; power.json aa_control_12x3 gives "
                   "the null pass rate), the end-to-end interval is reported" % (POINTS * K_AA)),
            "planted": ("index build cD4R1X / cD4R1 over the %d planted pairs, 95%% bootstrap lower bound (pairs "
                        "resampled, 10,000 draws) above 1; every cD4R1X must also reproduce the frozen layout digests "
                        "and check 2 x stored states roots" % (POINTS * K_PLANTED)),
            "planted_exactness": "the three planted corruptions rejected by verify_closure.py on D4 before timing, and the crate tests passing",
            "otherwise": "verdict invalid",
        },
        "decision_rule": {
            "improvement": ("R lower bound > 1: a qualified Tier 1 end-to-end speed-up of R1 over the field-ops producer on "
                            "the D4 base. The baselines are updated only if every gate and control passes"),
            "regression": "R upper bound < 1",
            "not_separated": "otherwise",
            "invalid": "any gate or control fails or is unknown, or any scheduled row is missing (time-guard skips included)",
        },
        "multiplicity": "one primary statistic; every secondary is descriptive and never changes the verdict",
        "exactness_argument": {
            "producers": fo2["exactness_argument"]["fieldops2"],
            "base": ("D4 is the k4c400 experiment's frozen base: the pinned oracle checked its header and table, its "
                     "index and layout digests are reproduced by every process of both binaries, every rank process "
                     "reproduces the frozen table, and every recovered scalar replays [d]G = Q in the oracle"),
        },
        "power": {"file": "analysis/power.json", "label": power["label"], "min_delta": power["min_delta"],
                  "noise": power["noise_of_one_pair_log_ratio_from_k4c400_AA_pairs"],
                  "designs": {k: {"power_at_1.005": v["1.005"]["power"], "power_at_1.010": v["1.010"]["power"],
                                  "power_at_1.020": v["1.020"]["power"], "type_i": v["1.000"]["power"]}
                              for k, v in power["designs"].items()},
                  "aa_control": power["aa_control_12x3"], "schedule_minutes_modelled": power["schedule_minutes_modelled"]},
        "local_diagnostics": {"identity": "inputs/local_identity.json", "closure_check": "inputs/local_verify_closure_D4.json",
                              "label": "cloud-agent VM, shared; correctness and sizing only"},
        "bootstrap": {"draws": DRAWS, "seed": BOOT_SEED},
    }
    (HERE / "protocol.json").write_text(json.dumps(p, indent=1, sort_keys=True) + "\n")
    print(str(HERE / "protocol.json"))


if __name__ == "__main__":
    main()
