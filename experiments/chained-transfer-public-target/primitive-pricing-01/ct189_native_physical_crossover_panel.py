#!/usr/bin/env python3
"""CT189: admitted-source physical A/B cold crossover producer + strict offline reader.

Source and mocked tests do not authorize hardware, prove native parity, provide
signed PCC, or demonstrate a complete ECDLP improvement. [pcc:unverified]
"""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import sys
import time

import ct176_cold_process_collector as native
import ct179_panel_adjudicator as audit
import ct188_physical_crossover_design as design

SCHEMA = "ct189-physical-cold-public-process-panel/v3"
REPORT_SCHEMA = "ct189-physical-cold-public-adjudication/v3"
ROSTER_DIGEST = "1bc8c26a01e7952e57d944fd535c9832607f2ab7bcc910342ad704171ab67af1"


def digest_file(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for part in iter(lambda: fh.read(1 << 20), b""):
            h.update(part)
    return h.hexdigest()


def checked_design():
    if not design.assert_design() or design.roster_sha256() != ROSTER_DIGEST:
        raise ValueError("CT188 exact physical roster changed; refuse")
    if design.FIXTURE_GIT_BLOB != native.FIXTURE_GIT_BLOB or design.N != 2304:
        raise ValueError("fixture or expected process population changed")
    return True


def manifest(fixture_sha, host):
    checked_design()
    return {
        "schema": SCHEMA,
        "standing": "[pcc:unverified]",
        "fixture_git_blob": native.FIXTURE_GIT_BLOB,
        "fixture_sha256": fixture_sha,
        "seed": design.SEED,
        "packets": design.PACKETS,
        "blocks": design.BLOCKS,
        "slots": design.SLOTS,
        "processes": design.N,
        "roster_sha256": ROSTER_DIGEST,
        "physical_arms": design.ARMS,
        "sequence_multiset_per_packet": list(design.SEQUENCES),
        "host": host,
        "scope": "actual physical cold transfer routes ONLY; not a complete prime-field ECDLP",
    }


def terminal(attempted, failure):
    if failure is None and attempted != design.N:
        failure = "incomplete physical crossover population"
    return {
        "type": "terminal", "attempted": attempted, "planned": design.N,
        "verified_complete": failure is None and attempted == design.N,
        "refusal": failure,
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

    rows, fixture_sha = native.fixture_rows(args.fixture)
    plan = manifest(fixture_sha, native.host_metadata())
    if not args.execute:
        print(json.dumps({"plan_only": True, **plan}, sort_keys=True))
        return 0

    if not args.admission_approved:
        parser.error("external owner/provider authorization required AND --admission-approved")
    if args.executable is None or args.executable_sha256 is None or args.output is None:
        parser.error("execution requires executable, executable SHA-256 and exclusive output")
    if type(args.timeout_seconds) is not int or args.timeout_seconds <= 0:
        parser.error("timeout-seconds must be positive")
    try:
        budget = native.require_panel_budget(args.panel_wall_seconds)
    except ValueError as exc:
        parser.error(str(exc))
    try:
        binary = args.executable.resolve(strict=True)
    except OSError as exc:
        parser.error("executable unavailable: " + str(exc))
    if not binary.is_file() or not os.access(binary, os.X_OK):
        parser.error("binary is not executable")
    observed_sha = digest_file(binary)
    if args.executable_sha256 != observed_sha:
        parser.error("executable SHA-256 mismatch")
    plan.update({
        "executable_path": str(binary), "executable_sha256": observed_sha,
        "timeout_seconds": args.timeout_seconds, "panel_wall_seconds": budget,
    })

    began_ns = time.monotonic_ns()
    deadline_ns = began_ns + budget * 1_000_000_000
    with args.output.open("x", encoding="utf-8") as fh:
        native.jwrite(fh, {
            "type": "manifest", **plan,
            "started_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        })
        attempted, failure = 0, None
        for block, packet, position, physical_arm in design.roster():
            if native.host_metadata() != plan["host"]:
                failure = "host/affinity changed before sample"
                break
            allowance = native.panel_child_timeout_seconds(deadline_ns, args.timeout_seconds)
            if allowance is None:
                failure = "aggregate wall deadline exhausted before sample"
                break
            # Actual physical route is passed, not a placebo treatment label.
            sample = native.run_sample(binary, packet, physical_arm, rows[packet], allowance)
            native.jwrite(fh, {
                "type": "sample", "block": block, "packet_index": packet,
                "position": position, "arm": physical_arm, **sample,
            })
            attempted += 1
            if time.monotonic_ns() >= deadline_ns:
                failure = "aggregate wall deadline exhausted after sample"
                break
            if sample.get("verified") is not True:
                failure = sample.get("error") or "native child not verified"
                break
        end = terminal(attempted, failure)
        native.jwrite(fh, end)
        failure = end["refusal"]
    if failure is not None:
        print("CT189 REFUSED: " + failure + "; incomplete evidence retained at " +
              str(args.output), file=sys.stderr)
        return 1
    print("CT189 producer-only cold crossover complete; not a complete ECDLP solve")
    return 0


def adjudicate(panel, fixture):
    rows, fixture_sha = audit.frozen_fixture(fixture)
    digest = hashlib.sha256()
    with Path(panel).open("rb") as fh:
        def next_object():
            raw = fh.readline(audit.MAX_LINE + 1)
            audit.refuse(bool(raw) and len(raw) <= audit.MAX_LINE,
                         "missing/oversized CT189 JSONL record")
            digest.update(raw)
            return audit.decode_json(raw)

        head = next_object()
        audit.refuse(type(head) is dict and head.get("type") == "manifest" and
                     head.get("schema") == SCHEMA, "CT189 v3 manifest schema")
        expected = manifest(fixture_sha, head.get("host"))
        for key, value in expected.items():
            audit.refuse(type(head.get(key)) is type(value) and head[key] == value,
                         "CT189 manifest mismatch: " + key)
        audit.refuse(type(head.get("host")) is dict and
                     isinstance(head["host"].get("hostname"), str) and
                     type(head["host"].get("cpu_affinity")) in (list, type(None)),
                     "host/affinity identity absent")
        audit.refuse(audit.hex_digest(head.get("executable_sha256")),
                     "executable digest absent")
        audit.refuse(type(head.get("executable_path")) is str and
                     bool(head["executable_path"]), "executable path absent")
        audit.integer(head.get("timeout_seconds"), "per-child timeout", 1)
        audit.integer(head.get("panel_wall_seconds"), "aggregate wall budget", 1)

        evidence = []
        rss_values = []
        rss_missing = 0
        for block, packet, position, physical_arm in design.roster():
            sample = next_object()
            audit.refuse(type(sample) is dict and sample.get("type") == "sample",
                         "missing sample/early terminal")
            for key, want in (("block", block), ("packet_index", packet),
                              ("position", position), ("arm", physical_arm)):
                audit.refuse(type(sample.get(key)) is type(want) and sample[key] == want,
                             "physical roster or arm mismatch: " + key)
            audit.refuse(
                sample.get("argv") == [
                    head["executable_path"], "--cold-route", str(packet), physical_arm,
                ], "actual physical executable argv mismatch")
            elapsed, rss = audit.valid_sample(sample, rows[packet], packet, physical_arm)
            evidence.append({
                "block": block, "packet_index": packet, "position": position,
                "arm": physical_arm, "wall_ns": elapsed,
            })
            if rss is None:
                rss_missing += 1
            else:
                rss_values.append(rss)
        end = next_object()
        audit.refuse(type(end) is dict and end.get("type") == "terminal" and
                     end.get("verified_complete") is True and
                     end.get("refusal") is None and
                     type(end.get("attempted")) is int and end["attempted"] == design.N and
                     type(end.get("planned")) is int and end["planned"] == design.N,
                     "incomplete/refused CT189 terminal")
        audit.refuse(fh.read(1) == b"", "trailing CT189 panel records")

    diagnostic = design.adjudicate_untrusted_times(evidence)
    return {
        "schema": REPORT_SCHEMA, "standing": "[pcc:unverified]",
        "input_panel_sha256": digest.hexdigest(),
        "fixture_git_blob": native.FIXTURE_GIT_BLOB,
        "fixture_sha256": fixture_sha,
        "roster_sha256": ROSTER_DIGEST,
        "executable_sha256_producer_reported": head["executable_sha256"],
        "host_producer_reported": head["host"],
        "observed_complete_processes": design.N,
        "processes_missing_peak_rss": rss_missing,
        "complete_memory_evidence": rss_missing == 0,
        "peak_rss_kib_producer_reported_max": max(rss_values, default=None),
        "conditional_source_model_diagnostic": diagnostic,
        "scope": "unverified producer-origin cold physical transfer only; not complete ECDLP",
        "original_full_695_701_custody_replayed": False,
        "signed_independent_pcc": False,
        "complete_single_target_ecdlp_advantage_established": False,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("plan", "collect", "adjudicate"))
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--panel", type=Path)
    parser.add_argument("--report", type=Path)
    args, remaining = parser.parse_known_args(argv)
    if args.mode in ("plan", "collect"):
        if args.panel is not None or args.report is not None:
            parser.error("panel/report arguments only for adjudicate")
        if args.mode == "plan" and remaining:
            parser.error("plan cannot accept execution or admission flags")
        if args.mode == "collect" and "--execute" in remaining:
            parser.error("collect already supplies execute flag")
        return collect(["--fixture", str(args.fixture)] +
                       (["--execute"] if args.mode == "collect" else []) + remaining)
    if remaining or args.panel is None or args.report is None:
        parser.error("adjudicate requires --panel and --report, no execution flags")
    result = adjudicate(args.panel, args.fixture)
    with args.report.open("x", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2, sort_keys=True, allow_nan=False)
        fh.write("\n")
    print("CT189 offline physical transfer diagnostic only; not an ECDLP speedup")
    return 0


if __name__ == "__main__":
    sys.exit(main())
