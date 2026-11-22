"""Measure exact sharing of coordinate-linear sign certificates across root tuples."""
import hashlib
import itertools
import json
import resource
import time
from pathlib import Path
from sage.all import EllipticCurve, GF, PolynomialRing, matrix, vector

HERE=Path(__file__).resolve().parent
sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
cfg=json.loads((HERE/"pool_protocol.json").read_text())
assert cfg["status"]=="FROZEN_BEFORE_CERTIFICATE_POOL"
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
state=[{} for _ in range(5)]
for line in Path(cfg["sources"]["join_input"]["path"]).read_text().splitlines()[2:]:
    cols=line.split()
    if cols[0]!="S":
        continue
    slot,sid,code,branch,a,b,ca,cb,x,y=map(int,cols[1:])
    state[slot][sid]=E(dec(x),dec(y))
Q=E(*(dec(v) for v in panel["target_point"]))
minus_q=-Q
def determinant(points):
    rows=[]
    for point in points+[minus_q]:
        x,y=point[0],point[1]
        rows.append([F.one(),x,y,x*x,x*y,x*x*x])
    return matrix(F,rows).det()
def add_basis(basis,value):
    while value:
        pivot=value.bit_length()-1
        if pivot in basis:
            value^=basis[pivot]
        else:
            basis[pivot]=value
            return True
    return False
def certifiable(coefficient_rows,indices):
    base=coefficient_rows[indices[0]][0]
    basis={}
    for index in indices:
        row=coefficient_rows[index]
        if index!=indices[0]:
            add_basis(basis,row[0]^base)
        for value in row[1:]:
            add_basis(basis,value)
        if len(basis)==41:
            return False
    test=dict(basis)
    return add_basis(test,base)
def certificate(coefficient_rows,indices):
    base=coefficient_rows[indices[0]][0]
    requirements=[(base,1)]
    for index in indices:
        row=coefficient_rows[index]
        if index!=indices[0]:
            requirements.append((row[0]^base,0))
        requirements.extend((v,0) for v in row[1:])
    A=matrix(GF(2),len(requirements),41,
             lambda r,c:(requirements[r][0]>>c)&1)
    rhs=vector(GF(2),[bit for _,bit in requirements])
    solution=A.solve_right(rhs)
    mask=sum(int(solution[i])<<i for i in range(41))
    assert all((mask&value).bit_count()%2==bit for value,bit in requirements)
    return mask
rows=[]
status="COMPLETE_CERTIFICATE_POOL"
for box_index,box in enumerate(panel["boxes"]):
    if time.monotonic()-started>=cfg["wall_cap_seconds"]:
        status="WALL_CAP_PARTIAL"
        break
    coeffs=[]
    for root_mask in range(32):
        options=[[state[slot][sid] for sid in box["root_choices"][slot][root_mask>>slot&1]]
                 for slot in range(5)]
        d0=determinant([options[j][0] for j in range(5)])
        linear=[determinant([options[slot][int(slot==j)] for slot in range(5)])+d0
                for j in range(5)]
        quadratic=[]
        for i,j in itertools.combinations(range(5),2):
            val=determinant([options[slot][int(slot==i or slot==j)]
                             for slot in range(5)])
            quadratic.append(val+d0+linear[i]+linear[j])
        coeffs.append([enc(v) for v in [d0]+linear+quadratic])
    individual=sum(certifiable(coeffs,(i,)) for i in range(32))
    pairs=[(i,j) for i,j in itertools.combinations(range(32),2)
           if certifiable(coeffs,(i,j))]
    triples=[(i,j,k) for i,j,k in itertools.combinations(range(32),3)
             if certifiable(coeffs,(i,j,k))]
    four_count=sum(certifiable(coeffs,q) for q in itertools.combinations(range(32),4))
    consecutive=[]
    for i in range(0,32,2):
        if certifiable(coeffs,(i,i+1)):
            consecutive.append({"root_masks":[i,i+1],
                                "certificate_mask":certificate(coeffs,(i,i+1))})
    if box_index==0:
        assert not certifiable(coeffs,(0,))
    else:
        assert individual==32
        assert len(consecutive)==16
    rows.append({"box_index":box_index,"kind":box["kind"],
                 "individual_certifiable":individual,
                 "compatible_pairs":len(pairs),
                 "compatible_triples":len(triples),
                 "compatible_quads":four_count,
                 "consecutive_pair_cover":consecutive,
                 "triple_examples":[list(q) for q in triples[:5]]})
    if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss>cfg["rss_cap_bytes"]:
        status="RSS_CAP_PARTIAL"
        break
result={"status":status,"candidate_id":None,"curve_id":cfg["curve_id"],
        "boxes_completed":len(rows),"rows":rows,
        "wall_seconds":time.monotonic()-started,
        "peak_rss_raw":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "protocol_sha256":sha(HERE/"pool_protocol.json"),
        "script_sha256":sha(Path(__file__))}
(HERE/"pool_result.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
print(json.dumps({"status":status,"boxes_completed":len(rows),
                  "wall_seconds":result["wall_seconds"],
                  "random_compatible_triples":sum(x["compatible_triples"] for x in rows[1:]),
                  "random_compatible_quads":sum(x["compatible_quads"] for x in rows[1:])},sort_keys=True),flush=True)
