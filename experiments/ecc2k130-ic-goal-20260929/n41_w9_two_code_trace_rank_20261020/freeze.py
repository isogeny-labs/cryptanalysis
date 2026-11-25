"""Freeze source-valid W9 code pairs before output and rank computation."""
import hashlib
import json
import random
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
states_path=ROOT/"n41_n131_w29_rotation_alignment_20261017/aligned_states.json"
audit_path=ROOT/"n41_n131_w29_rotation_alignment_20261017/n41_audit_result.json"
source=json.loads(states_path.read_text())
free_bits=[0,1,2,3,4,6,7,8]


def code(state):
    mask=state["masks"][0]
    return sum(((mask>>bit)&1)<<j for j,bit in enumerate(free_bits))


by_code=[]
for slot in (0,1):
    groups={}
    for index,state in enumerate(source["states"][slot]):
        groups.setdefault(code(state),[]).append((index,state))
    assert len(groups)==71 and all(len(v)==4 for v in groups.values())
    for group in groups.values():
        assert all(tuple(v[1]["columns"])==tuple(group[0][1]["columns"]) for v in group)
    by_code.append(groups)
eligible=[]
for left in sorted(by_code[0]):
    for right in sorted(by_code[1]):
        if left>=right:
            continue
        columns=by_code[0][left][0][1]["columns"]+by_code[1][right][0][1]["columns"]
        if len(set(columns))==4:
            eligible.append([left,right])
positive=[code(source["states"][0][105]),code(source["states"][1][244])]
assert positive==[93,228] and positive in eligible
seed=0x20261020
others=[pair for pair in eligible if pair!=positive]
random.Random(seed).shuffle(others)
selected=[positive]+others
families={"status":"FROZEN_BEFORE_N41_TWO_CODE_OUTPUT_EXPORT",
          "candidate_id":None,"curve_id":source["curve_id"],
          "code_bit_order":free_bits,"positive_pair":positive,
          "positive_state_ids":[105,244,66,47,111],
          "seed":seed,"eligible_ordered_pairs":len(eligible),
          "selected_pairs":selected,
          "states_sha256":hashlib.sha256(states_path.read_bytes()).hexdigest()}
family_path=HERE/"families.json"
assert not family_path.exists()
family_path.write_text(json.dumps(families,sort_keys=True,indent=2)+"\n")
paths=[HERE/"run_sage.py",family_path,states_path,audit_path,HERE/"sage_runtime_info.json"]
protocol={"status":"FROZEN_BEFORE_N41_TWO_CODE_OUTPUT_EXPORT",
          "candidate_id":None,"curve_id":source["curve_id"],
          "states":str(states_path),"audit":str(audit_path),
          "families":str(family_path),"wall_cap_seconds":120,
          "worker_count":1,"sources":{str(path):hashlib.sha256(path.read_bytes()).hexdigest() for path in paths},
          "test":"All eligible ordered two-code families in seeded order, including unpinned public-relation code pair first; all 16 signed partial sums in the reciprocal chart"}
out=HERE/"export_protocol.json"
assert not out.exists()
out.write_text(json.dumps(protocol,sort_keys=True,indent=2)+"\n")
print(len(eligible),positive,hashlib.sha256(out.read_bytes()).hexdigest())
