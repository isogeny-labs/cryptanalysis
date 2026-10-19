"""Target-conditioned N131 five-pair sign norm over frozen W33 code boxes."""
import hashlib
import itertools
import json
import resource
import sys
import time
from pathlib import Path
from sage.all import EllipticCurve, GF, PolynomialRing, matrix, vector

HERE=Path(__file__).resolve().parent
case=sys.argv[1]
assert case in ("positive","public")
sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
cfg=json.loads((HERE/("run_protocol_"+case+".json")).read_text())
assert cfg["status"]=="FROZEN_BEFORE_N131_SIGN_NORM_"+case.upper()
for label,source in cfg["sources"].items():
    assert sha(source["path"])==source["sha256"],label
panel=json.loads((HERE/"panel.json").read_text())
assert panel["status"]=="FROZEN_N131_SIGN_PANEL"
if case=="public":
    gate=json.loads((HERE/"positive_gate.json").read_text())
    assert gate["status"]=="PASS_N131_SIGN_NORM_POSITIVE_GATE"
    assert sha(HERE/"positive_gate.json")==cfg["positive_gate_sha256"]
selected=[0] if case=="positive" else list(range(1,9))
assert selected==cfg["box_indices"]
started=time.monotonic()
P=PolynomialRing(GF(2),"u")
u=P.gen()
F=GF(2**131,name="u",modulus=u**131+u**13+u**2+u+1)
E=EllipticCurve(F,[1,0,0,0,1])
dec=F.from_integer
enc=lambda value:sum(int(bit)<<i for i,bit in enumerate(value.polynomial().list()))
O=E(0)
pairs=list(itertools.combinations(range(5),2))
def determinant(points,target):
    rows=[]
    for point in points+[-target]:
        x,y=point[0],point[1]
        rows.append([F.one(),x,y,x*x,x*y,x*x*x])
    return matrix(F,rows).det()
def add_basis(basis,value):
    while value:
        pivot=(value&-value).bit_length()-1
        if pivot in basis:
            value^=basis[pivot]
        else:
            basis[pivot]=value
            return True
    return False
def mobius(values):
    out=list(values)
    for bit in range(5):
        for i in range(32):
            if i>>bit&1:
                out[i]^=out[i^(1<<bit)]
    return out
