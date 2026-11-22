#!/usr/bin/env python3
"""Write `protocol.json`, the frozen design, with the digests of every file the run executes.

Run once, after `make_targets.py`, `power_check.py` and before
`make_schedule.py`; `restore.py` then checks every digest on the runner. The
design text lives here so that the protocol is generated, not hand-edited.
"""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXP = HERE.parent
REPO = EXP.parent
RP = EXP / "koblitz-n83-rankprobe-20261019"
BL = EXP / "koblitz-n83-bl-arm-20261014"
RC = EXP / "koblitz-n83-reconcile-20261014"
B = EXP / "koblitz-single-target-n83-tier1-20261014"


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def local_files():
    return {
        "restore": HERE / "restore.py",
        "protocol_builder": HERE / "make_protocol.py",
        "targets_builder": HERE / "make_targets.py",
        "cold_targets": HERE / "inputs/cold_targets.json",
        "archived_identities": HERE / "inputs/archived_identities.json",
        "schedule_builder": HERE / "make_schedule.py",
        "schedule_runner": HERE / "run_schedule.py",
        "receipt_verifier": HERE / "verify_receipt.py",
        "power_prior_builder": HERE / "make_power_prior.py",
        "power_prior": HERE / "inputs/power_prior.json",
        "power_check": HERE / "power_check.py",
        "power_result": HERE / "analysis/power.json",
        "host_cpu_record": REPO / "scripts/host_cpu_record.py",
        "isolated_bench": REPO / "scripts/isolated_bench.py",
    }


def sibling_files():
    """Files of frozen sibling experiments this run executes or reads, unchanged."""
    return {
        "rankprobe:arm.py": RP / "arm.py",
        "rankprobe:restore.py": RP / "restore.py",
        "rankprobe:protocol.json": RP / "protocol.json",
        "rankprobe:make_online_source.py": RP / "make_online_source.py",
        "rankprobe:check_log_table.py": RP / "check_log_table.py",
        "rankprobe:online/Cargo.toml": RP / "online/Cargo.toml",
        "rankprobe:online/Cargo.lock": RP / "online/Cargo.lock",
        "reconcile:arm.py": RC / "arm.py",
        "reconcile:restore_sources.py": RC / "restore_sources.py",
        "reconcile:protocol.json": RC / "protocol.json",
        "bl-arm:arm.py": BL / "arm.py",
        "bl-arm:bl_table.py": BL / "bl_table.py",
        "bl-arm:bl_tools.py": BL / "bl_tools.py",
        "bl-arm:control.py": BL / "control.py",
        "bl-arm:restore_sources.py": BL / "restore_sources.py",
        "bl-arm:protocol.json": BL / "protocol.json",
        "bl-arm:Cargo.toml": BL / "Cargo.toml",
        "bl-arm:Cargo.lock": BL / "Cargo.lock",
        "bl-arm:bl_src/bl_sg.rs": BL / "bl_src/bl_sg.rs",
        "bl-arm:bl_src/sg_bl_impl.rs": BL / "bl_src/sg_bl_impl.rs",
        "bl-arm:bl_src/bl_table_io.rs": BL / "bl_src/bl_table_io.rs",
        "bl-arm:bl_src/rung3_bl_impl.rs": BL / "bl_src/rung3_bl_impl.rs",
        "b:targets.json": B / "inputs/targets.json",
        "b:factor_logs_n83_K600.json": B / "tier1_github_38523707244/precompute/factor_logs_n83_K600.json",
    }


def ic_arm(wrapper_arm, kind, binary, role):
    return {"runner": "rankprobe", "wrapper": "../koblitz-n83-rankprobe-20261019/arm.py",
            "wrapper_arm": wrapper_arm, "kind": kind, "binary": binary, "bin_dir": "ic", "role": role}


def bl_arm(kind, role, table):
    return {"runner": "bl", "wrapper": "../koblitz-n83-bl-arm-20261014/arm.py", "kind": kind, "binary": "bl_sg",
            "bin_dir": "bl", "field": "fold", "lanes": 64, "reference_dp_bits": 6, "uses_table": table,
            "role": role}


