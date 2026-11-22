"""Read-only identity, cap, proof-log and cross-audit receipt verification."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
p=json.loads((HERE/"protocol.json").read_text())
a=json.loads((HERE/"audit_protocol.json").read_text())
r=json.loads((HERE/"result.json").read_text())
v=json.loads((HERE/"audit_result.json").read_text())
for cfg in (p,a):
    for name,row in cfg["sources"].items():
        assert sha(row["path"])==row["sha256"],name
assert r["protocol_sha256"]==sha(HERE/"protocol.json")
assert v["audit_protocol_sha256"]==sha(HERE/"audit_protocol.json")
assert v["producer_sha256"]==sha(HERE/"result.json")
assert r["status"]=="PASS_N131_W23_TRIPLE_X_QUADRATIC_CAPACITY"
assert v["status"]=="PASS_INDEPENDENT_N131_TRIPLE_X_QUADRATIC_AUDIT"
assert r["curve_id"]==v["curve_id"]==p["curve_id"]
assert len(r["source_family_masks"])==v["families"]==p["family_cap"]==320
assert r["source_family_masks"][:4]==[[3,898617],[10,898608],[41,898579],[46,898580]]
assert all(left^right==p["seed_mask"] and left<right for left,right in r["source_family_masks"])
assert [row["families"] for row in r["rows"]]==p["checkpoints"]
assert all(row["distinct_x"]==32*row["families"] for row in r["rows"])
assert r["rows"][-1]["quadratic_rank"]==v["quadratic_rank"]==8646
assert v["first_full_rank_family"]==271
assert v["first_quadratic_hull_entry"]=={"constructed":1,"panel_public":271,"public":271}
assert r["rows"][-1]["target_checks"]["public"]=={"exact":False,"linear":True,"quadratic":True}
assert r["peak_rss_sample_bytes"]<p["rss_cap_bytes"]
assert r["total_seconds"]<p["wall_cap_seconds"]
assert v["wall_seconds"]<a["wall_cap_seconds"]
assert v["maxrss_raw"]<a["rss_cap_bytes"]
lean=(HERE/"lean_build.stdout.txt").read_text()
assert "'QuadraticHull.true_source_passes' depends on axioms: [propext, Quot.sound]" in lean
assert "'QuadraticHull.quadratic_feature_dimension' does not depend on any axioms" in lean
assert not (HERE/"lean_build.stderr.txt").read_text()
print(json.dumps({"status":"PASS_N131_TRIPLE_X_QUADRATIC_RECEIPT",
                  "families":320,"first_full_rank_family":271,
                  "producer_sha256":sha(HERE/"result.json"),
                  "audit_sha256":sha(HERE/"audit_result.json")},sort_keys=True))
