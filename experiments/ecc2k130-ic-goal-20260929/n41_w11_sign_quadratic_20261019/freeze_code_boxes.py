"""Freeze one positive and eight random two-root-choice five-slot boxes."""
import hashlib
import json
import random
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
cfg = json.loads((HERE/"code_box_protocol.json").read_text())
assert cfg["status"] == "FROZEN_BEFORE_CODE_BOX_PANEL"
for label, source in cfg["sources"].items():
    assert sha(source["path"]) == source["sha256"], label
panel = json.loads((HERE/"panel.json").read_text())
lines = Path(cfg["sources"]["join_input"]["path"]).read_text().splitlines()
states = defaultdict(dict)
roots = defaultdict(list)
for line in lines[2:]:
    cols = line.split()
    if cols[0] != "S":
        continue
    slot, sid, code, branch, a, b, ca, cb, x, y = map(int, cols[1:])
    states[slot][sid] = {"code":code, "columns":[ca,cb], "x":x}
    roots[(slot, code, x)].append(sid)
canonical = {slot:sorted(set(tuple(sorted(ids)) for (s,_,_),ids in roots.items() if s==slot))
             for slot in range(5)}
assert all(len(canonical[slot]) == 562 for slot in range(5))
rng = random.Random(cfg["seed"])
boxes = []
for anchor in panel["rows"][:9]:
    chosen = [list(pair) for pair in anchor["sign_state_ids"]]
    used_columns = set(anchor["columns"])
    used_x = set(anchor["x_coordinates"]+[panel["target_point"][0]])
    alternatives = []
    for slot in range(5):
        eligible = []
        for pair in canonical[slot]:
            state = states[slot][pair[0]]
            if state["code"] == states[slot][chosen[slot][0]]["code"]:
                continue
            if state["x"] in used_x or any(column in used_columns for column in state["columns"]):
                continue
            eligible.append(pair)
        assert eligible
        alt = list(rng.choice(eligible))
        alternatives.append(alt)
        used_columns.update(states[slot][alt[0]]["columns"])
        used_x.add(states[slot][alt[0]]["x"])
    assert len(used_columns) == 20 and len(used_x) == 11
    boxes.append({"kind":anchor["kind"],"root_choices":
                  [[chosen[slot],alternatives[slot]] for slot in range(5)],
                  "anchor_codes":anchor["chosen_codes"],
                  "alternative_codes":[states[slot][alternatives[slot][0]]["code"] for slot in range(5)]})
result = {"status":"FROZEN_CODE_BOX_PANEL","candidate_id":None,
          "curve_id":cfg["curve_id"],"target_point":panel["target_point"],
          "boxes":boxes,"protocol_sha256":sha(HERE/"code_box_protocol.json"),
          "script_sha256":sha(Path(__file__))}
(HERE/"code_box_panel.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
print(json.dumps({"status":result["status"],"boxes":len(boxes),
                  "positive_codes":boxes[0]["anchor_codes"]},sort_keys=True))
