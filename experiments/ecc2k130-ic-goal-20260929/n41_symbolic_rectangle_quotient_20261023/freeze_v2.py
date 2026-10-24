"""Freeze every complete 2x2 depth-six N41 rectangle before the sweep."""
import hashlib
import json
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
first = json.loads((HERE / "protocol.json").read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


geometry = json.loads(Path(first["sources"]["geometry"]["path"]).read_text())
cases = [json.loads(line) for line in Path(first["sources"]["coordinate_audit"]["path"]).open()]
left_masks = [geometry["blocks"][0]["states"][4 * i]["a"] for i in range(40)]
right_masks = [geometry["blocks"][1]["states"][4 * i]["a"] for i in range(40)]
groups = defaultdict(list)
for index, case in enumerate(cases):
    key = (left_masks[case["left_code"]] >> 2,
           right_masks[case["right_code"]] >> 2)
    groups[key].append(index)
rectangles = []
for key, indices in sorted(groups.items()):
    left = {cases[i]["left_code"] for i in indices}
    right = {cases[i]["right_code"] for i in indices}
    if len(indices) == 4 and len(left) == len(right) == 2:
        assert {(cases[i]["left_code"], cases[i]["right_code"]) for i in indices} == {
            (a, b) for a in left for b in right}
        rectangles.append({"label": f"prefix_{key[0]}_{key[1]}",
                           "prefix": list(key), "case_indices": indices})
assert len(rectangles) == 132
assert any(966 in rectangle["case_indices"] for rectangle in rectangles)
assert any(rectangle["prefix"] == [0, 4] for rectangle in rectangles)
sources = dict(first["sources"])
for name, path in {
    "producer_v2": HERE / "run_v2.py",
    "auditor_v2": HERE / "audit_sage_v2.py",
    "freeze_v2": HERE / "freeze_v2.py",
    "first_protocol": HERE / "protocol.json",
    "first_result": HERE / "result.json",
    "first_audit": HERE / "audit_result.json",
    "freeze_attempt1_failure": HERE / "freeze_v2_attempt1_failure.json",
}.items():
    sources[name] = {"path": str(path), "sha256": sha(path)}
record = {key: value for key, value in first.items()
          if key not in ("sources", "rectangles", "selection", "status")}
record.update({"status": "FROZEN_N41_COMPLETE_2X2_SWEEP",
               "selection": "All 132 complete Cartesian 2x2 product-code rectangles at depth (6,6), in ascending prefix order; fixed cubic bit (2,5,8). Two other four-family rectangles are incomplete Cartesian sources and remain outside this exact quotient ring.",
               "rectangles": rectangles, "sources": sources})
assert not (HERE / "protocol_v2.json").exists()
(HERE / "protocol_v2.json").write_text(json.dumps(record, sort_keys=True, indent=2) + "\n")
