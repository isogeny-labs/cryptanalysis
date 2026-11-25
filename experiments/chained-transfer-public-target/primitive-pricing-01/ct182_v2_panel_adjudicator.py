#!/usr/bin/env python3
"""CT182: versioned offline-only counterbalanced cold-transfer panel adjudicator.

No Rust is executed; no runtime measurements or complete ECDLP are claimed.
v1 producer evidence is never silently reinterpreted as v2 evidence.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import random
import statistics

import ct179_panel_adjudicator as legacy
import ct181_order_design as design

SCHEMA = "ct182-counterbalanced-cold-public-process-panel/v2"
REPORT_SCHEMA = "ct182-counterbalanced-cold-transfer-adjudication/v2"
ORDER_SCHEDULE = "ct181-block-packet-parity-ABBA-BAAB/v2"
ARM_NAME = {"A": "direct_composite", "B": "strongest_retained_lift_chain"}
N = 48 * design.BLOCKS * len(design.ABBA)


def roster():
    for block, packet, position, arm in design.roster(counterbalanced=True):
        yield block, packet, position, ARM_NAME[arm]


def roster_sha256():
    """Hash exact ordered wire-roster values, not only the nominal schedule."""
    encoded = json.dumps(list(roster()), separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(encoded.encode("ascii")).hexdigest()


def paired_statistics_v2(matrix, rows):
    legacy.refuse(len(matrix) == design.BLOCKS * 48,
                  "v2 matrix missing/extra packet-block keys")
    packet_logs, aa_drift, order_effects = {}, {}, {}
    for i in range(48):
        changes, controls = [], []
        for b in range(design.BLOCKS):
            durations = matrix.get((b, i))
            legacy.refuse(type(durations) is list and len(durations) == 6
                          and all(type(t) is int and t > 0 for t in durations),
                          "v2 matrix requires six positive integer walls")
            assignment = design.order(b, i)
            a_times = [durations[j] for j in range(4) if assignment[j] == "A"]
            b_times = [durations[j] for j in range(4) if assignment[j] == "B"]
            legacy.refuse(len(a_times) == len(b_times) == 2,
                          "v2 treatment balance missing")
            effect = math.log(sum(a_times) / sum(b_times))
            changes.append(effect)
            order_effects.setdefault((i, "".join(assignment[:4])), []).append(effect)
            controls.append(abs(math.log(durations[4] / durations[5])))
        packet_logs[i] = statistics.median(changes)
        aa_drift[i] = controls

    groups = {}
    for i, row in enumerate(rows):
        key = (row["from"], row["to"], row["sector"],
               "identity" if row["scalar_OUTSIDE_runtime"] == 0 else "generic")
        groups.setdefault(key, []).append(i)
    legacy.refuse(len(groups) == 16, "v2 frozen strata count")
    result = []
    for k, ids in sorted(groups.items()):
        effect = statistics.median(packet_logs[i] for i in ids)
        control = [v for i in ids for v in aa_drift[i]]
        order_a = [v for i in ids for v in order_effects[(i, "ABBA")]]
        order_b = [v for i in ids for v in order_effects[(i, "BAAB")]]
        legacy.refuse(len(order_a) == len(order_b) == 4 * len(ids),
                      "v2 strata order imbalance")
        ci = None
        if len(ids) > 1:
            rng = random.Random(legacy.SEED + 7919 * (k[0] + 1)
                                + 127 * k[2] + (1 if k[3] == "generic" else 0))
            trials = []
            for _ in range(2000):
                picks = [packet_logs[rng.choice(ids)] for _ in ids]
                trials.append(statistics.median(picks))
            ci = [math.exp(legacy.percentile(trials, p)) for p in (0.025, 0.975)]
        result.append({
            "direction": [k[0], k[1]], "sector": k[2], "class": k[3],
            "unique_packets": len(ids), "paired_blocks": len(ids) * design.BLOCKS,
            "balanced_abba_blocks": len(order_a),
            "balanced_baab_blocks": len(order_b),
            "direct_over_retained_transfer_wall_ratio": math.exp(effect),
            "cluster_bootstrap_ratio_ci95": ci,
            "aa_abs_log_ratio_p95": legacy.percentile(control, 0.95),
            "abba_log_ratio_median_diagnostic": statistics.median(order_a),
            "baab_log_ratio_median_diagnostic": statistics.median(order_b),
        })
    return result


def adjudicate_v2(panel, fixture):
    rows, fixture_hash = legacy.frozen_fixture(fixture)
    digest = hashlib.sha256()
    with Path(panel).open("rb") as fh:
        def next_obj():
            line = fh.readline(legacy.MAX_LINE + 1)
            legacy.refuse(line and len(line) <= legacy.MAX_LINE,
                          "missing or oversized v2 panel line")
            digest.update(line)
            return legacy.decode_json(line)

        manifest = next_obj()
        legacy.refuse(type(manifest) is dict and manifest.get("type") == "manifest"
                      and manifest.get("schema") == SCHEMA,
                      "v2 manifest schema (v1 not accepted)")
        expected = {
            "fixture_git_blob": legacy.FIXTURE_BLOB,
            "fixture_sha256": fixture_hash,
            "blocks": design.BLOCKS, "seed": legacy.SEED,
            "processes": N, "packets": 48,
            "order_schedule": ORDER_SCHEDULE,
            "order_roster_sha256": roster_sha256(),
        }
        for field, value in expected.items():
            legacy.refuse(type(manifest.get(field)) is type(value)
                          and manifest[field] == value,
                          "v2 manifest mismatch: " + field)
        legacy.refuse(legacy.hex_digest(manifest.get("executable_sha256"))
                      and type(manifest.get("host")) is dict,
                      "v2 executable/host identity missing")
        legacy.integer(manifest.get("panel_wall_seconds"), "v2 panel budget", 1)
        legacy.integer(manifest.get("timeout_seconds"), "v2 child timeout", 1)
        path = manifest.get("executable_path")
        legacy.refuse(type(path) is str and bool(path),
                      "v2 executable path missing")
        times, memory, missing_memory = {}, [], 0
        for block, index, position, arm in roster():
            sample = next_obj()
            legacy.refuse(type(sample) is dict and sample.get("type") == "sample",
                          "v2 non-sample within roster")
            for field, value in (("block", block), ("packet_index", index),
                                 ("position", position), ("arm", arm)):
                legacy.refuse(type(sample.get(field)) is type(value)
                              and sample[field] == value,
                              "v2 roster mismatch: " + field)
            legacy.refuse(sample.get("argv") == [path, "--cold-route", str(index), arm],
                          "v2 spawned command mismatch")
            elapsed, rss = legacy.valid_sample(sample, rows[index], index, arm)
            times.setdefault((block, index), []).append(elapsed)
            if rss is None:
                missing_memory += 1
            else:
                memory.append(rss)
        terminal = next_obj()
        legacy.refuse(type(terminal) is dict
                      and terminal.get("type") == "terminal"
                      and terminal.get("verified_complete") is True
                      and terminal.get("refusal") is None
                      and type(terminal.get("attempted")) is int
                      and terminal["attempted"] == N
                      and type(terminal.get("planned")) is int
                      and terminal["planned"] == N,
                      "v2 incomplete/refused terminal")
        legacy.refuse(fh.read(1) == b"", "v2 trailing panel records")

    return {
        "schema": REPORT_SCHEMA, "standing": "[pcc:unverified]",
        "input_panel_sha256": digest.hexdigest(),
        "frozen_fixture_git_blob": legacy.FIXTURE_BLOB,
        "frozen_fixture_sha256": fixture_hash,
        "roster_sha256": roster_sha256(),
        "executable_sha256_producer_reported": manifest["executable_sha256"],
        "host_identity_producer_reported": manifest["host"],
        "observed_complete_processes": N,
        "peak_rss_kib_linux_producer_reported_max": max(memory, default=None),
        "processes_missing_peak_rss": missing_memory,
        "complete_memory_evidence": missing_memory == 0,
        "strata": paired_statistics_v2(times, rows),
        "scope": "synthetic or producer-only cold transfer, not a complete ECDLP",
        "original_full_695_701_custody_replayed": False,
        "complete_single_target_ecdlp_advantage_established": False,
        "signed_independent_pcc": False,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--fixture", type=Path, required=True)
    p.add_argument("--panel", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    result = adjudicate_v2(args.panel, args.fixture)
    with args.output.open("x", encoding="utf-8") as fh:
        json.dump(result, fh, sort_keys=True, indent=2, allow_nan=False)
        fh.write("\n")
    print("CT182 offline v2 evidence accepted: transfer-only; NO complete ECDLP claim")


if __name__ == "__main__":
    main()
