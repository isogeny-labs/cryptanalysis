"""Evaluate a two-quadratic characteristic-two resultant on frozen rows."""
import hashlib
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "n131_w18_allseed_fourpair_20261012"))
from fourpair_v2 import Field

sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
cfg = json.loads((HERE / "protocol.json").read_text())
assert cfg["status"] == "FROZEN_BEFORE_N41_QUADRATIC_RESULTANT_PREFLIGHT"
for item in cfg["sources"].values():
    assert sha(item["path"]) == item["sha256"]
panel = json.loads(Path(cfg["sources"]["panel"]["path"]).read_text())
join = json.loads(Path(cfg["sources"]["join_rows"]["path"]).read_text())
fixture = json.loads(Path(cfg["sources"]["fixture"]["path"]).read_text())
assert len(panel) == len(join["rows"]) == 33
F = Field(41, [0, 3])


def s3(a, b, c):
    ab = F.mul(a, b)
    abc = F.mul(ab, c)
    return F.square(abc) ^ abc ^ F.square(a ^ b) ^ F.square(c)


def resultant(A, B, C, D, E, G):
    return F.square(F.mul(A, G) ^ F.mul(C, D)) ^ F.mul(
        F.mul(A, E) ^ F.mul(B, D), F.mul(B, G) ^ F.mul(C, E))


start = time.monotonic()
t = fixture["public_reciprocal"]
rows = []
for row, reference in zip(panel, join["rows"]):
    assert row["state_ids"] == reference["state_ids"]
    z = row["z"]
    u = reference["pair3_reciprocal"]
    v = reference["pair4_reciprocal"]
    y = reference["right_sum_reciprocal"]
    uv = F.mul(u, v)
    zt = F.mul(z, t)
    A, B, C = 1 ^ F.square(uv), uv, F.square(u ^ v)
    D, E, G = 1 ^ F.square(zt), zt, F.square(z ^ t)
    f_at_y = F.mul(A, F.square(y)) ^ F.mul(B, y) ^ C
    g_at_y = F.mul(D, F.square(y)) ^ F.mul(E, y) ^ G
    value = resultant(A, B, C, D, E, G)
    assert f_at_y == s3(u, v, y) == 0
    assert g_at_y == s3(z, y, t)
    assert (g_at_y == 0) == reference["target_link_zero"]
    if g_at_y == 0:
        assert value == 0
    rows.append({"kind": row["kind"], "control_index": row.get("control_index"),
                 "resultant_zero": value == 0, "resultant": value,
                 "target_link_zero": g_at_y == 0,
                 "first_lead_zero": A == 0, "second_lead_zero": D == 0,
                 "first_linear_nonzero": B != 0, "second_linear_nonzero": E != 0})
assert rows[0]["kind"] == "positive" and rows[0]["resultant_zero"]
result = {"status": "PASS_N41_QUADRATIC_RESULTANT_PREFLIGHT",
          "candidate_id": None, "curve_id": cfg["curve_id"],
          "rows": rows, "resultant_zero_count": sum(r["resultant_zero"] for r in rows),
          "target_link_zero_count": sum(r["target_link_zero"] for r in rows),
          "first_lead_zero_count": sum(r["first_lead_zero"] for r in rows),
          "second_lead_zero_count": sum(r["second_lead_zero"] for r in rows),
          "seconds": time.monotonic() - start,
          "protocol_sha256": sha(HERE / "protocol.json"), "script_sha256": sha(__file__)}
(HERE / "preflight_result.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
print(json.dumps({"status": result["status"],
                  "resultant_zero_count": result["resultant_zero_count"],
                  "target_link_zero_count": result["target_link_zero_count"],
                  "seconds": result["seconds"]}, sort_keys=True))
