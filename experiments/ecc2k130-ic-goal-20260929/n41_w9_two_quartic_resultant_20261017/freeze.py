"""Freeze one positive and 32 source-valid negative code families."""
import hashlib
import json
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent
p = json.loads((HERE / "panel_protocol.json").read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


for path, expected in p["sources"].items():
    assert sha(path) == expected, path
assert not (HERE / "panel.json").exists()
source = json.loads(Path(p["states"]).read_text())
fixture = json.loads(Path(p["fixture"]).read_text())
controls = json.loads(Path(p["controls"]).read_text())
witness = json.loads(Path(p["witness"]).read_text())
assert len(controls) == 2048 and len(source["states"]) == 5
bits = [i for i in range(9) if i != 5]


def code_of(state):
    mask = state["masks"][0]
    return sum(((mask >> bit) & 1) << j for j,bit in enumerate(bits))


positive = {"kind":"positive","z":fixture["left_reciprocal"],
            "w":witness["intermediate_reciprocal"],
            "state_ids":fixture["state_ids"],
            "code3":fixture["code_bit_words"][3],
            "code4":fixture["code_bit_words"][4]}
assert len(set(col for slot,sid in enumerate(positive["state_ids"])
               for col in source["states"][slot][sid]["columns"])) == 10

rng = random.Random(p["seed"])
rows = [positive]
for index,(w,z,i0,i1,i2,last_id) in enumerate(controls[:p["negative_count"]]):
    occupied = {col for slot,sid in enumerate((i0,i1,i2))
                for col in source["states"][slot][sid]["columns"]}
    occupied.update(source["states"][4][last_id]["columns"])
    choices = [sid for sid,state in enumerate(source["states"][3])
               if not occupied.intersection(state["columns"])]
    assert choices
    prior_id = choices[rng.randrange(len(choices))]
    ids = [i0,i1,i2,prior_id,last_id]
    assert len(set(col for slot,sid in enumerate(ids)
                   for col in source["states"][slot][sid]["columns"])) == 10
    rows.append({"kind":"reachable_control","control_index":index,
                 "z":z,"w":w,"state_ids":ids,
                 "code3":code_of(source["states"][3][prior_id]),
                 "code4":code_of(source["states"][4][last_id])})

(HERE / "panel.json").write_text(json.dumps(rows,sort_keys=True,indent=2)+"\n")
print(json.dumps({"status":"FROZEN_TWO_QUARTIC_FAMILY_PANEL",
                  "rows":len(rows),"protocol_sha256":sha(HERE / "panel_protocol.json"),
                  "panel_sha256":sha(HERE / "panel.json")},sort_keys=True))
