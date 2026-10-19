"""Exact sign-product norm and one-mask code-box certificates over GF(2^41)."""
import hashlib
import itertools
import json
import resource
import time
from pathlib import Path

HERE=Path(__file__).resolve().parent
sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
cfg=json.loads((HERE/"protocol_v2.json").read_text())
assert cfg["status"]=="FROZEN_BEFORE_SIGN_NORM"
for label,source in cfg["sources"].items():
    assert sha(source["path"])==source["sha256"],label
coeff=json.loads(Path(cfg["sources"]["coefficient_export"]["path"]).read_text())
boxes=json.loads(Path(cfg["sources"]["code_box_result"]["path"]).read_text())
assert coeff["status"]=="COMPLETE_COEFFICIENT_EXPORT"
assert boxes["status"]=="COMPLETE_CODE_BOX_AUDIT"
started=time.monotonic()
FIELD_BITS=41
MODULUS=(1<<41)|(1<<3)|1
FIELD_MASK=(1<<41)-1
PAIRS=list(itertools.combinations(range(5),2))

def multiply(a,b):
    result=0
    while b:
        if b&1:
            result^=a
        b>>=1
        a<<=1
        if a&(1<<FIELD_BITS):
            a^=MODULUS
    assert result<=FIELD_MASK
    return result

def evaluate(row,sign_mask):
    value=row[0]
    for i in range(5):
        if sign_mask>>i&1:
            value^=row[1+i]
    for index,(i,j) in enumerate(PAIRS):
        if sign_mask>>i&1 and sign_mask>>j&1:
            value^=row[6+index]
    return value

def solve_trace(values):
    equations={}
    rank=0
    for value in values:
        v=value
        rhs=1
        while v:
            pivot=(v&-v).bit_length()-1
            if pivot in equations:
                old_v,old_rhs=equations[pivot]
                v^=old_v
                rhs^=old_rhs
            else:
                equations[pivot]=(v,rhs)
                rank+=1
                break
        if not v and rhs:
            return rank,None
    mask=0
    for pivot in sorted(equations,reverse=True):
        v,rhs=equations[pivot]
        bit=rhs^((v&mask).bit_count()&1)
        mask|=bit<<pivot
    assert all((value&mask).bit_count()%2==1 for value in values)
    return rank,mask

def mobius(values):
    out=list(values)
    for bit in range(5):
        for index in range(32):
            if index>>bit&1:
                out[index]^=out[index^(1<<bit)]
    return out

def rank_values(values):
    basis={}
    for value in values:
        while value:
            pivot=(value&-value).bit_length()-1
            if pivot in basis:
                value^=basis[pivot]
            else:
                basis[pivot]=value
                break
    return len(basis)

results=[]
for box_index,rows in enumerate(coeff["boxes"]):
    assert len(rows)==32 and all(len(row)==16 for row in rows)
    norms=[]
    zero_pairs=[]
    for root_mask,row in enumerate(rows):
        norm=1
        for sign_mask in range(32):
            value=evaluate(row,sign_mask)
            if value==0:
                zero_pairs.append([root_mask,sign_mask])
            norm=multiply(norm,value)
        norms.append(norm)
    assert zero_pairs==boxes["rows"][box_index]["group_hits"]
    rank_at_decision,mask=solve_trace(norms)
    rank=rank_values(norms)
    assert rank>=rank_at_decision
    if box_index==0:
        assert zero_pairs==[[0,30]] and mask is None
    else:
        assert not zero_pairs
    if mask is not None:
        values=[(norm&mask).bit_count()%2 for norm in norms]
        anf=mobius(values)
        assert anf==[1]+[0]*31
    else:
        anf=None
    results.append({"box_index":box_index,"kind":boxes["rows"][box_index]["kind"],
                    "zero_pairs":zero_pairs,"norm_rank":rank,
                    "trace_mask":mask,"trace_anf":anf,
                    "norms":norms})
    if time.monotonic()-started>=cfg["wall_cap_seconds"]:
        status="WALL_CAP_PARTIAL"
        break
    if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss>cfg["rss_cap_bytes"]:
        status="RSS_CAP_PARTIAL"
        break
else:
    status="COMPLETE_SIGN_NORM"
result={"status":status,"candidate_id":None,"curve_id":cfg["curve_id"],
        "boxes_completed":len(results),"certified_random_boxes":sum(r["trace_mask"] is not None for r in results[1:]),
        "rows":results,"wall_seconds":time.monotonic()-started,
        "peak_rss_raw":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "protocol_sha256":sha(HERE/"protocol_v2.json"),
        "script_sha256":sha(Path(__file__))}
(HERE/"result_v2.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
print(json.dumps({key:result[key] for key in ("status","boxes_completed",
                                           "certified_random_boxes","wall_seconds")},sort_keys=True),flush=True)
