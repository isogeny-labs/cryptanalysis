"""Source-bound cubic profile for the frozen two-pair resultant panels."""
import hashlib
import json
import random
import resource
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
cfg = json.loads((HERE / "profile_protocol.json").read_text())
sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
assert cfg["status"] == "FROZEN_BEFORE_CUBIC_PROFILE"
for name,source in cfg["sources"].items():
    assert sha(source["path"]) == source["sha256"], name
base = Path(cfg["sources"]["scan_source"]["path"])
prefix = base.read_text().split("started = time.monotonic()",1)[0]
ns = {"__file__":str(base)}
exec(compile(prefix,str(base),"exec"),ns)
Field = ns["Field"]
poly_add = ns["poly_add"]
poly_mul = ns["poly_mul"]
poly_pow = ns["poly_pow"]
product_basis = ns["product_basis"]
read_n41_terms = ns["read_n41_terms"]
read_n131_terms = ns["read_n131_terms"]


def evaluate(poly, assignment):
    out = 0
    for mask,value in poly.items():
        if mask & assignment == mask:
            out ^= value
    return out


start = time.monotonic()
panels = []
for spec in ns["cfg"]["panels"]:
    n,k = spec["field_degree"],spec["first_free_bits"]
    field = Field(n,(1<<3)|1 if n==41 else (1<<13)|(1<<2)|(1<<1)|1)
    seed = 112 if n==41 else 898618<<1
    positions = [0,1,2,3,4,6,7,8,9,10] if n==41 else [i for i in range(33) if i!=898618 .bit_length()-1]
    rotation = (12,24) if n==41 else (0,18)
    pb = product_basis(field,seed,positions,rotation[0])
    qb = product_basis(field,seed,positions,rotation[1])
    offset = spec["first_code_offset"]
    p0 = 0
    for bit in range(k,len(pb)):
        if offset>>bit&1:p0 ^= pb[bit]
    p = ({0:p0} if p0 else {}) | {1<<bit:pb[bit] for bit in range(k)}
    q = {1<<(k+bit):value for bit,value in enumerate(qb)}
    pp = [poly_pow(field,p,i) for i in range(5)]
    qq = [poly_pow(field,q,i) for i in range(5)]
    terms = read_n41_terms(spec["target_index"]) if n==41 else read_n131_terms(spec["target_index"])
    F = {}
    for a,b,coefficient in terms:
        product = poly_mul(field,pp[a],qq[b])
        F = poly_add(F,{mask:field.mul(coefficient,value) for mask,value in product.items()})
    cubic = poly_mul(field,p,F)
    assert max(mask.bit_count() for mask in F)==4
    assert max(mask.bit_count() for mask in cubic)==3
    assert len(F)==(886 if n==41 else 5317)
    if n==41:
        # Exhaust the entire frozen first-code block and all second-code bits.
        assignments = [(x,y) for x in range(1<<k) for y in range(1<<len(qb))]
    else:
        rng=random.Random(20261019+spec["target_index"])
        assignments=[(rng.randrange(1<<k),rng.randrange(1<<len(qb))) for _ in range(4096)]
        assignments.append((3,16722))
    checked=0;exceptional=0;zeros_original=0;zeros_cubic=0
    for local,second in assignments:
        assignment=local|(second<<k)
        first_product=p0
        for bit in range(k):
            if local>>bit&1:first_product ^= pb[bit]
        f=evaluate(F,assignment)
        g=evaluate(cubic,assignment)
        assert g==field.mul(first_product,f)
        if first_product:
            assert (f==0)==(g==0)
        else:
            exceptional+=1
        zeros_original+=int(f==0)
        zeros_cubic+=int(g==0)
        checked+=1
    panels.append({"field_degree":n,"target_index":spec["target_index"],"first_free_bits":k,
                   "first_code_offset":offset,"first_product_offset":p0,
                   "original_monomials":len(F),"scaled_monomials":len(cubic),
                   "original_degree_histogram":{str(d):sum(mask.bit_count()==d for mask in F) for d in range(5)},
                   "scaled_degree_histogram":{str(d):sum(mask.bit_count()==d for mask in cubic) for d in range(5)},
                   "assignments_checked":checked,"exceptional_assignments":exceptional,
                   "original_zero_assignments":zeros_original,"scaled_zero_assignments":zeros_cubic})

result={"status":"PASS_CUBIC_PROFILE","candidate_id":None,
        "protocol_sha256":sha(HERE/"profile_protocol.json"),"script_sha256":sha(__file__),
        "wall_seconds":time.monotonic()-start,"self_peak_rss_raw":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "panels":panels}
assert result["wall_seconds"]<cfg["wall_cap_seconds"]
assert result["self_peak_rss_raw"]<cfg["rss_cap_bytes"]
(HERE/"profile_result.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
print(json.dumps(result,sort_keys=True))
