#!/usr/bin/env python3
"""Resolve a delayed ambiguous HTTP-batch create without allocating anything.

The controller receipt retains only a randomized pod name and SHA-256 of its
ephemeral bearer.  This tool lists by that exact name and ownership marker.  It
deletes at most one exact owned pod ID and verifies the v2 ID becomes 404.  It
has no create/start/retry path and never needs the bearer itself.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import runpod_http_batch as batch  # noqa: E402


SCHEMA = "runpod.http-batch.ambiguous-create-reconciliation/v1"
SAFE_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9-]{0,99}\Z")


def load_binding(path: Path) -> tuple[dict, str, str]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or value.get("schema") != batch.SCHEMA:
        raise batch.BatchError("controller receipt schema is invalid")
    request = value.get("request") if isinstance(value.get("request"), dict) else {}
    reconciliation = (
        value.get("reconciliation")
        if isinstance(value.get("reconciliation"), dict) else {}
    )
    name = request.get("name")
    ownership_id = reconciliation.get("ownership_id")
    if (
        not isinstance(name, str) or SAFE_NAME.fullmatch(name) is None
        or reconciliation.get("name") != name
        or not isinstance(ownership_id, str)
        or batch.SHA256.fullmatch(ownership_id) is None
    ):
        raise batch.BatchError("controller receipt lacks an exact ownership binding")
    if value.get("pod") is not None or value.get("cleanup") is not None:
        raise batch.BatchError("controller already recorded a pod or cleanup result")
    if value.get("error") is None or value.get("provider_actions") is not True:
        raise batch.BatchError("controller receipt is not an ambiguous real-provider failure")
    last_match_count = reconciliation.get("last_match_count")
    if (
        reconciliation.get("attempted") is not True
        or type(reconciliation.get("attempts")) is not int
        or reconciliation["attempts"] < 1
        or not (
            last_match_count is None
            or type(last_match_count) is int and last_match_count == 0
        )
        or reconciliation.get("owned_pod_id") is not None
    ):
        raise batch.BatchError("controller did not record an unresolved create reconciliation")
    capacity = value.get("capacity_gate")
    if isinstance(capacity, dict) and capacity.get("create_attempted") is not True:
        raise batch.BatchError("controller capacity gate did not spend the create attempt")
    return value, name, ownership_id


def execute(args, *, client=None, sleep=None) -> int:
    if args.out.exists():
        raise FileExistsError("reconciliation receipt already exists")
    controller, name, ownership_id = load_binding(args.controller_receipt)
    client = client or batch.RunpodClient()
    sleeper = sleep or __import__("time").sleep
    record = {
        "schema": SCHEMA,
        "provider_actions": True,
        "started_at": batch.utc_now(),
        "controller_receipt": {
            "path": str(args.controller_receipt),
            "sha256": batch.sha256_file(args.controller_receipt),
        },
        "binding": {"name": name, "ownership_id": ownership_id},
        "matched_pod_id": None,
        "cleanup": None,
        "absence_verified_by_name_and_marker": False,
        "error": None,
        "finished_at": None,
    }
    pending = None
    try:
        matches = [
            pod for pod in client.named(name)
            if batch.marker_matches(pod, name, ownership_id)
        ]
        if len(matches) > 1:
            raise batch.BatchError("multiple exact-name ownership-bound pods; refusing deletion")
        if not matches:
            record["absence_verified_by_name_and_marker"] = True
        else:
            pod_id = batch.pod_identifier(matches[0])
            record["matched_pod_id"] = pod_id
            record["cleanup"] = batch.cleanup_exact(client, pod_id, sleep=sleeper)
    except BaseException as error:
        pending = error
        record["error"] = batch.error_record(error)
    finally:
        record["finished_at"] = batch.utc_now()
        batch.write_once(args.out, record)
    if pending is not None:
        raise batch.BatchError(batch.safe_error(pending)) from pending
    return 0


def parse(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--controller-receipt", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv=None) -> int:
    try:
        return execute(parse(argv))
    except KeyboardInterrupt:
        print("runpod_http_reconcile: interrupted", file=sys.stderr)
        return 130
    except Exception as error:
        print(f"runpod_http_reconcile: {batch.safe_error(error)}", file=sys.stderr)
        return 125


if __name__ == "__main__":
    raise SystemExit(main())
