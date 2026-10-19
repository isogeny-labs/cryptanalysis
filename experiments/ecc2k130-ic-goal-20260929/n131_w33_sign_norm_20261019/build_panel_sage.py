"""Freeze exact W33 five-pair sign boxes on constructed and public N131 points."""
import hashlib
import itertools
import json
import random
import resource
import time
from pathlib import Path
from sage.all import EllipticCurve, GF, PolynomialRing

HERE=Path(__file__).resolve().parent
sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
cfg=json.loads((HERE/"panel_protocol.json").read_text())
assert cfg["status"]=="FROZEN_BEFORE_N131_SIGN_PANEL"
for label,source in cfg["sources"].items():
    assert sha(source["path"])==source["sha256"],label
gate=json.loads(Path(cfg["sources"]["n41_gate"]["path"]).read_text())
assert gate["status"]=="PASS_N41_NONLINEAR_SIGN_NORM_GATE"
control=json.loads(Path(cfg["sources"]["positive_control"]["path"]).read_text())
public=json.loads(Path(cfg["sources"]["public_build"]["path"]).read_text())
assert control["curve_id"]==public["curve_id"]==cfg["curve_id"]
assert control["rotations"]==cfg["rotations"]
assert public["target_point"]==cfg["public_point"]
started=time.monotonic()
P=PolynomialRing(GF(2),"u")
u=P.gen()
F=GF(2**131,name="u",modulus=u**131+u**13+u**2+u+1)
E=EllipticCurve(F,[1,0,0,0,1])
dec=F.from_integer
enc=lambda value:sum(int(bit)<<i for i,bit in enumerate(value.polynomial().list()))
seed_mask=898618
bits=[i for i in range(33) if i!=seed_mask.bit_length()-1]
assert len(bits)==32
source_seed=dec(seed_mask<<1)
O=E(0)
def halftrace(value):
    out=F.zero()
    term=value
    for _ in range(66):
        out+=term
        term=term**4
    assert out*out+out==value
    return out
def source_points(mask):
    h=halftrace(mask)
    x=F.one()+1/h
    points=E.lift_x(x,all=True)
    assert len(points)==2
    return points
def column(mask):
    x=F.one()+1/halftrace(mask)
    values=[]
    for _ in range(131):
        values.append(enc(x))
        x=x*x
    return min(values)
def source_mask(code):
    return sum(1<<bits[j] for j in range(32) if code>>j&1)
def build_code(code):
    mask=source_mask(code)
    companion=mask^seed_mask
    if not mask or not companion:
        return None
    a,b=dec(mask<<1),dec(companion<<1)
    if a.trace()!=0 or b.trace()!=0 or (1/a).trace()!=0 or (1/b).trace()!=0:
        return None
    left,right=source_points(a),source_points(b)
    groups={}
    for pa,pb in itertools.product(left,right):
        summed=pa+pb
        if summed==O:
            return None
        groups.setdefault(enc(summed[0]),[]).append(summed)
    if len(groups)!=2 or any(len(points)!=2 for points in groups.values()):
        return None
    root_pairs=[]
    for x in sorted(groups):
        points=sorted(groups[x],key=lambda point:enc(point[1]))
        assert points[0]==-points[1]
        root_pairs.append([[enc(point[0]),enc(point[1])] for point in points])
    return {"code":code,"masks":[mask,companion],
            "columns":[column(a),column(b)],
            "root_pairs":root_pairs,
            "first_first_pair":[enc((left[0]+right[0])[0]),enc((left[0]+right[0])[1])]}
def rotated_choice(info,root,slot):
    shift=1<<cfg["rotations"][slot]
    points=[]
    for x_int,y_int in info["root_pairs"][root]:
        point=E(dec(x_int),dec(y_int))
        rotated=E(point[0]**shift,point[1]**shift)
        points.append([enc(rotated[0]),enc(rotated[1])])
    assert points[0][0]==points[1][0]
    return {"code":info["code"],"masks":info["masks"],
            "columns":info["columns"],"root":root,"signed_points":points}
def allowed(choice,used_cols,used_x,target_x):
    x=choice["signed_points"][0][0]
    return (x!=target_x and x not in used_x and
            all(c not in used_cols for c in choice["columns"]))
rng=random.Random(cfg["selection_seed"])
cache={}
positive_codes=cfg["positive_codes"]
for code in positive_codes:
    info=build_code(code)
    assert info is not None
    cache[code]=info
