#!/usr/bin/env python3
"""Bind the v8 fixed-peer-key candidate to the generic remote A/B runner."""

from __future__ import annotations

from pathlib import Path

import run_remote_ab as runner


runner.BASELINE_COMMIT = "7c712913b7e912494e87c35e854cfd0129bad89c"
runner.BASELINE_TREE = "735e671e9492fb890a4e87825644c46bace88e4a"
runner.BASELINE_COORD_BLOB = "0d3f53806361e7442bc1d108c16b8b847f029918"
runner.CANDIDATE_COMMIT = "37b96362a53a7364dd4cc2a18f450a3627ec08d3"
runner.CANDIDATE_PARENT = "7c712913b7e912494e87c35e854cfd0129bad89c"
runner.CANDIDATE_TREE = "5a2653198b943e93c9f7ae7906ad39d74baf7a79"
runner.CANDIDATE_COORD_BLOB = "edba225c5a1ff613d71a21aa8d2c528096831b6f"
runner.CANDIDATE_DIFF_SHA256 = (
    "e29818ed168eaa886dfdc4be3c90777b1026b89246b760fd76d31614f33e8417"
)
runner.COMMON_TEST_COMMIT = "37b96362a53a7364dd4cc2a18f450a3627ec08d3"
runner.COMMON_TEST_BLOB = "b487d974638f5fe81a2921fa002b8ce481b956ad"
runner.COMMON_TEST_SHA256 = (
    "4bf65f9fa27f46e04d287e8fc49ce33d00e9fb74e176a25677b04d9f883e35b8"
)
runner.RUNNER_BINDING_PATH = str(Path(__file__).resolve())


if __name__ == "__main__":
    raise SystemExit(runner.main())
