"""Independently reconstruct W33 source points, replay all sums, and check sign norms."""
import hashlib
import itertools
import json
import resource
import time
from pathlib import Path
from sage.all import EllipticCurve, GF, PolynomialRing

HERE=Path(__file__).resolve().parent
sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
cfg=json.loads((HERE/"audit_protocol.json").read_text())
assert cfg["status"]=="FROZEN_BEFORE_N131_SIGN_NORM_AUDIT"
for label,source in cfg["sources"].items():
    assert sha(source["path"])==source["sha256"],label
panel=json.loads((HERE/"panel.json").read_text())
positive=json.loads((HERE/"positive_result.json").read_text())
ordinary=json.loads((HERE/"public_result.json").read_text())
coeff_positive=json.loads((HERE/"positive_coefficients.json").read_text())
coeff_public=json.loads((HERE/"public_coefficients.json").read_text())
assert panel["status"]=="FROZEN_N131_SIGN_PANEL"
assert positive["status"]==ordinary["status"]=="COMPLETE_N131_SIGN_NORM"
started=time.monotonic()
P=PolynomialRing(GF(2),"u")
u=P.gen()
F=GF(2**131,name="u",modulus=u**131+u**13+u**2+u+1)
E=EllipticCurve(F,[1,0,0,0,1])
dec=F.from_integer
enc=lambda value:sum(int(bit)<<i for i,bit in enumerate(value.polynomial().list()))
O=E(0)
r=680564733841876926932320129493409985129
seed_mask=898618
seed=dec(seed_mask<<1)
bits=[i for i in range(33) if i!=seed_mask.bit_length()-1]
assert len(bits)==32
rotations=[0,18,36,54,72]
def halftrace(value):
    out=F.zero()
    term=value
    for _ in range(66):
        out+=term
        term=term**4
    assert out*out+out==value
    return out
def source(mask):
    x=F.one()+1/halftrace(mask)
    points=E.lift_x(x,all=True)
    assert len(points)==2
    return points
def column(mask):
    x=F.one()+1/halftrace(mask)
    candidates=[]
    for _ in range(131):
        candidates.append(enc(x))
        x=x*x
    return min(candidates)
cache={}
for box in panel["boxes"]:
    for slot in range(5):
        for choice in box["choices"][slot]:
            code=choice["code"]
            if code in cache:
                continue
            mask=sum(1<<bits[j] for j in range(32) if code>>j&1)
            companion=mask^seed_mask
            a,b=dec(mask<<1),dec(companion<<1)
            assert mask and companion and a+b==seed
            assert a.trace()==0 and b.trace()==0
            assert (1/a).trace()==0 and (1/b).trace()==0
            left,right=source(a),source(b)
            pair_points=[p+q for p,q in itertools.product(left,right)]
            assert all(point!=O for point in pair_points)
            assert all(r*(4*point)==O for point in left+right)
            cache[code]={"masks":[mask,companion],
                         "columns":[column(a),column(b)],
                         "pair_points":pair_points}
reconstructed={}
for box_index,box in enumerate(panel["boxes"]):
    target=E(*(dec(v) for v in box["target_point"]))
    columns=[]
    xcoords=[box["target_point"][0]]
    for slot in range(5):
        for choice_index,choice in enumerate(box["choices"][slot]):
            info=cache[choice["code"]]
            assert choice["masks"]==info["masks"]
            assert choice["columns"]==info["columns"]
            columns.extend(info["columns"])
            shift=1<<rotations[slot]
            options=[]
            for point in info["pair_points"]:
                rotated=E(point[0]**shift,point[1]**shift)
                if enc(rotated[0])==choice["signed_points"][0][0]:
                    options.append(rotated)
            assert len(options)==2 and options[0]==-options[1]
            assert {tuple((enc(point[0]),enc(point[1]))) for point in options}=={
                tuple(xy) for xy in choice["signed_points"]}
            for sign_index,xy in enumerate(choice["signed_points"]):
                point=next(point for point in options
                           if (enc(point[0]),enc(point[1]))==tuple(xy))
                reconstructed[(box_index,slot,choice_index,sign_index)]=point
            xcoords.append(choice["signed_points"][0][0])
    assert len(set(columns))==20 and len(set(xcoords))==11
    assert target!=O
all_rows=positive["rows"]+ordinary["rows"]
all_coeff=coeff_positive["boxes"]+coeff_public["boxes"]
assert len(all_rows)==len(all_coeff)==len(panel["boxes"])==9
pairs=list(itertools.combinations(range(5),2))
replayed_assignments=norms_checked=mask_values_checked=0
for box_index,box in enumerate(panel["boxes"]):
    target=E(*(dec(v) for v in box["target_point"]))
    row=all_rows[box_index]
    coeff=all_coeff[box_index]
    assert row["box_index"]==coeff["box_index"]==box_index
    hits=[]
    for root_mask,source_row in enumerate(coeff["rows"]):
        assert len(source_row)==16
        product=F.one()
        for sign_mask in range(32):
            selected=[reconstructed[(box_index,slot,root_mask>>slot&1,sign_mask>>slot&1)]
                      for slot in range(5)]
            hit=sum(selected,O)==target
            if hit:
                hits.append([root_mask,sign_mask])
            value=dec(source_row[0])
            for j in range(5):
                if sign_mask>>j&1:
                    value+=dec(source_row[1+j])
            for index,(i,j) in enumerate(pairs):
                if sign_mask>>i&1 and sign_mask>>j&1:
                    value+=dec(source_row[6+index])
            assert (value==0)==hit
            product*=value
            replayed_assignments+=1
        assert enc(product)==row["norms"][root_mask]
        norms_checked+=1
        if row["trace_mask"] is not None:
            assert (row["trace_mask"]&enc(product)).bit_count()%2==1
            mask_values_checked+=1
    assert hits==row["group_hits"]
    if box_index==0:
        assert box["known_positive"] in hits
    else:
        assert not hits
assert replayed_assignments==9*1024
assert norms_checked==9*32
assert mask_values_checked==8*32
result={"status":"PASS_INDEPENDENT_N131_SIGN_NORM_AUDIT","candidate_id":None,
        "curve_id":cfg["curve_id"],"source_codes_rebuilt":len(cache),
        "signed_states_rebuilt":len(reconstructed),
        "assignments_replayed":replayed_assignments,
        "norm_products_checked":norms_checked,
        "trace_values_checked":mask_values_checked,
        "public_boxes_rejected":8,
        "wall_seconds":time.monotonic()-started,
        "peak_rss_raw":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "protocol_sha256":sha(HERE/"audit_protocol.json"),
        "script_sha256":sha(Path(__file__))}
(HERE/"audit_result.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
print(json.dumps({key:result[key] for key in ("status","source_codes_rebuilt",
                                            "assignments_replayed",
                                            "norm_products_checked",
                                            "wall_seconds")},sort_keys=True),flush=True)
