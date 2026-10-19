"""Independent low-pivot GF(2) rank replay of pooled determinant certificates."""
import hashlib
import itertools
import json
import resource
import time
from pathlib import Path

HERE=Path(__file__).resolve().parent
sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
cfg=json.loads((HERE/"pool_audit_protocol.json").read_text())
assert cfg["status"]=="FROZEN_BEFORE_POOL_RANK_AUDIT"
for label,source in cfg["sources"].items():
    assert sha(source["path"])==source["sha256"],label
export=json.loads((HERE/"pool_coefficients.json").read_text())
produced=json.loads((HERE/"pool_result.json").read_text())
assert export["status"]=="COMPLETE_COEFFICIENT_EXPORT"
assert produced["status"]=="COMPLETE_CERTIFICATE_POOL"
started=time.monotonic()

def reduce_low(values):
    basis={}
    for value in values:
        while value:
            pivot=(value & -value).bit_length()-1
            if pivot in basis:
                value^=basis[pivot]
            else:
                basis[pivot]=value
                break
    return basis

def possible(rows,indices):
    base=rows[indices[0]][0]
    differences=[]
    for i in indices:
        if i!=indices[0]:
            differences.append(rows[i][0]^base)
        differences.extend(rows[i][1:])
    rank=len(reduce_low(differences))
    return len(reduce_low(differences+[base]))==rank+1

audits=[]
status="PASS_INDEPENDENT_POOL_RANK_AUDIT"
for box_index,rows in enumerate(export["boxes"]):
    if time.monotonic()-started>cfg["wall_cap_seconds"]:
        status="WALL_CAP_PARTIAL_POOL_AUDIT"
        break
    assert len(rows)==32 and all(len(row)==16 for row in rows)
    single=sum(possible(rows,(i,)) for i in range(32))
    pair=sum(possible(rows,q) for q in itertools.combinations(range(32),2))
    triple=sum(possible(rows,q) for q in itertools.combinations(range(32),3))
    quad=sum(possible(rows,q) for q in itertools.combinations(range(32),4))
    reference=produced["rows"][box_index]
    assert (single,pair,triple,quad)==(
        reference["individual_certifiable"],reference["compatible_pairs"],
        reference["compatible_triples"],reference["compatible_quads"])
    for cover in reference["consecutive_pair_cover"]:
        indices=cover["root_masks"]
        mask=cover["certificate_mask"]
        assert possible(rows,indices)
        base=rows[indices[0]][0]
        assert (mask&base).bit_count()%2==1
        for i in indices:
            assert (mask&rows[i][0]).bit_count()%2==1
            assert all((mask&value).bit_count()%2==0 for value in rows[i][1:])
    audits.append({"box_index":box_index,"single":single,"pair":pair,
                   "triple":triple,"quad":quad,
                   "explicit_pair_cover_size":len(reference["consecutive_pair_cover"])})
result={"status":status,"candidate_id":None,"curve_id":cfg["curve_id"],
        "boxes_checked":len(audits),"rows":audits,
        "wall_seconds":time.monotonic()-started,
        "peak_rss_raw":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "protocol_sha256":sha(HERE/"pool_audit_protocol.json"),
        "script_sha256":sha(Path(__file__))}
(HERE/"pool_audit_result.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
print(json.dumps({"status":status,"boxes_checked":len(audits),
                  "wall_seconds":result["wall_seconds"]},sort_keys=True))
