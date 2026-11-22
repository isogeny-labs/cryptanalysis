"""Independently rebuild selected source states and all tested group sums."""
import hashlib
import itertools
import json
import resource
import time
from pathlib import Path
from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
cfg = json.loads((HERE/"audit_protocol.json").read_text())
assert cfg["status"] == "FROZEN_BEFORE_SOURCE_AND_GROUP_AUDIT"
for label,source in cfg["sources"].items():
    assert sha(source["path"]) == source["sha256"],label
panel=json.loads((HERE/"panel.json").read_text())
boxes=json.loads((HERE/"code_box_panel.json").read_text())
screen=json.loads((HERE/"result.json").read_text())
box_result=json.loads((HERE/"code_box_result.json").read_text())
started=time.monotonic()
P=PolynomialRing(GF(2),"u")
u=P.gen()
F=GF(2**41,name="u",modulus=u**41+u**3+1)
E=EllipticCurve(F,[1,0,0,0,1])
O=E(0)
dec=F.from_integer
enc=lambda value:sum(int(bit)<<i for i,bit in enumerate(value.polynomial().list()))
seed=dec(112)
bits=[0,1,2,3,4,6,7,8,9,10]
rotations=[0,0,12,12,24]
target=E(*(dec(v) for v in panel["target_point"]))
assert panel["target_point"]==boxes["target_point"]
input_rows={}
for line in Path(cfg["sources"]["join_input"]["path"]).read_text().splitlines()[2:]:
    words=line.split()
    if words[0]!="S":
        continue
    slot,sid,code,branch,a,b,ca,cb,x,y=map(int,words[1:])
    input_rows[(slot,sid)]=(code,branch,a,b,ca,cb,x,y)
needed=set()
for row in panel["rows"]:
    for slot,pair in enumerate(row["sign_state_ids"]):
        needed.update((slot,sid) for sid in pair)
for box in boxes["boxes"]:
    for slot,choices in enumerate(box["root_choices"]):
        for pair in choices:
            needed.update((slot,sid) for sid in pair)
assert len(needed)<=510
code_cache={}
points={}
for slot,sid in sorted(needed):
    code,branch,a_int,b_int,ca,cb,x_int,y_int=input_rows[(slot,sid)]
    if code not in code_cache:
        a=sum((dec(1<<(bit+1)) for j,bit in enumerate(bits) if code>>j&1),F.zero())
        b=a+seed
        assert a and b and a.trace()==0 and b.trace()==0
        assert (1/a).trace()==0 and (1/b).trace()==0
        def source(mask):
            h=F.zero()
            power=mask
            for _ in range(21):
                h+=power
                power=power**4
            assert h*h+h==mask
            x=F.one()+1/h
            options=E.lift_x(x,all=True)
            assert len(options)==2
            return options
        left,right=source(a),source(b)
        code_cache[code]=(enc(a),enc(b),left,right)
    a_saved,b_saved,left,right=code_cache[code]
    assert (a_int,b_int)==(a_saved,b_saved)
    pa,pb=left[branch//2],right[branch%2]
    pair=pa+pb
    rotated=E(pair[0]**(1<<rotations[slot]),pair[1]**(1<<rotations[slot]))
    assert (enc(rotated[0]),enc(rotated[1]))==(x_int,y_int)
    points[(slot,sid)]=rotated
positive_rows=[]
for row,produced in zip(panel["rows"],screen["rows"]):
    hits=[]
    for mask in range(32):
        selected=[points[(slot,row["sign_state_ids"][slot][mask>>slot&1])]
                  for slot in range(5)]
        if sum(selected,O)==target:
            hits.append(mask)
    assert hits==produced["matched_signs"]
    positive_rows.append(hits)
box_hits=[]
for box,produced in zip(boxes["boxes"],box_result["rows"]):
    hits=[]
    for root_mask,sign_mask in itertools.product(range(32),repeat=2):
        selected=[points[(slot,box["root_choices"][slot][root_mask>>slot&1][sign_mask>>slot&1])]
                  for slot in range(5)]
        if sum(selected,O)==target:
            hits.append([root_mask,sign_mask])
    assert hits==produced["group_hits"]
    box_hits.append(hits)
assert positive_rows[0]==[30] and box_hits[0]==[[0,30]]
assert all(not hits for hits in positive_rows[1:])
assert all(not hits for hits in box_hits[1:])
result={"status":"PASS_INDEPENDENT_SOURCE_AND_GROUP_AUDIT","candidate_id":None,
        "curve_id":cfg["curve_id"],"source_states_rebuilt":len(needed),
        "distinct_source_codes_rebuilt":len(code_cache),
        "sign_assignments_replayed":33*32,
        "code_box_assignments_replayed":9*1024,
        "positive_sign_hits":positive_rows[0],
        "positive_box_hits":box_hits[0],
        "other_hits":0,
        "wall_seconds":time.monotonic()-started,
        "peak_rss_raw":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "protocol_sha256":sha(HERE/"audit_protocol.json"),
        "script_sha256":sha(Path(__file__))}
(HERE/"audit_result.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
print(json.dumps({key:result[key] for key in ("status","source_states_rebuilt",
                                            "sign_assignments_replayed",
                                            "code_box_assignments_replayed",
                                            "wall_seconds")},sort_keys=True),flush=True)