results=[]
export=[]
status="COMPLETE_N131_SIGN_NORM"
for box_index in selected:
    if time.monotonic()-started>=cfg["wall_cap_seconds"]:
        status="WALL_CAP_PARTIAL"
        break
    box=panel["boxes"][box_index]
    target=E(*(dec(v) for v in box["target_point"]))
    choices=[]
    columns=[]
    xcoords=[box["target_point"][0]]
    for slot in range(5):
        slot_choices=[]
        for choice in box["choices"][slot]:
            signed=[E(*(dec(v) for v in xy)) for xy in choice["signed_points"]]
            assert signed[0]==-signed[1] and signed[0][0]==signed[1][0]
            slot_choices.append(signed)
            columns.extend(choice["columns"])
            xcoords.append(choice["signed_points"][0][0])
        choices.append(slot_choices)
    assert len(columns)==20 and len(set(columns))==20
    assert len(xcoords)==11 and len(set(xcoords))==11
    coeff_rows=[]
    norms=[]
    hits=[]
    coefficient_seconds=direct_audit_seconds=norm_seconds=0.0
    for root_mask in range(32):
        sign_options=[choices[slot][root_mask>>slot&1] for slot in range(5)]
        t0=time.monotonic()
        d0=determinant([sign_options[j][0] for j in range(5)],target)
        linear=[determinant([sign_options[slot][int(slot==j)] for slot in range(5)],target)+d0
                for j in range(5)]
        quadratic=[]
        for i,j in pairs:
            value=determinant([sign_options[slot][int(slot==i or slot==j)]
                               for slot in range(5)],target)
            quadratic.append(value+d0+linear[i]+linear[j])
        row=[d0]+linear+quadratic
        coeff_rows.append([enc(v) for v in row])
        coefficient_seconds+=time.monotonic()-t0
        t0=time.monotonic()
        norm=F.one()
        for sign_mask in range(32):
            predicted=d0
            for j in range(5):
                if sign_mask>>j&1:
                    predicted+=linear[j]
            for index,(i,j) in enumerate(pairs):
                if sign_mask>>i&1 and sign_mask>>j&1:
                    predicted+=quadratic[index]
            norm*=predicted
        norms.append(norm)
        norm_seconds+=time.monotonic()-t0
        t0=time.monotonic()
        for sign_mask in range(32):
            points=[sign_options[j][sign_mask>>j&1] for j in range(5)]
            actual=determinant(points,target)
            predicted=d0
            for j in range(5):
                if sign_mask>>j&1:
                    predicted+=linear[j]
            for index,(i,j) in enumerate(pairs):
                if sign_mask>>i&1 and sign_mask>>j&1:
                    predicted+=quadratic[index]
            assert actual==predicted,(box_index,root_mask,sign_mask)
            hit=sum(points,O)==target
            assert (actual==0)==hit,(box_index,root_mask,sign_mask)
            if hit:
                hits.append([root_mask,sign_mask])
        direct_audit_seconds+=time.monotonic()-t0
    assert len(norms)==32
    assert sorted([i for i,v in enumerate(norms) if v==0])==sorted({r for r,s in hits})
    int_norms=[enc(v) for v in norms]
    rank_basis={}
    for value in int_norms:
        add_basis(rank_basis,value)
    A=matrix(GF(2),32,131,lambda row,col:(int_norms[row]>>col)&1)
    rhs=vector(GF(2),[1]*32)
    consistent=A.augment(rhs.column()).rank()==A.rank()
    mask=None
    anf=None
    if consistent:
        solution=A.solve_right(rhs)
        mask=sum(int(solution[j])<<j for j in range(131))
        trace_values=[(value&mask).bit_count()%2 for value in int_norms]
        assert trace_values==[1]*32
        anf=mobius(trace_values)
        assert anf==[1]+[0]*31
    if case=="positive":
        assert box["known_positive"] in hits
        assert mask is None
    results.append({"box_index":box_index,"kind":box["kind"],
                    "target_point":box["target_point"],
                    "group_hits":hits,"norm_rank":len(rank_basis),
                    "trace_mask":mask,"trace_anf":anf,
                    "norms":int_norms,
                    "coefficient_seconds":coefficient_seconds,
                    "norm_seconds":norm_seconds,
                    "direct_audit_seconds":direct_audit_seconds})
    export.append({"box_index":box_index,"rows":coeff_rows})
    if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss>cfg["rss_cap_bytes"]:
        status="RSS_CAP_PARTIAL"
        break
coeff_output={"status":status,"candidate_id":None,"curve_id":cfg["curve_id"],
              "case":case,"boxes":export,"protocol_sha256":sha(HERE/("run_protocol_"+case+".json")),
              "script_sha256":sha(Path(__file__))}
(HERE/(case+"_coefficients.json")).write_text(json.dumps(coeff_output,indent=2,sort_keys=True)+"\n")
result={"status":status,"candidate_id":None,"curve_id":cfg["curve_id"],
        "case":case,"boxes_completed":len(results),"rows":results,
        "public_group_hits":sum(len(row["group_hits"]) for row in results if row["kind"]=="frozen_public_raw_point"),
        "certified_public_boxes":sum(row["trace_mask"] is not None for row in results if row["kind"]=="frozen_public_raw_point"),
        "wall_seconds":time.monotonic()-started,
        "peak_rss_raw":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "protocol_sha256":sha(HERE/("run_protocol_"+case+".json")),
        "script_sha256":sha(Path(__file__)),
        "coefficients_sha256":sha(HERE/(case+"_coefficients.json"))}
(HERE/(case+"_result.json")).write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
print(json.dumps({key:result[key] for key in ("case","status","boxes_completed",
                                           "public_group_hits","certified_public_boxes",
                                           "wall_seconds")},sort_keys=True),flush=True)
