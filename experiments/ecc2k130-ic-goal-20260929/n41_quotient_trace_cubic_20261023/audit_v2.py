"""Independent checked-Sage replay of quotient masks and target decisions."""
import hashlib
import importlib.util
import json
import resource
import struct
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
OLD = ROOT / "n41_w8_fixed_sum_table_20261009/audit.py"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


cfg = json.loads((HERE / "protocol_v2.json").read_text())
for name, item in cfg["sources"].items():
    assert sha(item["path"]) == item["sha256"], name
result = json.loads((HERE / "result.json").read_text())
assert result["status"] == "PASS_N41_ROOT_FREE_QUOTIENT_CUBIC_V2"
spec = importlib.util.spec_from_file_location("prior_sage_curve", OLD)
old = importlib.util.module_from_spec(spec)
spec.loader.exec_module(old)
curve, elem, integer = old.sage_curve()
cases = [json.loads(line) for line in Path(cfg["sources"]["coordinate_audit"]["path"]).open()]
target_x = struct.unpack("<65Q", Path(cfg["sources"]["target_residuals"]["path"]).read_bytes())
started = time.monotonic()


def feature(value):
    active = [i for i in range(1, 41) if (value >> i) & 1]
    positions = {}
    bit = 1
    for i in range(1, 41):
        for j in range(i + 1, 41):
            positions[(i, j)] = bit
            bit += 1
    for i in range(1, 41):
        for j in range(i + 1, 41):
            for k in range(j + 1, 41):
                positions[(i, j, k)] = bit
                bit += 1
    assert bit == 10661
    out = value & 1
    for a, i in enumerate(active):
        for b in range(a + 1, len(active)):
            j = active[b]
            out |= 1 << positions[(i, j)]
            for k in active[b + 1:]:
                out |= 1 << positions[(i, j, k)]
    return out


full = (1 << 10661) - 1
target_features = [feature(integer(1 / elem(x))) for x in target_x]
checked_roots = 0
for row in result["rows"]:
    case = cases[row["index"]]
    assert row["codes"] == [case["left_code"], case["right_code"]]
    roots = case["reciprocal_coordinates"]
    assert len(roots) == len(set(roots)) == 8
    h = [elem(v) for v in row["h"]]
    assert h[-1] == 1
    assert sum(h) != 0
    zero, one = full, full
    for z in roots:
        fz = elem(z) / (elem(z) + 1)
        value = 0
        for coefficient in reversed(h):
            value = value * fz + coefficient
        assert value == 0
        lifted = feature(z)
        zero &= full ^ lifted
        one &= lifted
        checked_roots += 1
    assert zero == int(row["zero_mask_hex"], 16), row["index"]
    assert one == int(row["one_mask_hex"], 16), row["index"]
    rejected = [panel for panel, value in enumerate(target_features)
                if (zero & value) | (one & (full ^ value))]
    assert rejected == row["rejected_target_indices"]
    assert all(panel not in rejected for panel in range(65)
               if target_x[panel] in case["x_coordinates"])
    assert time.monotonic() - started < cfg["wall_cap_seconds"]
    assert resource.getrusage(resource.RUSAGE_SELF).ru_maxrss < cfg["rss_cap_bytes"]

assert checked_roots == 8 * len(result["rows"])
assert 0 not in result["rows"][cfg["panel_indices"].index(cfg["witness_index"])]["rejected_target_indices"]
audit = {"status": "PASS_INDEPENDENT_SAGE_QUOTIENT_CUBIC_AUDIT",
         "candidate_id": None, "families_checked": len(result["rows"]),
         "roots_checked": checked_roots,
         "target_decisions_checked": 65 * len(result["rows"]),
         "wall_seconds": time.monotonic() - started,
         "self_maxrss_raw": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
         "result_sha256": sha(HERE / "result.json"),
         "protocol_sha256": sha(HERE / "protocol_v2.json")}
(HERE / "audit_result.json").write_text(json.dumps(audit, sort_keys=True, indent=2) + "\n")
print(json.dumps({"status": audit["status"], "roots_checked": checked_roots}, sort_keys=True))
