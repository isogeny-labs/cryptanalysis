#!/usr/bin/env python3
"""Bind the Lean table selector to the two frozen glv_rho_solve C sources."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
CURRENT_SOURCE_COMMIT = "42761f85b06242cb54f2a5fa405c723451897503"
CURRENT_SHA256 = "3f3a100d635d814bdfa0f6624a40b9d77c9c564f65db2bbc568dcd4b55285efe"
BASE_COMMIT = "7cb3dce4cac9176d74afb6403048b5fabbaab834"
BASE_SHA256 = "e504bb18f0e80134c9ccf9abc1b7a825097286a759075090d2693ef82b406975"
LIVE_SOURCE_COMMIT = "d488af97a0cae6d7e96686da17aeff2f0db5f29f"
LIVE_SHA256 = "4ab176d18c6b8b562fb48aba23e67127a61d59e4450a93d781902c47579fac20"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def selector_lines(divisor: int) -> str:
    return "\n".join(
        [
            "    uint64_t sqrt_nm = ca_isqrt(n / c.m) + 1;",
            "    int lg = glv_ilog2(n) + 1;",
            f"    uint64_t rbudget = sqrt_nm / ({divisor}u * (uint64_t)lg);",
            "    uint32_t rr = 8;",
            "    while ((uint64_t)rr * 2 <= rbudget && rr * 2 <= 32) rr *= 2;",
            "    c.r = rr;",
        ]
    )


def require_selector(data: bytes, expected_hash: str, divisor: int) -> None:
    if sha256(data) != expected_hash:
        raise ValueError("src/curve.c SHA-256 differs from the pinned source")
    source = data.decode("utf-8")
    if source.count(selector_lines(divisor)) != 1:
        raise ValueError("the exact GLV table selector is absent or duplicated")
    if "if (n < 64) {" not in source or "static int glv_ilog2(uint64_t v)" not in source:
        raise ValueError("selector input guards differ from the pinned source")


def main() -> None:
    pinned_current = subprocess.run(
        ["git", "show", f"{CURRENT_SOURCE_COMMIT}:src/curve.c"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    ).stdout
    baseline = subprocess.run(
        ["git", "show", f"{BASE_COMMIT}:src/curve.c"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    ).stdout
    require_selector(pinned_current, CURRENT_SHA256, 12)
    require_selector(baseline, BASE_SHA256, 48)

    live = len(sys.argv) == 2 and sys.argv[1] == "--live"
    if len(sys.argv) > 1 and not live:
        raise SystemExit("usage: check_lean_source_binding.py [--live]")
    current = pinned_current
    if live:
        current = (ROOT / "src/curve.c").read_bytes()
        pinned_live = subprocess.run(
            ["git", "show", f"{LIVE_SOURCE_COMMIT}:src/curve.c"],
            cwd=ROOT,
            check=True,
            capture_output=True,
        ).stdout
        require_selector(current, LIVE_SHA256, 12)
        if current != pinned_live:
            raise ValueError("live source differs from its pinned commit")

    rejected = 0
    for changed in (
        current.replace(b"(12u * (uint64_t)lg)", b"(48u * (uint64_t)lg)"),
        current.replace(b"rr * 2 <= 32", b"rr * 2 <= 64"),
    ):
        try:
            require_selector(changed, sha256(changed), 12)
        except ValueError:
            rejected += 1
    if rejected != 2:
        raise AssertionError("source-binding negative controls were admitted")

    result = {
        "schema": "glv-table-lean-source-binding-v1",
        "current_source_commit": CURRENT_SOURCE_COMMIT,
        "current_source_sha256": sha256(pinned_current),
        "current_divisor": 12,
        "baseline_commit": BASE_COMMIT,
        "baseline_source_sha256": sha256(baseline),
        "baseline_divisor": 48,
        "loop_start": 8,
        "loop_cap": 32,
        "negative_controls_rejected": rejected,
        "result": "pass",
    }
    if live:
        result = {
            "schema": "glv-table-live-source-binding-v1",
            "source_commit": LIVE_SOURCE_COMMIT,
            "source_sha256": sha256(current),
            "historical_source_commit": CURRENT_SOURCE_COMMIT,
            "historical_source_sha256": sha256(pinned_current),
            "divisor": 12,
            "loop_start": 8,
            "loop_cap": 32,
            "negative_controls_rejected": rejected,
            "result": "pass",
        }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
