#!/usr/bin/env python3
"""Bind the Lean table selector to the frozen glv_rho_solve C sources.

The default mode checks the two historical sources (divisor 48 and 12, cap 32).
`--live` checks the size-dependent-cap selector in the working tree against its
pinned commit, and re-checks the previous live pin (divisor 12, cap 32).
"""

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
PRIOR_LIVE_SOURCE_COMMIT = "8bf648dcbefe7b8131e5fb26909c77e68778332a"
PRIOR_LIVE_SHA256 = "60796724ef7d7c5b3b7dfd89c29db85d5e188deb247b5d9d0bd69b84551afe20"
LIVE_SOURCE_COMMIT = "e71ebecaf3a076590ddd3affa4878b4c80d85095"
LIVE_SHA256 = "e1d624e58c54f25f9225be97481b50c0ed406cedcfdffa8ba66f01a5fbed7f63"
CAP_THRESHOLD_LG = 40
CAP_BELOW = 32
CAP_FROM = 128


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def selector_lines(divisor: int, sized_cap: bool = False) -> str:
    """The exact selector text; `sized_cap` selects the size-dependent cap."""
    if sized_cap:
        cap_lines = [
            f"    uint32_t rcap = lg >= {CAP_THRESHOLD_LG} ? {CAP_FROM} : {CAP_BELOW};",
            "    uint32_t rr = 8;",
            "    while ((uint64_t)rr * 2 <= rbudget && rr * 2 <= rcap) rr *= 2;",
        ]
    else:
        cap_lines = [
            "    uint32_t rr = 8;",
            "    while ((uint64_t)rr * 2 <= rbudget && rr * 2 <= 32) rr *= 2;",
        ]
    return "\n".join(
        [
            "    uint64_t sqrt_nm = ca_isqrt(n / c.m) + 1;",
            "    int lg = glv_ilog2(n) + 1;",
            f"    uint64_t rbudget = sqrt_nm / ({divisor}u * (uint64_t)lg);",
            *cap_lines,
            "    c.r = rr;",
        ]
    )


def require_selector(
    data: bytes, expected_hash: str, divisor: int, sized_cap: bool = False
) -> None:
    if sha256(data) != expected_hash:
        raise ValueError("src/curve.c SHA-256 differs from the pinned source")
    source = data.decode("utf-8")
    if source.count(selector_lines(divisor, sized_cap)) != 1:
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
        prior_live = subprocess.run(
            ["git", "show", f"{PRIOR_LIVE_SOURCE_COMMIT}:src/curve.c"],
            cwd=ROOT,
            check=True,
            capture_output=True,
        ).stdout
        require_selector(prior_live, PRIOR_LIVE_SHA256, 12)
        require_selector(current, LIVE_SHA256, 12, sized_cap=True)
        if current != pinned_live:
            raise ValueError("live source differs from its pinned commit")

    rejected = 0
    if live:
        # Negative controls for the size-dependent selector: each changes one
        # of the divisor, the cap threshold, the large cap, or the small cap,
        # or drops the cap variable, and must be refused.
        controls = (
            current.replace(b"(12u * (uint64_t)lg)", b"(48u * (uint64_t)lg)"),
            current.replace(b"lg >= 40 ?", b"lg >= 41 ?"),
            current.replace(b"? 128 : 32", b"? 64 : 32"),
            current.replace(b"? 128 : 32", b"? 128 : 64"),
            current.replace(b"rr * 2 <= rcap", b"rr * 2 <= 32"),
        )
        expected_rejections = len(controls)
    else:
        controls = (
            current.replace(b"(12u * (uint64_t)lg)", b"(48u * (uint64_t)lg)"),
            current.replace(b"rr * 2 <= 32", b"rr * 2 <= 64"),
        )
        expected_rejections = 2
    for changed in controls:
        if changed == current:
            raise AssertionError("a negative control did not change the source")
        try:
            require_selector(changed, sha256(changed), 12, sized_cap=live)
        except ValueError:
            rejected += 1
    if rejected != expected_rejections:
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
            "schema": "glv-table-live-source-binding-v2",
            "source_commit": LIVE_SOURCE_COMMIT,
            "source_sha256": sha256(current),
            "prior_live_source_commit": PRIOR_LIVE_SOURCE_COMMIT,
            "prior_live_source_sha256": sha256(prior_live),
            "prior_live_loop_cap": 32,
            "historical_source_commit": CURRENT_SOURCE_COMMIT,
            "historical_source_sha256": sha256(pinned_current),
            "divisor": 12,
            "loop_start": 8,
            "cap_threshold_lg": CAP_THRESHOLD_LG,
            "cap_below_threshold": CAP_BELOW,
            "cap_from_threshold": CAP_FROM,
            "negative_controls_rejected": rejected,
            "result": "pass",
        }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
