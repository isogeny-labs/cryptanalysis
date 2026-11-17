#!/usr/bin/env python3
"""CT187: opt-in native all-A sham producer and strict offline reader.

The physical route is always direct_composite; A/B is a blinded sham label
which must NEVER become an executable argument. No ECDLP advantage claimed.
External provider/budget approval remains required in addition to CLI flags.
[pcc:unverified]
"""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import sys
import time

import ct176_cold_process_collector as bounded
import ct179_panel_adjudicator as legacy
import ct186_same_route_sham as sham

SCHEMA = "ct187-cold-same-route-sham-panel/v1"
REPORT_SCHEMA = "ct187-cold-same-route-sham-adjudication/v1"


def digest_file(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def manifest(fixture_hash, host):
    if sham.roster_sha256() != (
            "7cf758b05c82adf2d1e9edc675d10dc5a0bb603a004d51a42f9375a077d75228"):
        raise ValueError("CT186 roster SHA changed")
    return {
        "schema": SCHEMA, "standing": "[pcc:unverified]",
        "fixture_git_blob": bounded.FIXTURE_GIT_BLOB,
        "fixture_sha256": fixture_hash, "packets": sham.PACKETS,
        "blocks": sham.BLOCKS, "processes": sham.N, "seed": sham.SEED,
        "physical_arm": sham.PHYSICAL_ARM,
        "roster_sha256": sham.roster_sha256(),
        "host": host,
        "scope": "cold same-route placebo diagnostic; not complete ECDLP",
    }


def terminal(attempted, refusal):
    if refusal is None and attempted != sham.N:
        refusal = "incomplete sham population"
    return {
        "type": "terminal", "attempted": attempted, "planned": sham.N,
        "verified_complete": refusal is None and attempted == sham.N,
        "refusal": refusal,
        "ended_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }


def collect(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--admission-approved", action="store_true")
    parser.add_argument("--executable", type=Path)
    parser.add_argument("--executable-sha256")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--timeout-seconds", type=int, default=120)
    parser.add_argument("--panel-wall-seconds", type=int)
    args = parser.parse_args(argv)

    rows, fixture_hash = bounded.fixture_rows(args.fixture)
    plan = manifest(fixture_hash, bounded.host_metadata())
    if not args.execute:
        print(json.dumps({"plan_only": True, **plan}, sort_keys=True))
        return 0

    if not args.admission_approved:
        parser.error("external provider/owner approval required AND --admission-approved")
    if args.executable is None or args.executable_sha256 is None or args.output is None:
        parser.error("execution needs executable, executable-sha256 and output")
    if type(args.timeout_seconds) is not int or args.timeout_seconds <= 0:
        parser.error("timeout-seconds must be positive")
    try:
        budget = bounded.require_panel_budget(args.panel_wall_seconds)
    except ValueError as exc:
        parser.error(str(exc))
    binary = args.executable.resolve(strict=True)
    if not binary.is_file() or not os.access(binary, os.X_OK):
        parser.error("executable is not an executable file")
    observed_sha = digest_file(binary)
    if observed_sha != args.executable_sha256:
        parser.error("executable SHA-256 mismatch")
    plan.update({
        "executable_path": str(binary), "executable_sha256": observed_sha,
        "timeout_seconds": args.timeout_seconds, "panel_wall_seconds": budget,
    })
    started_ns = time.monotonic_ns()
    deadline_ns = started_ns + budget * 1_000_000_000
    completed, failure = 0, None
    # Exclusive creation: never overwrite a partial or verified prior panel.
    with args.output.open("x", encoding="utf-8") as fh:
        bounded.jwrite(fh, {
            "type": "manifest", **plan,
            "started_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        })
        for block, packet, position, label, arm in sham.roster():
            if bounded.host_metadata() != plan["host"]:
                failure = "host/affinity changed before sample"
                break
            allowance = bounded.panel_child_timeout_seconds(
                deadline_ns, args.timeout_seconds)
            if allowance is None:
                failure = "aggregate panel deadline before sample"
                break
            # Intentionally DOES NOT pass the placebo label to the native child.
            trial = bounded.run_sample(binary, packet, sham.PHYSICAL_ARM,
                                       rows[packet], allowance)
            bounded.jwrite(fh, {
                "type": "sample", "block": block, "packet_index": packet,
                "position": position, "label": label, "physical_arm": arm,
                **trial,
            })
            completed += 1
            if time.monotonic_ns() >= deadline_ns:
                failure = "aggregate panel deadline after sample"
                break
            if not trial["verified"]:
                failure = trial["error"] or "unverified native child"
                break
        record = terminal(completed, failure)
        bounded.jwrite(fh, record)
        failure = record["refusal"]
    if failure is not None:
        print("CT187 REFUSED: " + failure + "; preserved " + str(args.output),
              file=sys.stderr)
        return 1
    print("CT187 producer-only 1536-process sham panel; NOT full ECDLP")
    return 0


def adjudicate(panel, fixture):
    rows, fixture_hash = legacy.frozen_fixture(fixture)
    panel_digest = hashlib.sha256()
    with Path(panel).open("rb") as fh:
        def read_object():
            line = fh.readline(legacy.MAX_LINE + 1)
            legacy.refuse(bool(line) and len(line) <= legacy.MAX_LINE,
                          "missing/oversized sham panel line")
            panel_digest.update(line)
            return legacy.decode_json(line)

        head = read_object()
        legacy.refuse(type(head) is dict and head.get("type") == "manifest"
                      and head.get("schema") == SCHEMA,
                      "CT187 manifest schema")
        expected = manifest(fixture_hash, head.get("host"))
        for field, value in expected.items():
            legacy.refuse(type(head.get(field)) is type(value)
                          and head[field] == value, "manifest mismatch: " + field)
        legacy.refuse(type(head.get("host")) is dict
                      and legacy.hex_digest(head.get("executable_sha256"))
                      and type(head.get("executable_path")) is str
                      and bool(head["executable_path"]),
                      "executable/host identity absent")
        legacy.integer(head.get("panel_wall_seconds"), "panel budget", 1)
        legacy.integer(head.get("timeout_seconds"), "child timeout", 1)
        exact_path = head["executable_path"]
        records, memory, missing_memory = [], [], 0
        for block, packet, position, label, arm in sham.roster():
            sample = read_object()
            legacy.refuse(type(sample) is dict and sample.get("type") == "sample",
                          "non-sample or absent sham record")
            for name, value in (
                ("block", block), ("packet_index", packet),
                ("position", position), ("label", label),
                ("physical_arm", arm),
            ):
                legacy.refuse(type(sample.get(name)) is type(value)
                              and sample[name] == value,
                              "sham roster mismatch: " + name)
            legacy.refuse(
                sample.get("argv") == [
                    exact_path, "--cold-route", str(packet), sham.PHYSICAL_ARM,
                ], "sham physical command/argv mismatch")
            elapsed, rss = legacy.valid_sample(sample, rows[packet],
                                               packet, sham.PHYSICAL_ARM)
            records.append({
                "block": block, "packet_index": packet,
                "position": position, "label": label,
                "physical_arm": sham.PHYSICAL_ARM, "wall_ns": elapsed,
            })
            if rss is None:
                missing_memory += 1
            else:
                memory.append(rss)
        finish = read_object()
        legacy.refuse(type(finish) is dict and finish.get("type") == "terminal"
                      and finish.get("verified_complete") is True
                      and finish.get("refusal") is None
                      and type(finish.get("attempted")) is int
                      and finish["attempted"] == sham.N
                      and type(finish.get("planned")) is int
                      and finish["planned"] == sham.N,
                      "CT187 incomplete/censored terminal")
        legacy.refuse(fh.read(1) == b"", "extra sham records")
    report = sham.adjudicate(records)
    return {
        "schema": REPORT_SCHEMA, "standing": "[pcc:unverified]",
        "fixture_git_blob": bounded.FIXTURE_GIT_BLOB,
        "fixture_sha256": fixture_hash,
        "panel_sha256": panel_digest.hexdigest(),
        "executable_sha256_producer_reported": head["executable_sha256"],
        "host_producer_reported": head["host"],
        "observed_complete_processes": sham.N,
        "processes_missing_peak_rss": missing_memory,
        "complete_memory_evidence": missing_memory == 0,
        "peak_rss_kib_producer_reported_max": max(memory, default=None),
        "sham_diagnostic": report,
        "scope": "producer-only sham placebo; not native independent PCC or ECDLP",
        "complete_single_target_ecdlp_advantage_established": False,
        "original_full_695_701_custody_replayed": False,
        "signed_independent_pcc": False,
    }


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=("plan", "collect", "adjudicate"))
    p.add_argument("--fixture", type=Path, required=True)
    p.add_argument("--panel", type=Path)
    p.add_argument("--report", type=Path)
    args, other = p.parse_known_args(argv)
    if args.mode != "adjudicate":
        if args.panel or args.report:
            p.error("--panel and --report only for adjudicate")
        return collect(["--fixture", str(args.fixture)] +
                       (["--execute"] if args.mode == "collect" else []) + other)
    if other or args.panel is None or args.report is None:
        p.error("adjudicate requires --panel and --report, no execution flags")
    result = adjudicate(args.panel, args.fixture)
    with args.report.open("x", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2, sort_keys=True, allow_nan=False)
        fh.write("\n")
    print("CT187 offline sham diagnostic only; NO ECDLP advantage")
    return 0


if __name__ == "__main__":
    sys.exit(main())
