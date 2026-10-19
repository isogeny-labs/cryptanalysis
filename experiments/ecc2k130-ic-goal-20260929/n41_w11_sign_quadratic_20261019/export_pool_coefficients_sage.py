"""Export 16 determinant coefficients for each frozen root-choice tuple."""
import hashlib
import itertools
import json
import resource
import time
from pathlib import Path
from sage.all import EllipticCurve, GF, PolynomialRing, matrix

HERE=Path(__file__).resolve().parent
sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
cfg=json.loads((HERE/"coefficient_export_protocol.json").read_text())
assert cfg["status"]=="FROZEN_BEFORE_COEFFICIENT_EXPORT"
for label,source in cfg["sources"].items():
    assert sha(source["path"])==source["sha256"],label
panel=json.loads((HERE/"code_box_panel.json").read_text())
started=time.monotonic()
P=PolynomialRing(GF(2),"u")
u=P.gen()
F=GF(2**41,name="u",modulus=u**41+u**3+1)
E=EllipticCurve(F,[1,0,0,0,1])
dec=F.from_integer
enc=lambda value:sum(int(bit)<<i for i,bit in enumerate(value.polynomial().list()))
states=[{} for _ in range(5)]
for line in Path(cfg["sources"]["join_input"]["path"]).read_text().splitlines()[2:]:
    parts=line.split()
    if parts[0]=="S":
        slot,sid,code,branch,a,b,ca,cb,x,y=map(int,parts[1:])
        states[slot][sid]=E(dec(x),dec(y))
Q=E(*(dec(v) for v in panel["target_point"]))
minus_q=-Q
def D(points):
    rows=[]
    for point in points+[minus_q]:
        x,y=point[0],point[1]
        rows.append([1,x,y,x*x,x*y,x*x*x])
    return matrix(F,rows).det()
boxes=[]
for box in panel["boxes"]:
    coefficients=[]
    for root_mask in range(32):
        options=[[states[slot][sid] for sid in box["root_choices"][slot][root_mask>>slot&1]]
                 for slot in range(5)]
        values={}
        values[0]=D([options[j][0] for j in range(5)])
        for j in range(5):
            values[1<<j]=D([options[slot][int(slot==j)] for slot in range(5)])
        for i,j in itertools.combinations(range(5),2):
            values[(1<<i)|(1<<j)]=D([options[slot][int(slot==i or slot==j)]
                                    for slot in range(5)])
        c0=values[0]
        linear=[values[1<<j]+c0 for j in range(5)]
        quadratic=[values[(1<<i)|(1<<j)]+values[1<<i]+values[1<<j]+c0
                   for i,j in itertools.combinations(range(5),2)]
        coefficients.append([enc(v) for v in [c0]+linear+quadratic])
    boxes.append(coefficients)
result={"status":"COMPLETE_COEFFICIENT_EXPORT","candidate_id":None,
        "curve_id":cfg["curve_id"],"box_count":len(boxes),
        "root_tuples_per_box":32,"coefficients_per_tuple":16,
        "boxes":boxes,"wall_seconds":time.monotonic()-started,
        "peak_rss_raw":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "protocol_sha256":sha(HERE/"coefficient_export_protocol.json"),
        "script_sha256":sha(Path(__file__))}
(HERE/"pool_coefficients.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
print(json.dumps({"status":result["status"],"box_count":len(boxes),
                  "wall_seconds":result["wall_seconds"]},sort_keys=True),flush=True)
