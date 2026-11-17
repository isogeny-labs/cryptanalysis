#!/usr/bin/env python3
"""Check the narrow source-pin amendment; the native gate must replay it separately."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OLD = "reports/lean-current-corpus-20261101-glv-cap/receipt.json"
NEW = "reports/lean-current-corpus-20261117-glv-source/receipt.json"
BINDING = "experiments/glv-table-rule-confirm-20261022/live-source-binding.json"
OLD_SHA256 = "af4ce41f6ab652a4db38d16c2fbe5bdfd3d6d8ba38702004740e71fa8ea83d78"


def check(root: Path) -> None:
    old_bytes = (root / OLD).read_bytes()
    if hashlib.sha256(old_bytes).hexdigest() != OLD_SHA256:
        raise ValueError("historical corpus receipt changed")
    old = json.loads(old_bytes)
    expected = copy.deepcopy(old)
    binding_bytes = (root / BINDING).read_bytes()
    binding = json.loads(binding_bytes)
    if binding["previous_live_source_commit"] != old["fresh_native_evidence"]["glv_live_source_commit"]:
        raise ValueError("binding lost the historical sized-cap source")
    if binding["previous_live_source_sha256"] != old["fresh_native_evidence"]["glv_live_source_sha256"]:
        raise ValueError("binding lost the historical sized-cap hash")
    evidence = expected["fresh_native_evidence"]
    evidence["glv_live_source_commit"] = binding["source_commit"]
    evidence["glv_live_source_sha256"] = binding["source_sha256"]
    evidence["glv_live_binding_receipt_sha256"] = hashlib.sha256(binding_bytes).hexdigest()
    if json.loads((root / NEW).read_bytes()) != expected:
        raise ValueError("new corpus expectation changes more than the three source bindings")


if __name__ == "__main__":
    check(ROOT)
    print("Three source-binding amendments checked; native corpus replay remains required.")
