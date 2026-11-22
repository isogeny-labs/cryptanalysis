"""Check the frozen ten-pair native and independent Sage receipts."""

import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
INPUT = ROOT / "n41_w8_sixpair_mitm_20261011/join_input.tsv"
PARENT = ROOT / "n41_w8_ninepair_join_control_20261012"
BASE = ROOT / "n41_w7_entropy_cubic_20261011/w8"
protocol = json.loads((HERE / "protocol.json").read_text())
receipt = json.loads((HERE / "receipt.json").read_text())
audit_protocol = json.loads((HERE / "audit_protocol.json").read_text())
audit = json.loads((HERE / "audit_result.json").read_text())
assert protocol["status"] == "FROZEN_UNPINNED_N41_TENPAIR_PUBLIC_POINT_CONTROL"
assert audit_protocol["status"] == "FROZEN_N41_UNPINNED_TENPAIR_INDEPENDENT_REPLAY"
for name, path in {
    "source": HERE / "join10.cpp",
    "included_group_source": PARENT / "join9.cpp",
    "binary": HERE / "join10",
    "runner": HERE / "run.py",
    "input": INPUT,
    "ninepair_public_point_audit": PARENT / "audit_result.json",
}.items():
    assert hashlib.sha256(path.read_bytes()).hexdigest() == protocol["sha256"][name]
for name, path in {
    "audit_source": HERE / "audit_sage.py",
    "native_receipt": HERE / "receipt.json",
    "stdout": HERE / "stdout.log",
    "input": INPUT,
    "geometry": BASE / "geometry.json",
    "fixture": BASE / "fixture.json",
    "sage_runtime": HERE / "sage_runtime_info.json",
}.items():
    assert hashlib.sha256(path.read_bytes()).hexdigest() == audit_protocol["sha256"][name]
assert receipt["status"] == "HIT_PENDING_INDEPENDENT_REPLAY"
assert receipt["stop_reason"] is None and receipt["exit_code"] == 0
assert receipt["runner_wall_ns"] < 180 * 10**9
assert receipt["peak_combined_rss_bytes_sampled"] < 4 * 1024**3
assert receipt["stderr"] == ""
assert receipt["stdout_sha256"] == hashlib.sha256((HERE / "stdout.log").read_bytes()).hexdigest()
assert audit["status"] == "PASS_INDEPENDENT_N41_PUBLIC_TENPAIR_RELATION"
assert audit["source_pairs_free"] == audit["source_edges_distinct"] == 10
assert audit["term_count"] == audit["folded_columns_nonzero"] == 20
assert audit["rank_with_prior_six_and_nine"] == 3
assert audit["public_target_transported"] == json.loads((BASE / "fixture.json").read_text())["public_target_transported"]
assert len(audit["source_pairs"]) == 10
assert len({row["edge_id"] for row in audit["source_pairs"]}) == 10
print("PASS_N41_UNPINNED_TENPAIR_PUBLIC_POINT_RECEIPTS", receipt["runner_wall_ns"],
      receipt["peak_combined_rss_bytes_sampled"], audit["folded_columns_nonzero"])
