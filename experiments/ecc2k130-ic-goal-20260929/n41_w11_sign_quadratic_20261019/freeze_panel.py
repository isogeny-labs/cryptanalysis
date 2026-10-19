"""Freeze real-source five-pair sign families before determinant evaluation."""
import hashlib
import json
import random
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
cfg = json.loads((HERE / "protocol.json").read_text())
assert cfg["status"] == "FROZEN_BEFORE_SIGN_PANEL"
for label, source in cfg["sources"].items():
    assert sha(source["path"]) == source["sha256"], label
lines = Path(cfg["sources"]["join_input"]["path"]).read_text().splitlines()
assert lines[0] == "W11FIVE 5 1124 1"
target = [int(v) for v in lines[1].split()[2:]]
states = defaultdict(dict)
root_groups = defaultdict(list)
for line in lines[2:]:
    cols = line.split()
    if cols[0] != "S":
        continue
    values = list(map(int, cols[1:]))
    slot, sid, code, branch, mask_a, mask_b, col_a, col_b, x, y = values
    state = {"slot": slot, "sid": sid, "code": code, "branch": branch,
             "columns": [col_a, col_b], "point": [x, y]}
    states[slot][sid] = state
    root_groups[(slot, code, x)].append(sid)
assert all(len(states[slot]) == 1124 for slot in range(5))
assert all(len(ids) == 2 for ids in root_groups.values())
canonical = {slot: sorted(set(tuple(sorted(ids)) for (s, _, _), ids in root_groups.items()
                              if s == slot)) for slot in range(5)}
assert all(len(canonical[slot]) == 562 for slot in range(5))


def family(ids):
    paired = []
    for slot, sid in enumerate(ids):
        state = states[slot][sid]
        paired.append(sorted(root_groups[(slot, state["code"], state["point"][0])]))
    column_ids = [column for slot, pair in enumerate(paired)
                  for column in states[slot][pair[0]]["columns"]]
    xcoords = [states[slot][pair[0]]["point"][0] for slot, pair in enumerate(paired)]
    assert len(column_ids) == 10 and len(xcoords) == 5
    return {"sign_state_ids": paired, "columns": column_ids,
            "x_coordinates": xcoords,
            "chosen_codes": [states[slot][pair[0]]["code"] for slot, pair in enumerate(paired)]}


query = json.loads(Path(cfg["sources"]["query_result"]["path"]).read_text())
positive = family(query["hit"]["state_ids"])
assert len(set(positive["columns"])) == 10
assert len(set(positive["x_coordinates"]+[target[0]])) == 6
positive["kind"] = "independently_replayed_public_relation"
rng = random.Random(cfg["random_seed"])
rows = [positive]
seen = {tuple(tuple(pair) for pair in positive["sign_state_ids"])}
while len(rows) < cfg["random_families"]+1:
    sampled = [rng.choice(canonical[slot])[0] for slot in range(5)]
    row = family(sampled)
    if len(set(row["columns"])) != 10 or len(set(row["x_coordinates"]+[target[0]])) != 6:
        continue
    key = tuple(tuple(pair) for pair in row["sign_state_ids"])
    if key in seen:
        continue
    seen.add(key)
    row["kind"] = "frozen_random_source_family"
    rows.append(row)

out = {"status": "FROZEN_SIGN_PANEL", "candidate_id": None,
       "curve_id": cfg["curve_id"], "target_point": target,
       "rows": rows, "protocol_sha256": sha(HERE/"protocol.json"),
       "script_sha256": sha(Path(__file__))}
(HERE/"panel.json").write_text(json.dumps(out, indent=2, sort_keys=True)+"\n")
print(json.dumps({"status": out["status"], "families": len(rows),
                  "positive_codes": positive["chosen_codes"]}, sort_keys=True))
