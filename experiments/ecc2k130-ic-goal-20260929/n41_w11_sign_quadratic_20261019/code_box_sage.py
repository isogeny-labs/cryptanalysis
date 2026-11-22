"""Audit whether one sign-quadratic separator extends across two root choices per slot."""
import hashlib
import itertools
import json
import resource
import time
from pathlib import Path
from sage.all import EllipticCurve, GF, PolynomialRing, matrix

HERE = Path(__file__).resolve().parent
sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
cfg = json.loads((HERE/"code_box_run_protocol.json").read_text())
assert cfg["status"] == "FROZEN_BEFORE_CODE_BOX_AUDIT"
for label, source in cfg["sources"].items():
    assert sha(source["path"]) == source["sha256"], label
panel = json.loads((HERE/"code_box_panel.json").read_text())
assert panel["status"] == "FROZEN_CODE_BOX_PANEL" and len(panel["boxes"]) == 9
started = time.monotonic()
B = PolynomialRing(GF(2), "u")
u = B.gen()
F = GF(2**41, name="u", modulus=u**41+u**3+1)
E = EllipticCurve(F, [1,0,0,0,1])
dec = F.from_integer
enc = lambda value: sum(int(bit) << i for i,bit in enumerate(value.polynomial().list()))
states = [{} for _ in range(5)]
meta = [{} for _ in range(5)]
for line in Path(cfg["sources"]["join_input"]["path"]).read_text().splitlines()[2:]:
    words = line.split()
    if words[0] != "S":
        continue
    slot,sid,code,branch,a,b,ca,cb,x,y = map(int,words[1:])
    states[slot][sid] = E(dec(x),dec(y))
    meta[slot][sid] = (code,ca,cb,x)
Q = E(*(dec(v) for v in panel["target_point"]))
minus_q = -Q

def determinant(points):
    rows = []
    for point in points+[minus_q]:
        x,y = point[0],point[1]
        rows.append([F.one(),x,y,x*x,x*y,x*x*x])
    return matrix(F,rows).det()

def add_basis(basis,value):
    original = value
    while value:
        pivot = value.bit_length()-1
        if pivot in basis:
            value ^= basis[pivot]
        else:
            basis[pivot] = value
            return True
    return False

rows = []
status = "COMPLETE_CODE_BOX_AUDIT"
for box_index,box in enumerate(panel["boxes"]):
    if time.monotonic()-started >= cfg["wall_cap_seconds"]:
        status = "WALL_CAP_PARTIAL"
        break
    options = [[[states[slot][sid] for sid in box["root_choices"][slot][root]]
                for root in range(2)] for slot in range(5)]
    columns = []
    xvalues = [panel["target_point"][0]]
    for slot in range(5):
        for root in range(2):
            ids = box["root_choices"][slot][root]
            assert options[slot][root][0] == -options[slot][root][1]
            assert options[slot][root][0][0] == options[slot][root][1][0]
            assert meta[slot][ids[0]][0] == meta[slot][ids[1]][0]
            columns += list(meta[slot][ids[0]][1:3])
            xvalues.append(meta[slot][ids[0]][3])
    assert len(set(columns)) == 20 and len(set(xvalues)) == 11
    variation_basis = {}
    base_value = None
    root_to_full_rank = None
    group_hits = []
    sign_certificates = 0
    for root_mask in range(32):
        signs = [options[slot][root_mask >> slot & 1] for slot in range(5)]
        d0 = determinant([signs[j][0] for j in range(5)])
        linear = [determinant([signs[slot][int(slot == j)] for slot in range(5)])+d0
                  for j in range(5)]
        quadratic = {}
        for i,j in itertools.combinations(range(5),2):
            value = determinant([signs[slot][int(slot == i or slot == j)]
                                 for slot in range(5)])
            quadratic[(i,j)] = value+d0+linear[i]+linear[j]
        d0_int = enc(d0)
        if root_mask == 0:
            base_value = d0_int
        else:
            add_basis(variation_basis,d0_int ^ base_value)
        for value in linear+list(quadratic.values()):
            add_basis(variation_basis,enc(value))
        if len(variation_basis) == 41 and root_to_full_rank is None:
            root_to_full_rank = root_mask+1
        local_basis = {}
        for value in linear+list(quadratic.values()):
            add_basis(local_basis,enc(value))
        local_with_base = dict(local_basis)
        sign_certificates += add_basis(local_with_base,d0_int)
        for sign_mask in range(32):
            points = [signs[j][sign_mask >> j & 1] for j in range(5)]
            predicted = d0
            for j in range(5):
                if sign_mask >> j & 1:
                    predicted += linear[j]
            for (i,j),value in quadratic.items():
                if (sign_mask >> i & 1) and (sign_mask >> j & 1):
                    predicted += value
            actual = determinant(points)
            assert actual == predicted,(box_index,root_mask,sign_mask)
            hit = sum(points,E(0)) == Q
            assert (actual == 0) == hit,(box_index,root_mask,sign_mask)
            if hit:
                group_hits.append([root_mask,sign_mask])
    basis_with_base = dict(variation_basis)
    single_certificate = add_basis(basis_with_base,base_value)
    if box_index == 0:
        assert [0,30] in group_hits
    rows.append({"box_index":box_index,"kind":box["kind"],
                 "root_tuples":32,"sign_assignments":1024,
                 "variation_rank":len(variation_basis),
                 "first_full_rank_root_count":root_to_full_rank,
                 "single_coordinate_certificate":single_certificate,
                 "sign_family_certificates":sign_certificates,
                 "group_hits":group_hits})
    if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss > cfg["rss_cap_bytes"]:
        status = "RSS_CAP_PARTIAL"
        break
result = {"status":status,"candidate_id":None,"curve_id":cfg["curve_id"],
          "boxes_completed":len(rows),"rows":rows,
          "wall_seconds":time.monotonic()-started,
          "peak_rss_raw":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
          "protocol_sha256":sha(HERE/"code_box_run_protocol.json"),
          "script_sha256":sha(Path(__file__))}
(HERE/"code_box_result.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
print(json.dumps({"status":status,"boxes_completed":len(rows),
                  "wall_seconds":result["wall_seconds"],
                  "full_rank_boxes":sum(row["variation_rank"]==41 for row in rows)},sort_keys=True),flush=True)