def build():
    power = json.loads((HERE / "analysis/power.json").read_text())
    points = power["chosen_points"]
    targets = json.loads((HERE / "inputs/cold_targets.json").read_text())
    if len(targets["points"]) != points:
        raise SystemExit("cold panel size differs from the power check's choice")
    rp_protocol = json.loads((RP / "protocol.json").read_text())
    bl_protocol = json.loads((BL / "protocol.json").read_text())
    if bl_protocol["rho_reference"]["value"] != "rT770":
        raise SystemExit("the BL arm's protocol does not name rT770")
    blocks = [{"id": "K%d" % (i + 1), "rank_seed": 901 + i, "unit": "s%03d" % i} for i in range(4)]
    third = points // 3
    order = ["K1", "O1"] + ["C%d" % i for i in range(1, third + 1)] + ["K2"] + \
        ["C%d" % i for i in range(third + 1, 2 * third + 1)] + ["K3"] + \
        ["C%d" % i for i in range(2 * third + 1, points + 1)] + ["K4"]
    return {
        "schema": 1,
        "kind": "n83-bl-rankprobe-online-gap-tier1",
        "frozen_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "frozen_before_any_timing": True,
        "classification": ("MEASUREMENT of the distance to precomputation rho (AGENTS.md 'Success criterion', "
                           "'Distance to rho': report the gap to Bernstein-Lange where setup is excluded). It is "
                           "not an index-calculus improvement, it changes no IC code, and it never replaces or "
                           "promotes a baseline row; its figures fill the n=83 row's 'Online / BL' column."),
        "question": ("On EC1N83Ce1h35c7ced6b497 (a=1, n=83, r=8569786107849059), with the current n=83 baseline "
                     "(the rank-probe producer, arms cP / kP, koblitz-n83-rankprobe-20261019, run 39214027289), "
                     "how much faster online is a Bernstein-Lange precomputation rho whose precomputation costs "
                     "what the IC's precomputation costs (the BL-arm experiment's matched budget, measured in "
                     "this job), on 64 new public points; and what are the end-to-end cold S of IC, BL and the "
                     "tuned rho rT770 and each one's gap to rT770?"),
        "baseline_at_freeze": {
            "source": "docs/ic/BASELINES.md on origin/main 1158c2152 (fetched 2026-10-19), row n=83 a=1 K600",
            "row": ("the rank-probe producer (arms cP / kP), crypto 770f6a69, "
                    "koblitz-n83-rankprobe-20261019/protocol.json, run 39214027289: end-to-end cold S 6.390, "
                    "gap to rT770 64.0 [53.7, 78.0], online gap 0.129 [0.085, 0.183]; Online / BL: not measured "
                    "on this row (B's 235 [61, 645] is an older producer)"),
            "candidate_id": "IC1N83Ckb1fb99600PDP4s3rootindexRCguidedLAdenseTDsingleISO0hc0ecc1fffbd7",
            "online_source_sha256": rp_protocol["sources"]["online_source_sha256"],
            "in_flight_not_baseline": ["claude/n83-indexlift (run 39290913632, verdict pending)",
                                       "claude/n83-rotkey, claude/n83-k899, claude/n83-onlineframe, "
                                       "claude/n83-closure, claude/n83-knownlog (unpushed or unrun)"],
        },
        "sources": {
            "crypto_770f6a69": "770f6a6925a0d29b768bd79074f54a173e967fe7",
            "ic_restore": ("../koblitz-n83-rankprobe-20261019/restore.py: crypto 770f6a69 into its snapshots/r770 "
                           "(reconcile extraction, reconcile and B digests) and the rank-probe producer derived "
                           "by its make_online_source.py, checked against its own frozen protocol.json "
                           "(online_source_sha256 and every local digest)"),
            "bl_restore": ("../koblitz-n83-bl-arm-20261014/restore_sources.py: crypto 770f6a69 into its snapshot/ "
                           "and the BL arms generated by exact, counted edits, checked against its own frozen "
                           "protocol.json sources.sha256 and B's tier1_protocol.json"),
            "local_sha256": {key: sha256(path) for key, path in local_files().items()},
            "sibling_sha256": {key: sha256(path) for key, path in sibling_files().items()},
        },
        "arms": {
            "cP": ic_arm("cP", "ic_cold", "ic_online_rankprobe_r770",
                         "IC cold, the baseline row's cold arm: the rank-probe producer with B's verified cached "
                         "factor-log table (setup + one-target online); its online interval is the primary's "
                         "numerator"),
            "cPaa": ic_arm("cP", "ic_cold", "ic_online_rankprobe_r770",
                           "A/A of cP: the same arm and code in its own process at another position"),
            "kP": ic_arm("kP", "ic_rank", "ic_online_rankprobe_r770",
                         "IC rank stage, the baseline row's rank arm (KIC_RANK_SOLVE=frame): setup, rank stage "
                         "to full rank, linear algebra, one target; K1's process gives P_IC"),
            "rT": ic_arm("rT", "rho_tuned", "rho_tuned_r770",
                         "the tuned single-target rho rT770 (Fold/64/DP6), A's configured worker"),
            "BL": bl_arm("bl_sg", "Bernstein-Lange online on the rT770 walk (bl_sg --field fold, 64 lanes, DP 6) "
                                  "with this job's table loaded (BLAKE3-checked) before the target exists", True),
            "BLaa": bl_arm("bl_sg", "the BL-arm experiment's BL A/A: BL again on the same point and seed", True),
            "BLplain": bl_arm("bl_plain_sg", "step-identity control: the BL binary with no table and rT770's own "
                                             "jumps and DP rule, on Q0 at seed 831000", False),
        },
        "bl": {
            "machinery": ("koblitz-n83-bl-arm-20261014 (claude/n83-bl-arm, PR #918) unchanged: its generated "
                          "bl_sg, its bl_table.py (precompute and check), its arm.py (kinds bl_sg, bl_plain_sg), "
                          "its control.py and its frozen protocol.json (rho_reference rT770; bl.dp_bits 6, "
                          "bl_jump_seed 20261014, precompute_seed 20261015, the 256-round stop rule, the 40-byte "
                          "table format, oracle_sample 4096 with seed 2026101402)"),
            "budget": ("P_IC_ms = timing_ms.rank_stage + timing_ms.setup_total of this job's K1 kP process (the "
                       "BL-arm experiment's definition: one cold in-job IC run with the rank stage on the "
                       "execution CPU, one thread; base load, normal basis and self-test, root index, the rank "
                       "stage, setup's other phases). run_schedule.py --phase budget writes it to "
                       "ic_budget/precompute_receipt.json, which bl_table.py precompute reads"),
            "budget_excluded": ("as in the BL-arm experiment: the construction of the retained K600 base (427.5 ms "
                                "measured in koblitz-n83-replay-20261017), and linear algebra and the factor-log "
                                "write (tens of ms); this can only favour the IC"),
            "budget_pre_run_estimate_ms": 163646.0,
            "budget_pre_run_estimate_source": "mean rank_stage + setup_total of the four kP rows of run 39214027289",
            "matched_fraction_reported": "P_IC / (E2E(kP, cP) - mean cP online), a secondary",
        },
        "design": {
            "cold_points": points,
            "cold_targets_file": "inputs/cold_targets.json (role %s)" % targets["role"],
            "cold_arms": ["cP", "cPaa", "rT", "BL", "BLaa"],
            "q0_arms": ["cP", "BL", "BLplain", "rT"],
            "q0_seeds": {"cP": 7, "BL": 831000, "BLplain": 831000, "rT": 831000},
            "q0_point": rp_protocol["design"]["q0_point"],
            "rank_arms": ["kP"],
            "rank_blocks": blocks,
            "rank_seeds_note": "901-904 are new (stacked 101-102, rank-cut 201-204, rank-probe 301-304; the "
                               "scratch branches use 401-404, 501-504, 701, 801-816)",
            "rho_seed_base": 930000,
            "bl_seed_rule": "BL and BLaa use the rT seed of the same point (the BL-arm experiment's rule: "
                            "shared start streams, different jump tables)",
            "ic_seed": 7,
            "phases": {"budget": ["K1"], "panel": [s for s in order if s != "K1"]},
            "segment_order": order,
            "within_segment_order": ("random.Random(2026101960 + i).shuffle (C<i>), "
                                     "random.Random(2026102060 + b) (K<b>, one arm), random.Random(2026102160) (O1)"),
            "process_model": "one point per process, fresh process per run, one pinned CPU, one runner",
            "segment_upper_estimate_s": {"C": 180, "K": 900, "O": 120},
            "time_guard": "skip a segment (rows skipped_time_guard) if elapsed + its estimate exceeds 300 min",
            "timeout_s": {"ic_cold": 600, "ic_rank": 2400, "rho_tuned": 600, "bl_sg": 600, "bl_plain_sg": 900},
            "runtime_estimate": ("build and tests about 25 min (two crates); positive control about 2 min; K1 about "
                                 "170 s; BL precompute about P_IC; table checks about 6 min; cold segment about "
                                 "60 s (cP and cPaa about 23 s each, rT about 3 s, BL and BLaa about 4 s each with "
                                 "the table load); 64 segments plus K2-K4; total about 2.3 h, up to about 3 h"),
        },
        "statistics": {
            "primary": ("G = mean cP online_ms / mean BL online_ms over the %d cold points (the online gap, IC over "
                        "BL, as B's 235 was stated); 95%% percentile bootstrap, 10,000 draws, seed 2026101990, "
                        "the points resampled with each point's (cP, BL) pair kept together" % points),
            "primary_is": "a MEASUREMENT of the online distance to BL at matched precomputation, not an IC improvement",
            "secondary": [
                "rho over BL: mean rT online / mean BL online (BL's online speedup over the single-target rho)",
                "online gaps to rT770: cP / rT and BL / rT (means, bootstrap over points)",
                "end-to-end cold per arm: IC = E2E(kP, cP) = mean timing_ms.rank_stage over K1-K4 + mean cP "
                "cold_in_process_ms (the baseline row's definition); BL = BL precompute_ms + median BL setup_ms "
                "(curve, jumps, table read and insert) + mean BL online_ms (the BL-arm experiment's definition); "
                "rT = mean (setup_ms + online_ms) of rT",
                "S per arm = cold or online ms / (rT ms per step x sqrt(r)), this run's rT770 step",
                "end-to-end cold gaps to rT770: IC E2E / rT cold (bootstrap: blocks, attempts within blocks, "
                "points) and BL cold / rT cold (bootstrap over points); cold IC / BL (about 1 by construction)",
                "matched fraction P_IC / (E2E(kP, cP) - mean cP online)",
                "medians, rows with BL faster, Q0 per arm",
                "BL model check: mean BL steps / the frozen model at this table's covered count",
                "table: T, alpha = T * 2^dp / l, duplicate walk ends",
                "host: the host_cpu_record of the runner (model, flags, microcode, caches, kernel)",
            ],
            "bootstrap_draws": 10000,
            "bootstrap_seed": 2026101990,
        },
        "controls": {
            "ic_aa": "cold cP / cPaa and online cP / cPaa, ratio of means over the points: point estimates inside "
                     "[0.97, 1.03] (cold) and [0.95, 1.05] (online); and the gates make each point's relation and "
                     "probe count identical",
            "bl_aa": "the BL-arm experiment's: BL and BLaa walk steps identical on every point, and the geometric "
                     "mean of BL / BLaa online with its 95% bootstrap interval inside [0.9, 1.1]",
            "bl_positive": "bl-arm control.py --only pc69-rT770 (E_0 over GF(2^69), 256 known-answer targets, tables "
                           "at 2^17 and 2^18 steps): status PASS by its own gates (amendment A1), and its rows.jsonl "
                           "byte-identical to the archived run's (sha256 in inputs/archived_identities.json)",
            "bl_step_identity": "BLplain on Q0 at seed 831000 takes 12,592,070 steps, equal to this job's rT on Q0 at "
                                "seed 831000, and recovers 3141592653589793",
            "bl_table": "bl-arm bl_table.py check: regeneration byte-identical, every record verified by the "
                        "producer, a 4,096-record oracle.py sample",
            "bl_budget": "bl_table.py precompute receipt PASS (budget reached, overrun at most 1% + 50 ms) and its "
                         "budget equal to this job's P_IC",
        },
        "gates": [
            "every scheduled row present and valid (exit 0, verified, schedule match, no memory event)",
            "every IC process: the rank-probe arm.py checks (layout, fold, index digests, counters; kP: full rank "
            "and a factor-log table equal to B's archived table, log for log)",
            "per point: one scalar across every arm on the point (cP, cPaa, rT, BL, BLaa, and kP on its unit), "
            "replayed as [d]G = Q in the pinned oracle",
            "per point: one relation and one probe count across every IC process on the point",
            "Q0: cP gives the archived Feistel relation and scalar with 1,987,852 probes; BL, BLplain and rT give "
            "3141592653589793",
            "every BL row: solved by the precomputed table or by its own walk (recorded), the table's entry count "
            "loaded, BL and BLaa steps identical",
        ],
        "decision_rule": {
            "eligible": "every gate and every control passes and every scheduled row is present",
            "reading": {
                "bl_online_faster_than_ic": "eligible and the lower bound of G > 1",
                "ic_online_faster_than_bl": "eligible and the upper bound of G < 1",
                "not_separated": "eligible and the interval contains 1",
                "no_result": "not eligible: rows and failures are reported, no ratio is read",
            },
            "scope": ("instance-scoped Tier 1 (one GitHub runner, one pinned CPU, CPU-only; host class recorded by "
                      "scripts/host_cpu_record.py); a measured BL arm on this curve, base and budget; not a speed "
                      "of either method in general; no transfer to ECC2K-130 or E_0 over GF(2^83)"),
        },
        "power": {"file": "analysis/power.json", "chosen_points": points, "rule": power["rule"],
                  "median_width_ratio_at_chosen": next(c["median_width_ratio"] for c in power["cells"]["bl_scale_1.0"]
                                                       if c["n"] == points),
                  "note": "the prior is model-based (BL rows rescaled from B's budget); the interval's width ratio "
                          "does not depend on that scale"},
        "measurement_tier": "tier1_instance",
        "success_criterion": "AGENTS.md 'Success criterion' ('Distance to rho'); a measurement, never an improvement",
    }


def main():
    protocol = build()
    (HERE / "protocol.json").write_text(json.dumps(protocol, indent=1, sort_keys=True) + "\n")
    print(str(HERE / "protocol.json"))


if __name__ == "__main__":
    main()
