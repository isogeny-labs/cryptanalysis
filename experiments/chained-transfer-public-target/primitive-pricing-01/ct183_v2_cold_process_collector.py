#!/usr/bin/env python3
"""CT183 counterbalanced v2 cold public-transfer producer; NOT a DLP solve.

Default plan-only. Native execution requires explicit owner/provider approval
in addition to both --execute and --admission-approved; this program cannot
grant admission. See CT183_BALANCED_V2_PRODUCER_PROTOCOL.md.
"""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import random
import sys
import time

import ct176_cold_process_collector as bounded

SCHEMA = "ct182-counterbalanced-cold-public-process-panel/v2"
ORDER_SCHEDULE = "ct181-block-packet-parity-ABBA-BAAB/v2"
A = "direct_composite"
B = "strongest_retained_lift_chain"
SEED = bounded.SEED
BLOCKS = bounded.BLOCKS
PACKETS = 48
N = 2304
EXPECTED_ROSTER_SHA256 = "1dddb4839321ad6560fd429330778aa083ff3a13625393250e964c05f9fc5ee4"


def treatment_order(block, packet):
    """Parity counterbalances slot assignment without changing packet order."""
    if type(block) is not int or not 0 <= block < BLOCKS:
        raise ValueError("invalid block")
    if type(packet) is not int or not 0 <= packet < PACKETS:
        raise ValueError("invalid packet")
    return (B, A, A, B, A, A) if (block + packet) % 2 else (A, B, B, A, A, A)


def roster():
    for block in range(BLOCKS):
        packet_ids = list(range(PACKETS))
        random.Random(SEED + block).shuffle(packet_ids)
        for index in packet_ids:
            for position, arm in enumerate(treatment_order(block, index)):
                yield block, index, position, arm


def roster_sha256():
    # Exact CT182 reader serialization: JSON arrays for Python tuples.
    wire = json.dumps(list(roster()), separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(wire.encode("ascii")).hexdigest()


def validated_roster_digest():
    digest = roster_sha256()
    if digest != EXPECTED_ROSTER_SHA256:
        raise ValueError("CT182 v2 wire-roster digest mismatch")
    return digest


def manifest(fixture_hash, host):
    return {
        "schema": SCHEMA, "standing": "[pcc:unverified]",
        "fixture_git_blob": bounded.FIXTURE_GIT_BLOB,
        "fixture_sha256": fixture_hash,
        "blocks": BLOCKS, "seed": SEED, "packets": PACKETS,
        "processes": N, "order_schedule": ORDER_SCHEDULE,
        "order_roster_sha256": validated_roster_digest(),
        "host": host,
        "scope": "fresh-process cold transfer ONLY, not a complete prime-field ECDLP",
    }


def run(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", required=True, type=Path)
    parser.add_argument("--executable", type=Path)
    parser.add_argument("--executable-sha256", type=str)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--timeout-seconds", type=int, default=120)
    parser.add_argument("--panel-wall-seconds", type=int)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--admission-approved", action="store_true")
    args = parser.parse_args(argv)

    rows, fixture_sha = bounded.fixture_rows(args.fixture)
    plan = manifest(fixture_sha, bounded.host_metadata())
    if not args.execute:
        print(json.dumps({"plan_only": True, **plan}, sort_keys=True))
        return 0

    if not args.admission_approved:
        parser.error("native execution requires external owner/provider approval AND --admission-approved")
    if args.executable is None or args.executable_sha256 is None or args.output is None:
        parser.error("execution requires executable, executable-sha256 and output")
    if args.timeout_seconds <= 0:
        parser.error("timeout-seconds must be positive")
    try:
        panel_wall_seconds = bounded.require_panel_budget(args.panel_wall_seconds)
    except ValueError as exc:
        parser.error(str(exc))

    binary = args.executable.resolve(strict=True)
    if not binary.is_file() or not os.access(binary, os.X_OK):
        parser.error("binary is not executable")
    observed_sha = hashlib.sha256(binary.read_bytes()).hexdigest()
    if observed_sha != args.executable_sha256:
        parser.error("executable SHA-256 mismatch")

    plan.update({
        "executable_path": str(binary),
        "executable_sha256": observed_sha,
        "timeout_seconds": args.timeout_seconds,
        "panel_wall_seconds": panel_wall_seconds,
    })
    # The deadline covers output setup, fsync, every child and final record.
    started_ns = time.monotonic_ns()
    deadline_ns = started_ns + panel_wall_seconds * 1_000_000_000
    with args.output.open("x", encoding="utf-8") as fh:
        bounded.jwrite(fh, {
            "type": "manifest", **plan,
            "started_utc": datetime.datetime.now(
                datetime.timezone.utc).isoformat(),
        })
        completed = 0
        failure = None
        for block, index, position, arm in roster():
            if bounded.host_metadata() != plan["host"]:
                failure = f"host/affinity changed before block {block} packet {index}"
                break
            allowance = bounded.panel_child_timeout_seconds(
                deadline_ns, args.timeout_seconds)
            if allowance is None:
                failure = "aggregate panel wall deadline exhausted before next sample"
                break
            trial = bounded.run_sample(binary, index, arm, rows[index], allowance)
            bounded.jwrite(fh, {
                "type": "sample", "block": block,
                "packet_index": index, "position": position, "arm": arm,
                **trial,
            })
            completed += 1
            if time.monotonic_ns() >= deadline_ns:
                failure = "aggregate panel wall deadline exhausted after sample"
                break
            if not trial["verified"]:
                failure = trial["error"] or "unverified child"
                break
        terminal = bounded.terminal_status(completed, failure)
        bounded.jwrite(fh, terminal)
        failure = terminal["refusal"]

    if failure is not None:
        print(f"CT183 REFUSED: {failure}; incomplete raw evidence: {args.output}",
              file=sys.stderr)
        return 1
    print(f"CT183 producer-only v2 transfer panel complete: {completed} processes; {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(run())
