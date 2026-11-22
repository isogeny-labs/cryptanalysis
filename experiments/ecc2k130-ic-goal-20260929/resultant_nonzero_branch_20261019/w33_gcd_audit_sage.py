"""Independent checked-Sage W33 subspace-GCD audit of both width-four blocks."""
import hashlib
import json
import resource
import time
from pathlib import Path

from sage.all import GF, PolynomialRing

HERE=Path(__file__).resolve().parent
sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
cfg=json.loads((HERE/"w33_gcd_protocol.json").read_text())
assert cfg["status"]=="FROZEN_BEFORE_W33_GCD_AUDIT"
for label,source in cfg["sources"].items():
    assert sha(source["path"])==source["sha256"],label
source=json.loads(Path(cfg["sources"]["coefficients"]["path"]).read_text())

B=PolynomialRing(GF(2),"u")
u=B.gen()
F=GF(2**131,name="u",modulus=u**131+u**13+u**2+u+1)
P=PolynomialRing(F,"z")
z=P.gen()
dec=lambda value:F.from_integer(value)
seed_mask=898618
bits=[i for i in range(33) if i!=seed_mask.bit_length()-1]
assert len(bits)==32
seed=dec(898618<<1)


def product(code,rotation):
    a=sum((dec(1<<(bit+1)) for j,bit in enumerate(bits) if code>>j&1),F.zero())
    return (a*a+seed*a)**(1<<rotation)


def linearized(coefficients,value):
    result=F.zero()
    for c in coefficients:
        result+=c*value
        value*=value
    return result


started=time.monotonic()
qbasis=[product(1<<j,18) for j in range(32)]
coefficients=[F.one()]
for basis in qbasis:
    w=linearized(coefficients,basis)
    assert w
    next_coefficients=[w*coefficients[0]]
    for j in range(1,len(coefficients)):
        next_coefficients.append(coefficients[j-1]*coefficients[j-1]+w*coefficients[j])
    next_coefficients.append(coefficients[-1]*coefficients[-1])
    coefficients=next_coefficients
assert len(coefficients)==33
assert all(linearized(coefficients,b)==0 for b in qbasis)
terms=[[(i,j,dec(c)) for i,j,c in row["terms"]] for row in source["rows"][:2]]
assert all(len(t)==13 for t in terms)
assert cfg["first_codes"]==list(range(16))
rows=[]
status="COMPLETE_W33_GCD_AUDIT"
for target_index in cfg["target_indexes"]:
    for code in cfg["first_codes"]:
        if time.monotonic()-started>=cfg["wall_cap_seconds"]:
            status="WALL_CAP_PARTIAL_REFERENCE"
            break
        p=product(code,0)
        pp=[F.one(),p,p*p,p*p*p,p*p*p*p]
        h=sum((c*pp[i]*z**j for i,j,c in terms[target_index]),P.zero())
        if not h:
            gcd_degree=-1
            reject=False
        else:
            x=z%h
            remainder=P.zero()
            for c in coefficients:
                remainder=(remainder+c*x)%h
                x=(x*x)%h
            gcd_degree=int(h.gcd(remainder).degree())
            reject=gcd_degree==0
        row={"target_index":target_index,"p_code":code,"reject":reject,
             "quartic_degree":int(h.degree()) if h else -1,"gcd_degree":gcd_degree}
        rows.append(row)
        if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss>cfg["rss_cap_bytes"]:
            status="RSS_CAP_PARTIAL_REFERENCE"
            break
    if status!="COMPLETE_W33_GCD_AUDIT":
        break
if status=="COMPLETE_W33_GCD_AUDIT":
    assert next(x for x in rows if x["target_index"]==0 and x["p_code"]==3)["reject"] is False
result={"status":status,"candidate_id":None,"rows":rows,"requested_rows":len(cfg["target_indexes"])*len(cfg["first_codes"]),
        "curve_id":source["curve_id"],"field_degree":131,"source_bits":32,"wall_seconds":time.monotonic()-started,
        "peak_rss_raw":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "protocol_sha256":sha(HERE/"w33_gcd_protocol.json"),"script_sha256":sha(Path(__file__))}
(HERE/"w33_gcd_result.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
print(json.dumps({k:result[k] for k in ("status","requested_rows","wall_seconds","peak_rss_raw")},sort_keys=True),flush=True)
