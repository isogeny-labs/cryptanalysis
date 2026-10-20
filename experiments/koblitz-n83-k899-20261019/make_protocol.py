#!/usr/bin/env python3
"""Write the frozen protocol (`protocol.json`) of the n=83 K899 experiment.

Run once, before any Tier 1 timing, after `diag/make_identity.py`,
`make_power_prior.py`, `power_check.py`, `make_targets.py` and
`restore.py`; `restore.py` re-checks every digest it records. Built from
`koblitz-n83-rankprobe-20261019`'s `make_protocol.py`: the same producer,
arms at two factor-base sizes, a primary over K and the time budget fitted
from the diagnostic.
"""

import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
RP = HERE.parent / "koblitz-n83-rankprobe-20261019"
BINARY = "ic_online_rankprobe_r770"
LOG600 = "../koblitz-single-target-n83-tier1-20261014/tier1_github_38523707244/precompute/factor_logs_n83_K600.json"
BASE600 = "snapshots/r770/experiments/koblitz-single-target-n83-20261006/base_n83_K600.jsonl"
LAW_BAND = [0.90, 1.10]
GUARD_MIN = 300
JOB_LIMIT_MIN = 350
BUILD_MIN = 20


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    import restore  # noqa: E402  (this directory)

    rp = json.loads((RP / "protocol.json").read_text())
    power = json.loads((HERE / "analysis" / "power.json").read_text())
    identity = json.loads((HERE / "inputs" / "k899_identity.json").read_text())
    targets = json.loads((HERE / "inputs" / "cold_targets.json").read_text())
    diag = identity["diagnostic"]
    wall = diag["process_wall_s"]
    ro = rp["online"]
    k600 = {"base": BASE600, "base_file_sha256": sha256(HERE / BASE600), "base_hash": ro["base_hash"],
            "orbit_columns": 600, "regular_states": ro["regular_states"],
            "stored_states_folded": ro["stored_states_folded"],
            "root_table_slots_folded": ro["root_table_slots"]["folded"],
            "root_table_entries": ro["root_table_entries"], "index_digest": ro["index_digest"],
            "q0_identity": {k: ro["q0_identity"][k] for k in ("relation", "scalar", "probes_folded", "source")},
            "factor_log_table": LOG600, "factor_log_table_sha256": ro["factor_log_table_sha256"]}
    k899 = {k: v for k, v in identity["k899"].items()
            if k not in ("factor_log_table_oracle_status", "first_600_logs_equal_B_K600")}
    cold = lambda k, **kw: dict({"kind": "ic_cold", "binary": BINARY, "table": "compact", "fold": True, "K": k}, **kw)  # noqa: E731
    rank = lambda k, **kw: dict({"kind": "ic_rank", "binary": BINARY, "table": "compact", "fold": True, "K": k,  # noqa: E731
                                 "rank_canon": "lift", "rank_order": "feistel", "rank_probe": "target"}, **kw)
    arms = {
        "cP600": cold(600, role=("baseline cold: the rank-probe producer's cold path at K600 (koblitz-n83-rankprobe-"
                                 "20261019 arm cP, the n=83 baseline), setup + one-target online with B's verified "
                                 "cached factor-log table")),
        "cP899": cold(899, role=("candidate cold: the same producer and code on the nested K899 base (the K600 base "
                                 "is its exact prefix), with the frozen K899 factor-log table")),
        "cP899aa": cold(899, role="A/A control: a second cold process of cP899 on the same point"),
        "cPI600": cold(600, index_canon="lift",
                       role="pre-registered secondary (never decides): cP600 with lift_scan in the index build"),
        "cPI899": cold(899, index_canon="lift",
                       role="pre-registered secondary (never decides): cP899 with lift_scan in the index build"),
        "rT": {"kind": "rho_tuned", "binary": "rho_tuned_r770",
               "role": "A's tuned rho rT770 (Fold/64/DP6), the strongest one-target rho at n=83, same points"},
        "kP600": rank(600, rank_solve="frame",
                      role="baseline rank stage: the rank-probe producer's at K600 (arm kP of run 39214027289)"),
        "kP899": rank(899, rank_solve="frame",
                      role="candidate rank stage: the same loop on the K899 index, 899 columns, then one target"),
        "kP899aa": rank(899, rank_solve="frame", role="A/A control: a second process of kP899 (same seed, attempts)"),
        "kPX899": rank(899, rank_solve="frame_plant",
                       role=("planted positive control at K899: kP899 plus the work the frame loop removes, redone "
                             "(the rank-cut key derivation on every candidate of every state, compared field by "
                             "field with kP899's keys, panic on any difference, discarded); a known extra cost the "
                             "instrument must see at K899, and an exactness check of the frame keys at K899")),
    }
    blocks = [{"id": "K%d" % (i + 1), "rank_seed": 401 + i, "unit": "s%03d" % i} for i in range(4)]
    order = ["O1"]
    for b in range(4):
        order += ["C%d" % (5 * b + j + 1) for j in range(5)] + ["K%d" % (b + 1)]
    cold_arms = ["cP600", "cP899", "cP899aa", "cPI600", "cPI899", "rT"]
    rank_arms = ["kP600", "kP899", "kP899aa", "kPX899"]
    # time budget: diagnostic process walls (one runner, Q0); planted at ~1.97x the kP899 rank stage
    # (run 39214027289: kPX / kP 278.8 / 141.5 ns per probe), rho ~5 s, 1.5x margin.
    c_est = wall["cP600_a"] + 2 * wall["cP899_a"] + wall["cPI600"] + wall["cPI899"] + 5
    planted = wall["kP899"] + 0.97 * diag["rank_stage_ms"]["K899"] / 1e3
    k_est = wall["kP600"] + 2 * wall["kP899"] + planted
    o_est = wall["cP600_a"] + wall["cP899_a"]
    upper = {"C": math.ceil(1.5 * c_est), "K": math.ceil(1.5 * k_est), "O": math.ceil(1.5 * o_est)}
    expected_min = BUILD_MIN + (o_est + 20 * c_est + 4 * k_est) / 60
    upper_min = BUILD_MIN + (upper["O"] + 20 * upper["C"] + 4 * upper["K"]) / 60
    if upper_min > GUARD_MIN:
        raise SystemExit("the design's upper estimate %.0f min exceeds the %d-min guard" % (upper_min, GUARD_MIN))
    protocol = {
        "schema": 1,
        "kind": "n83-k899-e2e-cold-tier1",
        "frozen_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "frozen_before_any_timing": True,
        "success_criterion": "AGENTS.md 'Success criterion: iterative improvement of the index-calculus baseline'",
        "question": ("Does the nested K899 factor base (899 orbit columns, the largest K whose folded root table "
                     "keeps 2^27 16-byte slots, 2 GiB) lower the END-TO-END cold cost (setup + index build + rank "
                     "stage + linear algebra + one-target online) of the n=83 a=1 rank-probe producer against "
                     "K600, the baseline, on new targets and new rank seeds, with every answer verified, the "
                     "factor-log table of each K verified in the pinned oracle and the rank-stage probes inside "
                     "the frozen band around the law r / (166 E)?"),
        "current_baseline": ("the rank-probe producer (koblitz-n83-rankprobe-20261019, run 39214027289, PR #980): "
                             "K600, end-to-end cold 166.0 s (rank stage 143.7 s + cold 22.3 s), S 6.39, gap to "
                             "rT770 64.0 [53.7, 78.0]. The index-lift run (claude/n83-indexlift, run 39290913632) "
                             "had not landed when this protocol froze, so the baseline is the rank-probe producer; "
                             "its lift_scan index build is the pre-registered secondary pair cPI600 / cPI899"),
        "cost_model": {"source": "pre-registration analysis (not a result): E2E(K) ~ 146.9/a + 21.6 a^2 + 0.31 a + "
                                 "0.38/a^2 s with a = K/600; K899 about 151 s [142, 165], about 1.10x",
                       "probe_law": "mean probes per rank attempt = r / (166 E), E = root-table entries ~ 83 K^2",
                       "slot_cliff": "K899: 4 x 33,541,591 stored states < 2^27 slots; K900 needs 2^28"},
        "arms": arms,
        "design": {
            "cold_arms": cold_arms, "rank_arms": rank_arms, "q0_arms": ["cP600", "cP899"],
            "q0_point": rp["design"]["q0_point"], "cold_points": len(targets["points"]),
            "rank_blocks": blocks,
            "rank_seeds_note": ("401-404 are new (stacked 101-102, rank cut 201-204, rank probe 301-304, the K899 "
                                "diagnostic 8991); each seed fixes the rank targets [a]G - R_j of both K"),
            "rho_seed_base": 890000,
            "process_model": "one point per process, fresh process per run, one pinned CPU, one runner",
            "segment_order": order,
            "within_segment_order": ("random.Random(2026101930 + block).shuffle (C), random.Random(2026102030 + "
                                     "block) (K), random.Random(2026102130) (O)"),
            "segment_upper_estimate_s": upper,
            "timeout_s": {"ic_cold": 600, "ic_rank": 2400, "rho_tuned": 600},
            "time_guard": "skip a segment (rows skipped_time_guard) if elapsed + its estimate exceeds %d min" % GUARD_MIN,
            "time_budget": {"job_limit_min": JOB_LIMIT_MIN, "guard_min": GUARD_MIN, "build_min_allowance": BUILD_MIN,
                            "expected_total_min": round(expected_min, 1),
                            "upper_estimate_total_min": round(upper_min, 1),
                            "estimate_source": ("diagnostic process walls (%s, %s); planted rank stage at 1.97x "
                                                "kP899's; 1.5x margin" % (diag["where"], diag["run_url"]))},
        },
        "online": {
            "k": {"600": k600, "899": k899},
            "cold_targets_file": ("inputs/cold_targets.json (role k899-cold-v1; disjoint from Q0, B's panel and every "
                                  "earlier n=83 panel of the law, rankprobe-cold-v1 and indexlift-cold-v1 included)"),
            "curve_id": ro["curve_id"], "subgroup_order": ro["subgroup_order"], "sqrt_r": ro["sqrt_r"],
            "tuned_rho_config": ro["tuned_rho_config"],
            "cold_interval": ro["cold_interval"], "online_interval": ro["online_interval"],
            "rank_interval": ro["rank_interval"],
        },
        "law_band": {"band": LAW_BAND,
                     "statistic": ("per K: mean probes per rank attempt pooled over the rank blocks of kP600 / kP899, "
                                   "divided by r / (166 E_K), E_K the K's frozen root-table entries"),
                     "why": ("a gate, not a decision: 2,400 (K600) and 3,596 (K899) attempts give a standard error of "
                             "about 2.0% and 1.6% (per-attempt CV 0.97); the archived Feistel-order K600 ratios are "
                             "0.978 (run 39214027289) and 1.036 (run 38891404048); +-10% is about five standard "
                             "errors and admits both"),
                     "diagnostic_ratios": diag["law"]},
        "gates": [
            "every scheduled row valid (exit 0, verified, schedule match, no memory event)",
            ("every IC process: lift_scan targets, Feistel, prefetch; the 16-byte compact table over the folded "
             "index; its K's base hash, orbit columns, logical and stored states, slot count (2^26 at K600, 2^27 at "
             "K899), root-table entries and index digests equal online.k.<K>; no root bloom"),
            "per point: one scalar across every IC process of both K and rT, replayed as [d]G = Q in the pinned oracle",
            "per point and K: one relation (point indices) and one probe count across the IC processes of that K",
            "Q0 (O1): cP600 gives the archived K600 Feistel identity, cP899 the frozen K899 identity (relation, probes, scalar)",
            ("rank arms: full rank (K), the arm's KIC_RANK_SOLVE recorded, the written factor-log table equal to "
             "the K's frozen table log for log (B's at K600; at K899 inputs/factor_logs_n83_K899.json, every log "
             "re-verified in the pinned oracle by check_log_table.py in the job, its first 600 logs equal to B's)"),
            ("per rank block: kP899, kP899aa and kPX899 with one rank_relations_blake3, one per-attempt probe vector, "
             "one rank_root_calls_total and one set of point-addition counters"),
            ("frame counters: every rank arm builds exactly one frame per attempt; kPX899 checks every candidate "
             "(rank_frame_plant_checked_inputs > 0), the others check none"),
            "probe law band (law_band) at both K",
        ],
        "exactness_argument": (
            "K changes no code: the producer reads the base file and sizes the fold, the state array, the root "
            "table (slots = (4 x stored states).next_power_of_two()), the echelon and the factor-log table from "
            "its orbit columns; the 16-byte slot's four 11-bit fields hold K < 2048. Exactness at K899 cannot mean "
            "the K600 probes; it means: (1) the K899 factor-log table is self-consistent and verified (the producer "
            "checks [L_j]G = R_j for every column before any target; check_log_table.py re-checks every log in the "
            "pinned pure-Python oracle; the K600 base is an exact prefix of the K899 base and discrete logs of fixed "
            "points are unique mod r, so its first 600 logs equal B's); (2) every target's scalar is the same in "
            "every K600 process, every K899 process and rT, and replays in the oracle; (3) within K899, the rank "
            "arms agree attempt for attempt, and the planted arm checks the frame keys against the rank-cut keys "
            "on every candidate; (4) the probes per rank attempt fall in the frozen band around the law."),
        "statistics": {
            "end_to_end_cold": ("E2E(k, c) = mean over the rank blocks of timing_ms.rank_stage of rank arm k + mean "
                                "over the cold points of cold_in_process_ms of cold arm c"),
            "primary": ("R = E2E(kP600, cP600) / E2E(kP899, cP899). Bootstrap, 10,000 draws: the rank blocks "
                        "resampled with replacement (the same drawn ids for both arms); within each drawn block the "
                        "attempts of each arm resampled with replacement independently (the two K run different "
                        "attempts), each process's non-attempt time kept; the cold points resampled, paired across "
                        "cP600 and cP899"),
            "primary_is": "the END-TO-END cold ratio; the rank-stage, cold and online ratios are co-reported and never decide",
            "secondary": [
                "rank stage kP600 / kP899 (whole stage), ns per probe per arm (all attempts and the first 50), probes per attempt against the law",
                "cold without rank, setup, index build, online and peak RSS cP899 / cP600 (paired by point)",
                "pre-registered secondary pair cPI600 / cPI899 (lift_scan in the index build): E2E(kP600, cPI600) / E2E(kP899, cPI899) and E2E(kP600, cP600) / E2E(kP899, cPI899); never decide",
                "rho ms/step from rT; S = cost / (rho ms/step) / sqrt(r) for E2E cold, cold and online per arm; delta S K600 to K899; E2E cold gaps to rT, online gaps",
            ],
        },
        "controls_pass_rule": {
            "aa": ("E2E(kP899, cP899) / E2E(kP899aa, cP899aa) (attempts paired) and cold cP899 / cP899aa point "
                   "estimates both inside [0.97, 1.03]"),
            "planted": "rank stage kPX899 / kP899 per attempt (attempts paired within blocks), 95% bootstrap lower bound above 1",
            "otherwise": "verdict invalid",
        },
        "decision_rule": {
            "improvement": "R lower bound > 1 (K899 becomes the new n=83 end-to-end cold baseline)",
            "regression": "R upper bound < 1",
            "not_separated": "otherwise",
            "invalid": "any gate or control fails, or any scheduled row is missing (including time-guard skips)",
        },
        "multiplicity": "one primary statistic; every secondary (cPI included) is descriptive and never changes the verdict",
        "power": {"file": "analysis/power.json", "blocks": power["blocks"], "min_delta": power["min_delta"],
                  "by_effect": {e: {"power": v["power"], "mc_se": v["mc_se"]} for e, v in power["power"].items()},
                  "rejection_rate_at_no_effect": power["type_i_at_1.00"],
                  "predicted_e2e_ratio_from_diagnostic": diag["predicted_e2e_ratio"],
                  "information_only_other_block_counts": power["information_only_other_block_counts"],
                  "note": ("the rank stage's own work is random (probes per attempt geometric, CV 0.97) and the "
                           "two K run different attempts, so the primary's interval is set mostly by the 2,400 + "
                           "3,596 attempts, not by timing noise. Four blocks (the design) detect 1.10 with power "
                           "%.2f but the diagnostic's predicted %.3f only with %.2f (1.05: %.2f): a not_separated "
                           "verdict is the likely outcome if the diagnostic's per-probe ratio holds"
                           % (power["power"]["1.100"]["power"], diag["predicted_e2e_ratio"],
                              power["power"]["%.3f" % round(diag["predicted_e2e_ratio"], 3)]["power"],
                              power["power"]["1.050"]["power"]))},
        "diagnostic": {"file": "inputs/k899_identity.json", "where": diag["where"], "run_url": diag["run_url"],
                       "gates": diag["gates"], "derived": diag["derived"]},
        "sources": {
            "crypto_770f6a69": rp["sources"]["crypto_770f6a69"],
            "online_source_sha256": rp["sources"]["online_source_sha256"],
            "producer": ("the rank-probe producer, unchanged: koblitz-n83-rankprobe-20261019 make_online_source.py "
                         "(verbatim here with its five verbatim parents), output sha256 %s, the digest that "
                         "experiment froze" % rp["sources"]["online_source_sha256"]),
            "local_sha256": {key: sha256(path) for key, path in restore.local_files().items()},
        },
    }
    (HERE / "protocol.json").write_text(json.dumps(protocol, indent=1, sort_keys=True) + "\n")
    print(json.dumps({"upper": upper, "expected_min": round(expected_min, 1), "upper_min": round(upper_min, 1)}))


if __name__ == "__main__":
    main()
