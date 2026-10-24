"""Build exact residual charts for every state of the fourth pair slot."""
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
GEOMETRY = ROOT / "n41_w8_fixed_sum_table_20261009/geometry.json"
WITNESS = ROOT / "n41_w8_fixedseed_ordinary_join_20261013/protocol.json"
CURVE_AUDIT = ROOT / "n41_w8_fixed_sum_table_20261009/audit.py"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


spec = importlib.util.spec_from_file_location("independent_sage_curve", CURVE_AUDIT)
old = importlib.util.module_from_spec(spec)
spec.loader.exec_module(old)
curve, elem, integer = old.sage_curve()
geo = json.loads(GEOMETRY.read_text())
proto = json.loads(WITNESS.read_text())
raw_target = curve(*(elem(x) for x in proto["raw_target"]))
suffix_ids = [14, 109, 51]
suffix = curve(0)
for axis, state_id in enumerate(suffix_ids, 4):
    suffix += curve(*(elem(x) for x in geo["blocks"][axis]["states"][state_id]["raw_sum"]))
first_four_target = raw_target - suffix
table = []
for code in range(40):
    row = []
    for state_id in range(4*code, 4*code+4):
        state = geo["blocks"][3]["states"][state_id]
        point = curve(*(elem(x) for x in state["raw_sum"]))
        residual = first_four_target - point
        assert residual != curve(0) and residual[0] != 1
        chart = 1 / (residual[0] + 1)
        row.append({"state_id": state_id, "chart": integer(chart),
                    "raw_point": [integer(residual[0]), integer(residual[1])]})
    table.append(row)
assert table[0][0]["chart"] == 112961062585
out = {"status": "PASS_N41_FOURTH_PAIR_TARGET_TABLE", "curve_id": geo["curve_id"],
       "raw_target": proto["raw_target"], "suffix_state_ids": suffix_ids,
       "fourth_pair_codes": 40, "states_per_code": 4, "rows": table,
       "source_sha256": {"geometry": sha(GEOMETRY), "witness_protocol": sha(WITNESS),
                         "sage_curve_audit": sha(CURVE_AUDIT),
                         "producer": sha(Path(__file__))}}
(HERE / "target_table.json").write_text(json.dumps(out, sort_keys=True, indent=2) + "\n")
print(json.dumps({"status": out["status"], "states": sum(map(len, table))}, sort_keys=True))
