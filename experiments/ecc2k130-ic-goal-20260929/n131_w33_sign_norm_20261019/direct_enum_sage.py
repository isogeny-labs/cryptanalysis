"""Matched finite-box direct group-enumeration diagnostic on the public point."""
import hashlib
import json
import resource
import time
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
cfg = json.loads((HERE / "direct_protocol.json").read_text())
assert cfg["status"] == "FROZEN_BEFORE_N131_DIRECT_ENUM"
for label, source in cfg["sources"].items():
    assert sha(source["path"]) == source["sha256"], label
panel = json.loads((HERE / "panel.json").read_text())
public = json.loads((HERE / "public_result.json").read_text())
assert public["status"] == "COMPLETE_N131_SIGN_NORM"
start = time.monotonic()
R = PolynomialRing(GF(2), "u")
u = R.gen()
F = GF(2**131, name="u", modulus=u**131 + u**13 + u**2 + u + 1)
E = EllipticCurve(F, [1, 0, 0, 0, 1])
dec = F.from_integer
O = E(0)
rows = []
for box_index in range(1, 9):
    box = panel["boxes"][box_index]
    target = E(*(dec(v) for v in box["target_point"]))
    choices = [[[E(*(dec(v) for v in xy)) for xy in choice["signed_points"]]
                for choice in slot] for slot in box["choices"]]
    box_start = time.monotonic()
    hits = []
    for root in range(32):
        selected = [choices[slot][root >> slot & 1] for slot in range(5)]
        for sign in range(32):
            points = [selected[slot][sign >> slot & 1] for slot in range(5)]
            if sum(points, O) == target:
                hits.append([root, sign])
    assert hits == public["rows"][box_index - 1]["group_hits"]
    rows.append({"box_index": box_index, "assignments": 1024,
                 "group_hits": hits, "enumeration_seconds": time.monotonic() - box_start})
result = {"status": "COMPLETE_N131_DIRECT_ENUM", "candidate_id": None,
          "curve_id": cfg["curve_id"], "boxes_completed": len(rows),
          "assignments_checked": sum(x["assignments"] for x in rows),
          "group_hits": sum(len(x["group_hits"]) for x in rows),
          "enumeration_seconds": sum(x["enumeration_seconds"] for x in rows),
          "rows": rows, "wall_seconds": time.monotonic() - start,
          "peak_rss_raw": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
          "protocol_sha256": sha(HERE / "direct_protocol.json"),
          "script_sha256": sha(Path(__file__))}
(HERE / "direct_result.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
print(json.dumps({key: result[key] for key in
                  ("status", "assignments_checked", "enumeration_seconds", "wall_seconds")},
                 sort_keys=True), flush=True)
