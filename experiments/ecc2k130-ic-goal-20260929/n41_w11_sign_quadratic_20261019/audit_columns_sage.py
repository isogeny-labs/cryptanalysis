"""Independent signed-Frobenius column audit for every selected source code."""
import hashlib
import json
import resource
import time
from pathlib import Path
from sage.all import GF, PolynomialRing

HERE=Path(__file__).resolve().parent
sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
cfg=json.loads((HERE/"columns_protocol.json").read_text())
assert cfg["status"]=="FROZEN_BEFORE_COLUMN_AUDIT"
for label,source in cfg["sources"].items():
    assert sha(source["path"])==source["sha256"],label
panel=json.loads((HERE/"panel.json").read_text())
boxes=json.loads((HERE/"code_box_panel.json").read_text())
started=time.monotonic()
P=PolynomialRing(GF(2),"u")
u=P.gen()
F=GF(2**41,name="u",modulus=u**41+u**3+1)
dec=F.from_integer
enc=lambda value:sum(int(bit)<<i for i,bit in enumerate(value.polynomial().list()))
bits=[0,1,2,3,4,6,7,8,9,10]
seed=dec(112)
rows={}
for line in Path(cfg["sources"]["join_input"]["path"]).read_text().splitlines()[2:]:
    cols=line.split()
    if cols[0]!="S":
        continue
    slot,sid,code,branch,a,b,ca,cb,x,y=map(int,cols[1:])
    rows[(slot,sid)]=(code,ca,cb)
needed=set()
for row in panel["rows"]:
    for slot,pair in enumerate(row["sign_state_ids"]):
        needed.update((slot,sid) for sid in pair)
for box in boxes["boxes"]:
    for slot,choices in enumerate(box["root_choices"]):
        for pair in choices:
            needed.update((slot,sid) for sid in pair)
def halftrace(value):
    out=F.zero()
    power=value
    for _ in range(21):
        out+=power
        power=power**4
    assert out*out+out==value
    return out
def column(mask):
    x=F.one()+1/halftrace(mask)
    conjugates=[]
    for _ in range(41):
        conjugates.append(enc(x))
        x=x*x
    return min(conjugates)
cache={}
for slot,sid in sorted(needed):
    code,ca,cb=rows[(slot,sid)]
    if code not in cache:
        a=sum((dec(1<<(bit+1)) for j,bit in enumerate(bits) if code>>j&1),F.zero())
        b=a+seed
        cache[code]=(column(a),column(b))
    assert (ca,cb)==cache[code]
for row in panel["rows"]:
    computed=[v for slot,pair in enumerate(row["sign_state_ids"])
              for v in cache[rows[(slot,pair[0])][0]]]
    assert computed==row["columns"] and len(set(computed))==10
for box in boxes["boxes"]:
    computed=[v for slot,choices in enumerate(box["root_choices"])
              for pair in choices for v in cache[rows[(slot,pair[0])][0]]]
    assert len(computed)==20 and len(set(computed))==20
result={"status":"PASS_INDEPENDENT_COLUMN_AUDIT","candidate_id":None,
        "curve_id":cfg["curve_id"],"source_states_checked":len(needed),
        "source_codes_checked":len(cache),"sign_families_checked":len(panel["rows"]),
        "code_boxes_checked":len(boxes["boxes"]),
        "wall_seconds":time.monotonic()-started,
        "peak_rss_raw":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "protocol_sha256":sha(HERE/"columns_protocol.json"),
        "script_sha256":sha(Path(__file__))}
(HERE/"columns_result.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
print(json.dumps(result,sort_keys=True),flush=True)
