"""Read-only terminal audit of the frozen image-filter experiment."""
import hashlib
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def checked_sources(protocol_file):
    p = read(protocol_file)
    assert p["status"].startswith("FROZEN_BEFORE_")
    for path, expected in p["sources"].items():
        assert sha(path) == expected, path
    return p


p = checked_sources(HERE / "protocol.json")
ap = checked_sources(HERE / "audit_protocol.json")
gp = checked_sources(HERE / "group_bridge_protocol.json")
r = read(HERE / "result.json")
a = read(HERE / "audit_sage_result.json")
g = read(HERE / "group_bridge_result.json")
assert r["status"] == "PASS_EXACT_FINALPAIR_CODE_RECOVERY_PANEL"
assert r["protocol_sha256"] == sha(HERE / "protocol.json")
assert r["candidate_id"] is None and r["curve_id"] == p["curve_id"]
assert r["total_wall_seconds"] < p["wall_cap_seconds"]
assert r["self_maxrss_bytes"] < p["rss_cap_bytes"]
assert abs(sum(r["phase_seconds"].values()) - r["total_wall_seconds"]) < 1e-8
assert r["reachable_draws"] <= p["reachable_draw_cap"]


def summary(rows):
    return {"count": len(rows),
            "chart_counts": dict(Counter(row["chart"] for row in rows)),
            "rank_counts": dict(Counter(str(row["map_rank"]) for row in rows)),
            "linear_image_hits": sum(bool(row["linear_image_codes"]) for row in rows),
            "allowed_code_hits": sum(bool(row["allowed_codes"]) for row in rows)}


for key, expected_count in (("uniform", 1024), ("reachable", 256)):
    rows = r[key]
    assert len(rows) == expected_count
    assert len({row["w"] for row in rows}) == expected_count
    assert all(0 <= row["w"] < 2**41 for row in rows)
    assert summary(rows) == r[key + "_summary"]
    assert all(row["map_rank"] == 8 for row in rows)
    assert all(not row["linear_image_codes"] for row in rows)
assert all(row["field_root_count"] == 2 for row in r["reachable"])
assert len(r["special"]) == 4
assert r["positive"]["allowed_codes"] == [95]
assert r["positive"]["w"] not in {row["w"] for row in r["uniform"]}
assert r["positive"]["w"] not in {row["w"] for row in r["reachable"]}

assert a["status"] == "PASS_INDEPENDENT_SAGE_FINALPAIR_IMAGE_REPLAY"
assert a["audit_protocol_sha256"] == sha(HERE / "audit_protocol.json")
assert a["rows_checked"] == 1285
assert a["reachable_group_sums_checked"] == 256
assert a["positive_group_relation_checked"]
assert g["status"] == "PASS_GROUP_TO_UNRESTRICTED_PRODUCT_BRIDGE"
assert g["protocol_sha256"] == sha(HERE / "group_bridge_protocol.json")
assert g["reachable_sums_checked"] == 256
assert g["reachable_with_two_residual_products"] == 256
assert g["exception_counts"] == {"minus": 0, "plus": 0}
assert 618674919662 in g["positive_products"]
assert not (HERE / "run.stderr").read_bytes()
assert not (HERE / "audit_sage.stderr").read_bytes()
assert not (HERE / "group_bridge.stderr").read_bytes()
lean = (HERE / "lean.stdout").read_text()
for theorem in ("map_additive", "equal_output_two_preimages", "second_root",
                "shared_root_resultant_zero", "unrestricted_product_from_root"):
    assert f"'FinalPairImage.{theorem}' depends on axioms:" in lean
assert "sorryAx" not in lean
assert not (HERE / "lean.stderr").read_bytes()
assert not any(bad in (HERE / "FinalPairImage.lean").read_text()
               for bad in ("sorry", "admit", "sorryAx", "axiom "))

print(json.dumps({"verification": "PASS_FROZEN_FINALPAIR_IMAGE_EVIDENCE",
                  "positive_code": 95,
                  "uniform_rows": len(r["uniform"]),
                  "reachable_rows": len(r["reachable"]),
                  "reachable_with_two_field_roots": 256,
                  "sparse_image_hits": 0,
                  "independent_sage_rows": a["rows_checked"]}, sort_keys=True))
