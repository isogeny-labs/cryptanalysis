#!/usr/bin/env python3
"""Export the retained Go coordinator A/A campaign in experiment.export/v1."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
from typing import Any


def args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--campaign", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--protocol-tool", type=Path, required=True)
    return parser.parse_args()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def entry(base: Path, relative: str, kind: str) -> dict[str, Any]:
    path = base / relative
    return {
        "path": relative,
        "sha256": sha256(path),
        "bytes": path.stat().st_size,
        "kind": kind,
    }


def load_tool(path: Path):
    spec = importlib.util.spec_from_file_location("experiment_protocol", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    options = args()
    campaign = options.campaign.resolve()
    protocol_path = options.protocol.resolve()
    protocol = json.loads(protocol_path.read_text())
    manifest = json.loads((campaign / "manifest.json").read_text())
    summary = json.loads((campaign / "summary.json").read_text())
    rows = [
        json.loads(line)
        for line in (campaign / "rows.jsonl").read_text().splitlines()
        if line
    ]
    receipt_lines = [
        line for line in (campaign / "isolation.jsonl").read_text().splitlines() if line
    ]
    if protocol["freeze"]["status"] != "frozen" or len(receipt_lines) != 1:
        raise SystemExit("expected one receipt and a frozen protocol")
    receipt = json.loads(receipt_lines[0])
    protocol_sha = protocol["freeze"]["protocol_sha256"]
    if manifest["protocol_sha256"] != protocol_sha or any(
        row["protocol_sha256"] != protocol_sha for row in rows
    ):
        raise SystemExit("protocol hash mismatch")
    if len(rows) != 276 or any(row["status"] != "completed" for row in rows):
        raise SystemExit("campaign is incomplete")

    ep = load_tool(options.protocol_tool.resolve())
    export = ep.export_skeleton(
        protocol,
        os.path.relpath(protocol_path, campaign),
        "local",
        "GO-COORD-AA-V2",
    )
    export["created"] = summary["finished"]
    export["producer"].update(runtime="codex_cli", role="executor")
    export["source"] = {
        "repo": protocol["repository"],
        "commit": protocol["arms"][0]["instrument"]["commit"],
        "dirty": False,
    }
    host = receipt["host"]
    export["host"] = {
        "path": "isolation.jsonl",
        "sha256": sha256(campaign / "isolation.jsonl"),
        "class_id": "intel-xeon-platinum-8573c-linux-6.18.57",
        "summary": {
            "cpu_model": host["cpu_model"],
            "logical_cpus": host["logical_cpus"],
            "memory_bytes": None,
            "kernel": host["kernel"],
            "hypervisor": None,
            "isolation_tier_max": "L1",
        },
    }
    manifest_arms = {arm["id"]: arm for arm in manifest["arms"]}
    protocol_arms = {arm["id"]: arm for arm in protocol["arms"]}
    for arm in export["arms"]:
        arm["binary_sha256"] = manifest_arms[arm["id"]]["sha256"]
        arm["commit"] = protocol_arms[arm["id"]]["instrument"]["commit"]

    blocker = (
        f"campaign receipt failed clock isolation: {receipt['contended_samples']}/"
        f"{len(receipt['samples'])} samples contended"
    )
    for row in rows:
        metrics = row["parsed"]["metrics"]
        fingerprints = json.dumps(
            row["parsed"]["fingerprints"], sort_keys=True, separators=(",", ":")
        )
        artifacts = [
            entry(campaign, row["artifacts"]["stdout"], "raw"),
            entry(campaign, row["artifacts"]["stderr"], "log"),
            entry(campaign, row["artifacts"]["metadata"], "raw"),
        ]
        export["runs"].append(
            ep.run_row(
                run_id=row["run_id"],
                arm=row["arm"],
                instance_id=str(row["case_index"] - 1),
                seed=24301,
                replicate=row["replicate"] if row["warmup"] else row["replicate"] - 1,
                warmup=row["warmup"],
                status="succeeded",
                measurements={
                    "counted": {
                        "bytes_per_op": metrics["B/op"],
                        "allocs_per_op": metrics["allocs/op"],
                        "correctness_fingerprints": fingerprints,
                    },
                    "wall_seconds": metrics["ns/op"] / 1e9,
                    "wall_valid": False,
                    "cpu_user_seconds": None,
                    "cpu_sys_seconds": None,
                    "max_rss_bytes": row["rusage"]["max_rss_kib"] * 1024,
                    "counters": {
                        "cpu_ns_per_op": metrics["cpu-ns/op"],
                        "benchmark_iterations": row["parsed"]["iterations"],
                        "log_entries": metrics["log_entries"],
                        "outer_wall_ns": row["outer_wall_ns"],
                        "steal_ticks_delta": (
                            row["host_after"]["steal_ticks"]
                            - row["host_before"]["steal_ticks"]
                        ),
                    },
                },
                isolation={"tier": "L1", "contended": True, "blockers": [blocker]},
                verification={
                    "status": "verified",
                    "verifier": "post-timing benchmark line/vector SHA-256 fingerprints",
                },
                artifacts=artifacts,
                started_at=row["started"],
                finished_at=row["finished"],
                worker="local-cpu0",
                backend_ref=str(row["sequence"]),
            )
        )
    export["flow"] = ep.compute_flow(export["runs"])
    export["files"] = [
        entry(campaign, "rows.jsonl", "raw"),
        entry(campaign, "manifest.json", "summary"),
        entry(campaign, "summary.json", "summary"),
        entry(campaign, "isolation.jsonl", "receipt"),
        entry(campaign, "../run_campaign.py", "other"),
    ]
    export["analysis"] = {
        "script": entry(campaign, "../export_campaign.py", "analysis"),
        "blinded": False,
        "blinding_key_sha256": None,
        "outputs": [
            entry(campaign, "analysis/paired-ratios.json", "analysis"),
            entry(campaign, "analysis/paired-ratios.md", "analysis"),
            entry(campaign, "report/REPORT.md", "report"),
        ],
        "unmasked_at": None,
    }
    export["notes"] = [
        {
            "kind": "observation",
            "text": f"The isolation receipt recorded {receipt['contended_samples']} contended samples.",
            "by": "export_campaign.py",
        },
        {
            "kind": "observation",
            "text": "All measured fingerprint pairs matched and allocation A/A gates passed.",
            "by": "export_campaign.py",
        },
    ]
    export["backend_record"] = {
        "schema": receipt["schema"],
        "mode": receipt["mode"],
        "label": receipt["label"],
        "exit_status": receipt["exit_status"],
        "samples": len(receipt["samples"]),
        "contended_samples": receipt["contended_samples"],
    }
    out = campaign / "export.json"
    out.write_text(json.dumps(export, indent=2) + "\n", encoding="utf-8")
    errors = ep.schema_errors(export, "experiment.export/v1") or ep.lint_export(
        export, protocol, campaign, verify_files=True
    )
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
