"""Independent checked-Sage replay of sign products and whole-box trace masks."""
import hashlib
import itertools
import json
import resource
import time
from pathlib import Path
from sage.all import GF, PolynomialRing

HERE=Path(__file__).resolve().parent
sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
cfg=json.loads((HERE/"audit_protocol.json").read_text())
assert cfg["status"]=="FROZEN_BEFORE_NORM_AUDIT"
for label,source in cfg["sources"].items():
    assert sha(source["path"])==source["sha256"],label
result=json.loads((HERE/"result_v2.json").read_text())
coeff=json.loads(Path(cfg["sources"]["coefficient_export"]["path"]).read_text())
boxes=json.loads(Path(cfg["sources"]["code_box_result"]["path"]).read_text())
started=time.monotonic()
P=PolynomialRing(GF(2),"u")
u=P.gen()
F=GF(2**41,name="u",modulus=u**41+u**3+1)
dec=F.from_integer
enc=lambda value:sum(int(bit)<<i for i,bit in enumerate(value.polynomial().list()))
pairs=list(itertools.combinations(range(5),2))
def eval_sage(row,sign_mask):
    value=dec(row[0])
    for i in range(5):
        if sign_mask>>i&1:
            value+=dec(row[1+i])
    for index,(i,j) in enumerate(pairs):
        if sign_mask>>i&1 and sign_mask>>j&1:
            value+=dec(row[6+index])
    return value
zero_pairs_checked=0
trace_values_checked=0
for box_index,rows in enumerate(coeff["boxes"]):
    audited_norms=[]
    zeros=[]
    for root_mask,row in enumerate(rows):
        product=F.one()
        values=[]
        for sign_mask in range(32):
            value=eval_sage(row,sign_mask)
            values.append(value)
            if value==0:
                zeros.append([root_mask,sign_mask])
            product*=value
        assert enc(product)==result["rows"][box_index]["norms"][root_mask]
        # Reindexing any one sign bit permutes the same 32 factors.
        alternate=F.one()
        for sign_mask in range(32):
            alternate*=values[sign_mask^1]
        assert alternate==product
        audited_norms.append(product)
    assert zeros==boxes["rows"][box_index]["group_hits"]
    assert zeros==result["rows"][box_index]["zero_pairs"]
    mask=result["rows"][box_index]["trace_mask"]
    if mask is None:
        assert box_index==0 and zeros==[[0,30]]
    else:
        assert box_index>0 and not zeros
        for norm in audited_norms:
            assert (mask&enc(norm)).bit_count()%2==1
            trace_values_checked+=1
    zero_pairs_checked+=len(zeros)
audit={"status":"PASS_INDEPENDENT_SAGE_NORM_AUDIT","candidate_id":None,
       "curve_id":cfg["curve_id"],"boxes_checked":len(coeff["boxes"]),
       "norm_products_checked":9*32,
       "determinant_factors_checked":9*32*32,
       "trace_values_checked":trace_values_checked,
       "zero_pairs_checked":zero_pairs_checked,
       "wall_seconds":time.monotonic()-started,
       "peak_rss_raw":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
       "protocol_sha256":sha(HERE/"audit_protocol.json"),
       "script_sha256":sha(Path(__file__))}
(HERE/"audit_result.json").write_text(json.dumps(audit,indent=2,sort_keys=True)+"\n")
print(json.dumps(audit,sort_keys=True),flush=True)
