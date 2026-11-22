"""Synthetic software checks only; no curve data, solve or timing experiment."""
import copy
import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location("cold_cost_audit", Path(__file__).with_name("cold_cost_audit.py"))
M = importlib.util.module_from_spec(spec)
spec.loader.exec_module(M)


def fixture():
    panel = {"schema": "cold-transfer-cost/v1", "boundary": "disjoint-cold-per-query",
             "identity": {k: "synthetic" for k in M.IDENTITY},
             "targets": [f"fixture-{i}" for i in range(5)], "repeats": 2,
             "arms": {"direct": "source", "mapped": "transferred"}, "rows": []}
    panel["identity"].update(subgroup_order="43", cohort_sha256="a" * 64, host_receipt_sha256="b" * 64)
    for arm in panel["arms"]:
        for target in panel["targets"]:
            for repeat in range(2):
                phases = {k: 1_000_000 for k in M.PHASES}
                phases["solve"] = 6_000_000 if arm == "direct" else 4_000_000
                panel["rows"].append({"arm": arm, "target": target, "repeat": repeat,
                                      "status": "ok", "unit": "ns", "phases_ns": phases,
                                      "total_ns": sum(phases.values()), "peak_rss_bytes": 1000,
                                      "source_sha256": "c" * 64, "binary_sha256": "d" * 64,
                                      "answer_check": "synthetic-only"})
    return panel


def test_exact_units_and_complete_cost():
    got = M.audit(fixture())
    assert got["source_over_transferred"] == 1.25
    assert got["additional_headroom_ms_per_query"] == 2
    assert got["additional_headroom_ns_per_query"] == 2_000_000


@pytest.mark.parametrize("mutation", ["missing", "extra", "negative", "float", "bool", "unit", "total", "status", "memory", "answer", "digest", "repeat", "boundary", "row"])
def test_rejects_incomplete_or_malformed_evidence(mutation):
    p = fixture()
    r = p["rows"][0]
    if mutation == "missing": del r["phases_ns"]["setup"]
    elif mutation == "extra": r["phases_ns"]["nested_solve"] = 0
    elif mutation == "negative": r["phases_ns"]["solve"] = -1
    elif mutation == "float": r["phases_ns"]["solve"] = float("nan")
    elif mutation == "bool": r["phases_ns"]["solve"] = True
    elif mutation == "unit": r["unit"] = "ms"
    elif mutation == "total": r["total_ns"] -= 1
    elif mutation == "status": r["status"] = "timeout"
    elif mutation == "memory": r["peak_rss_bytes"] = 0
    elif mutation == "answer": del r["answer_check"]
    elif mutation == "digest": r["binary_sha256"] = "bad"
    elif mutation == "repeat": r["repeat"] = True
    elif mutation == "boundary": p["boundary"] = "amortized"
    elif mutation == "row": p["rows"].pop()
    with pytest.raises(ValueError): M.audit(p)


def test_best_arm_is_fixed_for_whole_cohort_and_overhead_can_erase_gain():
    p = fixture()
    p["arms"]["direct2"] = "source"
    for row in list(p["rows"]):
        if row["arm"] == "direct":
            extra = copy.deepcopy(row)
            extra["arm"] = "direct2"
            extra["phases_ns"]["solve"] = 0 if row["target"] == "fixture-0" else 10_000_000
            extra["total_ns"] = sum(extra["phases_ns"].values())
            p["rows"].append(extra)
        elif row["arm"] == "mapped":
            row["phases_ns"]["setup"] += 3_000_000
            row["total_ns"] += 3_000_000
    result = M.audit(p)
    assert result["best_fixed_source"][1] == "direct"
    assert result["source_over_transferred"] < 1