positive_first=[]
used_cols=set()
used_x=set()
for slot,code in enumerate(positive_codes):
    info=cache[code]
    desired=E(*(dec(v) for v in info["first_first_pair"]))
    shift=1<<cfg["rotations"][slot]
    desired=E(desired[0]**shift,desired[1]**shift)
    root=next(j for j in range(2)
              if any(E(*(dec(v) for v in xy))==desired
                     for xy in rotated_choice(info,j,slot)["signed_points"]))
    choice=rotated_choice(info,root,slot)
    assert allowed(choice,used_cols,used_x,control["target_raw_point"][0])
    positive_first.append(choice)
    used_cols.update(choice["columns"])
    used_x.add(choice["signed_points"][0][0])
assert len(used_cols)==10 and len(used_x)==5

attempts=0
while len(cache)<cfg["candidate_codes"]:
    if attempts>=cfg["candidate_attempt_cap"]:
        raise RuntimeError("candidate source selection cap")
    attempts+=1
    code=rng.randrange(1,1<<32)
    if code in cache:
        continue
    info=build_code(code)
    if info is not None:
        cache[code]=info
    if time.monotonic()-started>=cfg["wall_cap_seconds"]:
        raise TimeoutError("panel construction wall cap")
assert len(cache)==cfg["candidate_codes"]
candidates=[info for code,info in sorted(cache.items()) if code not in positive_codes]
def select_extra(slot,used_cols,used_x,target_x,exclude_codes):
    order=list(candidates)
    rng.shuffle(order)
    for info in order:
        if info["code"] in exclude_codes:
            continue
        for root in rng.sample(range(2),2):
            choice=rotated_choice(info,root,slot)
            if allowed(choice,used_cols,used_x,target_x):
                return choice
    raise RuntimeError("no disjoint candidate")

positive_choices=[]
used_cols=set(c for row in positive_first for c in row["columns"])
used_x=set(row["signed_points"][0][0] for row in positive_first)
used_codes=set(positive_codes)
for slot in range(5):
    choice=select_extra(slot,used_cols,used_x,control["target_raw_point"][0],used_codes)
    positive_choices.append([positive_first[slot],choice])
    used_cols.update(choice["columns"])
    used_x.add(choice["signed_points"][0][0])
    used_codes.add(choice["code"])
assert len(used_cols)==20 and len(used_x)==10
positive_target=E(*(dec(v) for v in control["target_raw_point"]))
positive_signs=[]
for sign_mask in range(32):
    selected=[positive_choices[slot][0]["signed_points"][sign_mask>>slot&1]
              for slot in range(5)]
    points=[E(*(dec(v) for v in xy)) for xy in selected]
    if sum(points,O)==positive_target:
        positive_signs.append(sign_mask)
assert len(positive_signs)==1
assert control["distinct_folded_columns"]==10
boxes=[{"kind":"constructed_control","target_point":control["target_raw_point"],
        "choices":positive_choices,"known_positive":[0,positive_signs[0]]}]
for box_index in range(cfg["public_boxes"]):
    choices=[[],[],[],[],[]]
    used_cols=set()
    used_x=set()
    used_codes=set()
    for slot in range(5):
        for _ in range(2):
            choice=select_extra(slot,used_cols,used_x,cfg["public_point"][0],used_codes)
            choices[slot].append(choice)
            used_cols.update(choice["columns"])
            used_x.add(choice["signed_points"][0][0])
            used_codes.add(choice["code"])
    assert len(used_cols)==20 and len(used_x)==10
    boxes.append({"kind":"frozen_public_raw_point",
                  "target_point":cfg["public_point"],"choices":choices,
                  "known_positive":None})
result={"status":"FROZEN_N131_SIGN_PANEL","candidate_id":None,
        "curve_id":cfg["curve_id"],"field_degree":131,
        "source_bits":32,"seed_mask":seed_mask,
        "rotations":cfg["rotations"],"candidate_codes_built":len(cache),
        "candidate_attempts":attempts,"boxes":boxes,
        "wall_seconds":time.monotonic()-started,
        "peak_rss_raw":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "protocol_sha256":sha(HERE/"panel_protocol.json"),
        "script_sha256":sha(Path(__file__))}
(HERE/"panel.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
print(json.dumps({"status":result["status"],"candidate_codes_built":len(cache),
                  "candidate_attempts":attempts,"boxes":len(boxes),
                  "positive_sign_mask":positive_signs[0],
                  "wall_seconds":result["wall_seconds"]},sort_keys=True),flush=True)
