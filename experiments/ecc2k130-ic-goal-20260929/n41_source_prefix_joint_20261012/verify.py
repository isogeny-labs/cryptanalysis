"""Terminal audit of every prefix query, exhaustive join, and relation replay."""

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "n131_w18_allseed_fourpair_20261012"
sys.path.insert(0, str(SOURCE))
import fourpair_v2  # noqa: E402


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def loaded(name):
    return json.loads((HERE / name).read_text())


panel = loaded("panel.json")
protocol = loaded("protocol.json")
summary = loaded("summary.json")
assert panel["status"] == "FROZEN_N41_SOURCE_PREFIX_PANEL"
assert protocol["status"] == "FROZEN_BEFORE_N41_PREFIX_PUBLIC_QUERIES"
assert summary["status"] == "COMPLETE_BOUNDED_N41_PREFIX_PANEL"
assert summary["protocol_sha256"] == sha(HERE / "protocol.json")
for path, digest in protocol["sources"].items():
    assert sha(path) == digest, path
fixture = json.loads((SOURCE / "n41_diagonal/control_fixture.json").read_text())
_, wires, _ = fourpair_v2.build("n41", fixture["target_reciprocal"])
original = (SOURCE / "v2_n41_control.xcnf").read_text().splitlines(keepends=True)
assert original[0] == "p cnf 14803 38696\n"
receipts = {item["label"]: item for item in summary["receipts"]}
assert len(panel["rows"]) == len(receipts) == 13
for case in panel["rows"]:
    label = case["label"]
    depth = case["depth"]
    receipt = loaded(f"{label}.receipt.json")
    assert receipt == receipts[label] and receipt["formula_sha256"] == case["formula_sha256"]
    assert receipt["status"] == "BOUNDED_UNKNOWN"
    assert receipt["wall_ns"] <= protocol["per_case_parent_cap_ns"] + 2 * 10**9
    assert receipt["peak_combined_rss_bytes"] <= protocol["combined_rss_cap_bytes"]
    output = (HERE / f"{label}.xcnf").read_text().splitlines(keepends=True)
    assert output[0] == f"p cnf 14803 {38696 + 8 * depth}\n"
    assert output[1:len(original)] == original[1:]
    units = []
    for slot, prefix in enumerate(case["prefixes"]):
        for bit in range(8 - depth, 8):
            wire = wires["masks"][slot][bit]
            units.append(wire if (prefix >> (bit - (8 - depth))) & 1 else -wire)
    assert output[len(original):] == [f"{lit} 0\n" for lit in units]
    assert sha(HERE / f"{label}.xcnf") == case["formula_sha256"]
    assert sha(HERE / f"{label}.stdout") == receipt["stdout_sha256"]
    assert sha(HERE / f"{label}.stderr") == receipt["stderr_sha256"]
    lines = (HERE / f"{label}.stdout").read_text(errors="replace").splitlines()
    terminal = [line for line in lines if line.startswith("s ")]
    assert (terminal[-1] if terminal else None) == receipt["terminal"]
    assert sum(line.startswith("c rst") for line in lines) == receipt["restart_rows"]

join_protocol = loaded("join_protocol.json")
joins = loaded("join_summary.json")
assert join_protocol["status"] == "FROZEN_BEFORE_N41_PREFIX_EXHAUSTIVE_LABELS"
assert joins["status"] == "COMPLETE_N41_PREFIX_EXHAUSTIVE_LABELS"
assert joins["join_protocol_sha256"] == sha(HERE / "join_protocol.json")
for path, digest in join_protocol["sources"].items():
    assert sha(path) == digest, path
assert len(join_protocol["cases"]) == len(joins["receipts"]) == 8
labels = {"HIT_PENDING_SAGE": [], "EXACT_MISS": []}
for receipt in joins["receipts"]:
    label = receipt["label"]
    assert receipt == loaded(f"{label}.join.receipt.json")
    assert sha(HERE / f"{label}.join.stdout") == receipt["stdout_sha256"]
    assert sha(HERE / f"{label}.join.stderr") == receipt["stderr_sha256"]
    assert receipt["stop_reason"] is None and receipt["exit_code"] == 0
    assert receipt["wall_ns"] <= join_protocol["per_case_parent_cap_ns"]
    assert receipt["peak_combined_rss_bytes"] <= join_protocol["combined_rss_cap_bytes"]
    lines = (HERE / f"{label}.join.stdout").read_text().splitlines()
    assert sum(line.startswith("SOURCE_PASS ") for line in lines) == 1
    assert sum(line.startswith("LEFT_DONE ") for line in lines) == 1
    final = [line for line in lines if line.startswith(("HIT ", "EXHAUSTED "))]
    assert len(final) == 1
    expected = "HIT " if receipt["status"] == "HIT_PENDING_SAGE" else "EXHAUSTED "
    assert final[0].startswith(expected)
    labels[receipt["status"]].append(label)
assert len(labels["HIT_PENDING_SAGE"]) == 3 and len(labels["EXACT_MISS"]) == 5

analysis = loaded("analysis.json")
memory = loaded("memory_projection_result.json")
audit = loaded("sage_audit_result.json")
chart = loaded("chart_audit_result.json")
rank = loaded("rank_union_result.json")
pivot = loaded("pivot_certificate.json")
assert analysis["status"] == "PASS_N41_SOURCE_TABLE_REPLAY_AND_N131_EXACT_PREFIX_COUNT"
assert memory["status"] == "PASS_EXACT_PREFIX_LITERAL_LEFT_COUNT_N41_REPLAY"
assert audit["status"] == "PASS_INDEPENDENT_SAGE_PREFIX_HITS"
assert chart["status"] == "PASS_INDEPENDENT_N41_NONEXCEPTIONAL_S3_CHART"
assert rank["status"] == "PASS_INDEPENDENT_N41_RANK_UNION"
assert pivot["status"] == "PASS_EXCLUSIVE_SIX_ROW_MODULAR_PIVOT_CERTIFICATE"
assert {item["label"] for item in audit["relations"]} == set(labels["HIT_PENDING_SAGE"])
assert {item["label"] for item in chart["relations"]} == set(labels["HIT_PENDING_SAGE"])
assert rank["rank_with_bucket_and_prefix_hits"] == 6
assert pivot["pivot_columns"] == [27, 18, 7, 15, 87, 46]
assert len(memory["rows"]) == 13 and len(analysis["rows"]) == 13
assert "sorryAx" not in (HERE / "lean_check.txt").read_text()
result = {"status": "PASS_TERMINAL_N41_PREFIX_PUBLIC_AND_TRANSFER_AUDIT",
          "candidate_id": None, "sat_bounded_unknown_rows": len(receipts),
          "exact_join_hits": len(labels["HIT_PENDING_SAGE"]),
          "exact_join_misses": len(labels["EXACT_MISS"]),
          "independent_sage_hits": len(audit["relations"]),
          "rank_with_bucket_and_prefix_hits": rank["rank_with_bucket_and_prefix_hits"],
          "protocol_sha256": sha(HERE / "protocol.json"),
          "join_protocol_sha256": sha(HERE / "join_protocol.json"),
          "source_sha256": sha(__file__)}
with (HERE / "terminal_verification.json").open("x") as out:
    json.dump(result, out, sort_keys=True, indent=2)
    out.write("\n")
print(result["status"])
