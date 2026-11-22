"""Check frozen identities, bounded run status, and independent replay receipt."""
import hashlib
import json
from pathlib import Path

h = Path(__file__).resolve().parent
root = h.parent
parent = root / "n41_w8_ninepair_join_control_20261012"
paths = {
    "source": h / "join10_x.cpp",
    "binary": h / "join10_x",
    "runner": h / "run.py",
    "included_group_source": parent / "join9.cpp",
    "input": root / "n41_w8_sixpair_mitm_20261011/join_input.tsv",
    "ninepair_public_point_audit": parent / "audit_result.json",
    "baseline_protocol": root / "n41_w8_tenpair_density_control_20261012/protocol.json",
    "baseline_receipt": root / "n41_w8_tenpair_density_control_20261012/receipt.json",
}
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
p = json.loads((h / "protocol.json").read_text())
assert {k: sha(v) for k, v in paths.items()} == p["sha256"]
r = json.loads((h / "receipt.json").read_text())
a = json.loads((h / "audit_result.json").read_text())
ap = json.loads((h / "audit_protocol.json").read_text())
assert r["protocol_sha256"] == sha(h / "protocol.json")
assert r["stdout_sha256"] == sha(h / "stdout.log")
assert r["stderr_sha256"] == sha(h / "stderr.log")
assert r["status"] == "HIT_PENDING_INDEPENDENT_REPLAY" and r["stop_reason"] is None
assert r["exit_code"] == 0 and r["runner_wall_ns"] < 180 * 10**9
assert r["peak_combined_rss_bytes_sampled"] < 4 * 1024**3
assert r["hit_line"] in (h / "stdout.log").read_text().splitlines()
assert ap["sha256"] == {
    "audit_source": sha(h / "audit_sage.py"),
    "native_receipt": sha(h / "receipt.json"),
    "stdout": sha(h / "stdout.log"),
    "input": sha(paths["input"]),
    "geometry": sha(root / "n41_w7_entropy_cubic_20261011/w8/geometry.json"),
    "fixture": sha(root / "n41_w7_entropy_cubic_20261011/w8/fixture.json"),
    "sage_runtime": sha(h / "sage_runtime_info.json"),
}
assert a["status"] == "PASS_INDEPENDENT_N41_PUBLIC_XQUOTIENT_TENPAIR_RELATION"
assert a["sha256"]["audit_source"] == sha(h / "audit_sage.py")
assert a["sha256"]["stdout"] == sha(h / "stdout.log")
assert a["source_edges_distinct"] == 10 and a["term_count"] == 20
assert a["public_target_transported"] == [920359962848, 755404565011]
prior = json.loads(paths["baseline_receipt"].read_text())
new = r["hit_line"].split()
old = prior["hit_line"].split()
assert int(new[12]) == int(old[12]) == 5_000_000
assert int(new[13]) == int(old[13]) == 6_741_384
assert int(new[14]) == 136_258 and int(old[14]) == 898_812
print("PASS_FROZEN_N41_XQUOTIENT_RECEIPT", a["folded_columns_nonzero"])
