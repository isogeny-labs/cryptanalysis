#!/usr/bin/env python3
"""Recover one authenticated HTTP-batch result after its controller vanished.

This is a recovery path, not a second allocation path.  It requires the exact
pod identity and every frozen source/command/output binding, obtains the
ephemeral bearer only from that pod's provider metadata, verifies the same
provider and result contracts as :mod:`runpod_http_batch`, installs only
hash-bound declared outputs, and deletes only the bound pod ID in ``finally``.

The design follows ``cloud/README.md`` and Runpod's official Pod REST and
HTTPS-proxy documentation linked there.  In particular, provider metadata is
used only to resume the existing authenticated GET channel; no create, start,
or retry-allocation operation exists here.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time


HERE = Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(HERE))
import runpod_http_batch as batch  # noqa: E402
import runpod_pod  # noqa: E402


SCHEMA = "runpod.http-batch.recovery-receipt/v1"
TOOL_PATH = "cloud/runpod_http_recover.py"
SAFE_REASON = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,159}\Z")
SAFE_POD_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9-]{0,99}\Z")


def _text_b64(value: object, label: str) -> str:
    if not isinstance(value, str):
        raise batch.BatchError(f"provider environment has invalid {label}")
    try:
        raw = base64.b64decode(value, validate=True)
        return raw.decode("utf-8")
    except (ValueError, UnicodeDecodeError) as error:
        raise batch.BatchError(
            f"provider environment has invalid {label}") from error


def _positive_decimal(value: object, label: str) -> int:
    if not isinstance(value, str) or not re.fullmatch(r"[1-9][0-9]*", value):
        raise batch.BatchError(f"provider environment has invalid {label}")
    return int(value)


def environment_contract(pod: dict, args) -> tuple[str, dict]:
    """Return the in-memory bearer and a safe exact binding for one pod."""
    if batch.pod_identifier(pod) != args.pod_id or pod.get("name") != args.pod_name:
        raise batch.BatchError("listed pod identity does not match recovery target")
    environment = pod.get("env")
    if not isinstance(environment, dict):
        raise batch.BatchError("provider did not return the pod environment")

    token = environment.get("RUNPOD_BATCH_TOKEN")
    if not isinstance(token, str) or len(token) < 43:
        raise batch.BatchError("provider environment lacks a valid recovery bearer")
    ownership_id = hashlib.sha256(token.encode()).hexdigest()
    if environment.get("RUNPOD_BATCH_OWNERSHIP_ID") != ownership_id:
        raise batch.BatchError("pod ownership marker does not bind its recovery bearer")

    expected = {
        "RUNPOD_BATCH_JOB_ID": args.pod_name,
        "RUNPOD_BATCH_SOURCE_URL": batch.PUBLIC_ORIGIN,
        "RUNPOD_BATCH_SOURCE_REF": args.source_ref,
        "RUNPOD_BATCH_SOURCE_COMMIT": args.source_commit,
        "RUNPOD_BATCH_SOURCE_TREE": args.source_tree,
        "RUNPOD_BATCH_SOURCE_ARCHIVE_SHA256": args.source_archive_sha256,
        "RUNPOD_BATCH_COMMAND_SHA256": args.command_sha256,
        "RUNPOD_BATCH_TIMEOUT_SECONDS": str(args.command_timeout),
        "RUNPOD_BATCH_CHUNK_BYTES": str(batch.CHUNK_BYTES),
        "RUNPOD_BATCH_MAX_RESULT_BYTES": str(args.max_result_mib << 20),
        "RUNPOD_BATCH_PORT": str(batch.HTTP_PORT),
        "POD_MAX_SECONDS": str(int(args.max_hours * 3600)),
    }
    if any(environment.get(key) != value for key, value in expected.items()):
        raise batch.BatchError("provider environment does not match frozen recovery binding")

    command = _text_b64(environment.get("RUNPOD_BATCH_COMMAND_B64"), "command")
    if (not command.strip()
            or hashlib.sha256(command.encode()).hexdigest() != args.command_sha256):
        raise batch.BatchError("recovered command does not match its frozen SHA-256")
    outputs_text = _text_b64(
        environment.get("RUNPOD_BATCH_OUTPUTS_B64"), "output declaration")
    try:
        remote_outputs = json.loads(outputs_text)
    except json.JSONDecodeError as error:
        raise batch.BatchError("provider output declaration is not JSON") from error
    if not isinstance(remote_outputs, list) or any(
            not isinstance(item, str) for item in remote_outputs):
        raise batch.BatchError("provider output declaration is invalid")
    outputs = batch.validate_outputs(remote_outputs)
    if outputs != args.outputs:
        raise batch.BatchError("provider outputs do not match frozen recovery binding")

    timeout = _positive_decimal(
        environment.get("RUNPOD_BATCH_TIMEOUT_SECONDS"), "command timeout")
    maximum = _positive_decimal(
        environment.get("RUNPOD_BATCH_MAX_RESULT_BYTES"), "result limit")
    lifetime = _positive_decimal(environment.get("POD_MAX_SECONDS"), "lifetime")
    safe = {
        "ownership_id": ownership_id,
        "job_id": args.pod_name,
        "source": {
            "origin": batch.PUBLIC_ORIGIN,
            "ref": args.source_ref,
            "commit": args.source_commit,
            "tree": args.source_tree,
            "archive_sha256": args.source_archive_sha256,
        },
        "command": command,
        "command_sha256": args.command_sha256,
        "outputs": outputs,
        "command_timeout_seconds": timeout,
        "chunk_bytes": batch.CHUNK_BYTES,
        "max_result_bytes": maximum,
        "pod_max_seconds": lifetime,
        "port": batch.HTTP_PORT,
        "authentication": "provider-recovered ephemeral bearer; value redacted",
    }
    if token in json.dumps(safe, sort_keys=True):
        raise AssertionError("recovery bearer reached safe environment binding")
    return token, safe


def tool_binding(repo: Path, commit: str) -> dict:
    """Bind this exact file to an explicit committed Git object."""
    if not batch.COMMIT.fullmatch(commit):
        raise batch.BatchError("--tool-commit must be an exact commit ID")
    result = subprocess.run(
        ["git", "show", f"{commit}:{TOOL_PATH}"], cwd=repo,
        capture_output=True, check=False)
    if result.returncode:
        raise batch.BatchError("recovery tool is absent from --tool-commit")
    committed_sha = hashlib.sha256(result.stdout).hexdigest()
    current_sha = batch.sha256_file(Path(__file__).resolve())
    if committed_sha != current_sha:
        raise batch.BatchError("working recovery tool differs from --tool-commit")
    return {"path": TOOL_PATH, "commit": commit, "sha256": current_sha}


def _terminal_expected(args) -> dict:
    expected = {
        "job_id": args.pod_name,
        "commit": args.source_commit,
        "tree": args.source_tree,
        "archive_sha256": args.source_archive_sha256,
        "command_sha256": args.command_sha256,
        "pod_id": args.pod_id,
        "max_result_bytes": args.max_result_mib << 20,
    }
    if args.cpu:
        expected.update(compute_type="CPU", gpu_count=0)
    else:
        if len(args.gpu) != 1:
            raise batch.BatchError("GPU recovery requires exactly one --gpu identity")
        expected.update(
            compute_type="GPU", gpu_id=args.gpu[0], gpu_count=args.gpu_count)
    return expected


def _paths_absent(receipt: Path, archive: Path, metadata: Path) -> None:
    if receipt.exists() or archive.exists() or metadata.exists():
        raise FileExistsError(
            "recovery receipt, archive, or remote metadata already exists")


def execute(args, *, client=None, transport=None, repo=REPO,
            sleep=time.sleep, tool_binding_fn=tool_binding) -> int:
    batch.validate_compute_request(args)
    args.outputs = batch.validate_outputs(args.out)
    expected = _terminal_expected(args)
    receipt_path = args.receipt.resolve()
    archive_path = args.archive.resolve()
    metadata_dir = receipt_path.with_suffix(".remote")
    _paths_absent(receipt_path, archive_path, metadata_dir)
    tool = tool_binding_fn(Path(repo), args.tool_commit)

    client = client or batch.RunpodClient()
    transport = transport or batch.HttpTransport()
    receipt = {
        "schema": SCHEMA,
        "provider_actions": True,
        "started_at": batch.utc_now(),
        "recovery": {
            "reason": args.reason,
            "original_controller_receipt_available": False,
            "new_allocation_attempted": False,
            "tool": tool,
        },
        "binding": None,
        "pod": None,
        "remote_status": None,
        "result": None,
        "cleanup": None,
        "error": None,
    }
    token = ""
    owned_pod_id = None
    pending: BaseException | None = None
    returncode = 125
    try:
        matches = [pod for pod in client.list_pods()
                   if pod.get("id") == args.pod_id]
        if len(matches) != 1:
            raise batch.BatchError("exact recovery pod is absent or duplicated")
        token, binding = environment_contract(matches[0], args)
        receipt["binding"] = binding
        owned_pod_id = args.pod_id

        provider = client.get_v2(args.pod_id)
        receipt["pod"] = batch.guard_provider(
            provider, args.pod_id, args.pod_name, args)
        deadline = time.monotonic() + args.wait
        status = transport.wait_status(
            batch.proxy_base(args.pod_id), token, expected, deadline,
            sleep=sleep,
            provider_monitor=lambda: batch.monitor_provider(
                client, args.pod_id, args.pod_name, args))
        receipt["remote_status"] = status
        transport.download(
            batch.proxy_base(args.pod_id), token, status, archive_path)
        verified = batch.extract_verified(
            archive_path, args.outputs, Path(repo), metadata_dir,
            args.max_result_mib << 20)
        receipt["result"] = {
            "archive": str(archive_path),
            "archive_sha256": batch.sha256_file(archive_path),
            "archive_bytes": archive_path.stat().st_size,
            "metadata": str(metadata_dir),
            "files": verified,
        }
        returncode = status["returncode"]
    except BaseException as error:
        pending = error
        receipt["error"] = {
            "type": type(error).__name__,
            "detail": batch.safe_error(error, (token,)),
        }
    finally:
        if owned_pod_id is not None:
            try:
                receipt["cleanup"] = batch.cleanup_exact(
                    client, owned_pod_id, sleep=sleep)
            except BaseException as error:
                receipt["cleanup"] = {
                    "id": owned_pod_id,
                    "delete_requested": False,
                    "absence_verified": False,
                    "error_type": type(error).__name__,
                    "error": batch.safe_error(error, (token,)),
                }
                if pending is None:
                    pending = error
        receipt["finished_at"] = batch.utc_now()
        serialized = json.dumps(receipt, sort_keys=True, allow_nan=False)
        if token and token in serialized:
            raise AssertionError("recovery bearer reached receipt")
        batch.write_once(receipt_path, receipt)
    if pending is not None:
        if isinstance(pending, (KeyboardInterrupt, SystemExit)):
            raise pending
        raise batch.BatchError(batch.safe_error(pending, (token,))) from pending
    return returncode


def parse(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pod_id", help="exact existing Runpod pod ID")
    parser.add_argument("pod_name", help="exact randomized batch pod name")
    runpod_pod.add_pod_options(parser)
    parser.add_argument(
        "--cpu-memory", type=int, default=0, metavar="PROVIDER_VALUE",
        help="exact raw v2 cpu.memory response required for a CPU pod")
    parser.add_argument("--max-price", type=float, required=True)
    parser.add_argument("--source-ref", required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--source-tree", required=True)
    parser.add_argument("--source-archive-sha256", required=True)
    parser.add_argument("--command-sha256", required=True)
    parser.add_argument("--command-timeout", type=int, required=True)
    parser.add_argument("--max-result-mib", type=int, required=True)
    parser.add_argument("--out", action="append", default=[], metavar="PATH")
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--tool-commit", required=True)
    parser.add_argument("--reason", required=True)
    args = parser.parse_args(argv)
    if (not batch.POD_ID.fullmatch(args.pod_id)
            or not SAFE_POD_NAME.fullmatch(args.pod_name)):
        parser.error("pod ID or exact name is invalid")
    if (not batch.SOURCE_REF.fullmatch(args.source_ref)
            or not batch.COMMIT.fullmatch(args.source_commit)
            or not batch.COMMIT.fullmatch(args.source_tree)
            or not batch.SHA256.fullmatch(args.source_archive_sha256)
            or not batch.SHA256.fullmatch(args.command_sha256)):
        parser.error("source or command binding is invalid")
    if (not SAFE_REASON.fullmatch(args.reason)
            or args.command_timeout < 1 or args.max_result_mib < 1
            or args.max_price <= 0 or args.wait < 1 or args.max_hours <= 0):
        parser.error("reason, timeout, result, price, wait, or lifetime is invalid")
    return args


def main(argv=None) -> int:
    try:
        return execute(parse(argv))
    except KeyboardInterrupt:
        print(
            "runpod_http_recover: interrupted after exact-ID cleanup attempt",
            file=sys.stderr)
        return 130
    except Exception as error:
        print(f"runpod_http_recover: {batch.safe_error(error)}", file=sys.stderr)
        return 125


if __name__ == "__main__":
    raise SystemExit(main())
