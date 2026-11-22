"""Independent point reconstruction and low-pivot quadratic-rank audit."""
import hashlib
import json
import resource
import signal
import time
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE=Path(__file__).resolve().parent
cfg=json.loads((HERE/"audit_protocol.json").read_text())
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
for name,item in cfg["sources"].items():
    assert sha(item["path"])==item["sha256"],name
assert not (HERE/"audit_result.json").exists()
signal.alarm(cfg["wall_cap_seconds"])
started=time.monotonic()
result=json.loads((HERE/"result.json").read_text())
panel=json.loads(Path(cfg["sources"]["panel"]["path"]).read_text())
frozen=json.loads(Path(cfg["sources"]["sixpair"]["path"]).read_text())["n131"]
public=json.loads(Path(cfg["sources"]["public"]["path"]).read_text())
old_sets=json.loads(Path(cfg["sources"]["prior_x_sets"]["path"]).read_text())["n131"]
R=PolynomialRing(GF(2),"z")
z=R.gen()
F=GF(2**131,name="z",modulus=z**131+z**13+z**2+z+1)
E=EllipticCurve(F,[1,0,0,0,1])
def dec(n):
    return F(R([(int(n)>>i)&1 for i in range(131)]))
def enc(a):
    return sum(int(bit)<<i for i,bit in enumerate(a.polynomial().list()))
def point(row):
    return E(dec(row[0]),dec(row[1]))
fixed=[]
for slot in (1,2):
    fixed.append([point(raw) for root in frozen["edges"][slot]["roots"] for raw in root])
assert all(len(f)==4 for f in fixed)
suffix=sum((point(frozen["edges"][i]["roots"][0][0]) for i in (3,4,5)),E(0))
constructed=sum((point(edge["roots"][0][0]) for edge in frozen["edges"]),E(0))
residuals={"constructed":constructed-suffix,
           "panel_public":point(panel["target"])-suffix,
           "public":point(public["raw_point"])-suffix}
target_x={k:enc(p[0]) for k,p in residuals.items()}
assert target_x==result["residual_x"]

def halftrace(a):
    acc=F.zero()
    v=a
    for _ in range(66):
        acc+=v
        v=v**4
    assert acc*acc+acc==a
    return acc
cache={}
def lift(mask):
    if mask not in cache:
        w=dec(mask<<1)
        assert w and w.trace()==0 and (1/w).trace()==0
        roots=E.lift_x(1+1/halftrace(w),all=True)
        assert len(roots)==2
        cache[mask]=roots[0]
    return cache[mask]
def feature(x):
    out=x
    for i in range(131):
        if not (x>>i)&1:continue
        base=131+i*(261-i)//2
        for j in range(i+1,131):
            if (x>>j)&1:
                out|=1<<(base+j-i-1)
    return out
def add(piv,word):
    while word:
        bit=(word & -word).bit_length()-1
        old=piv.get(bit)
        if old is None:
            piv[bit]=word
            return
        word^=old
def contains(piv,word):
    while word:
        bit=(word & -word).bit_length()-1
        old=piv.get(bit)
        if old is None:return False
        word^=old
    return True

seen=set()
base=None
piv={}
entries={name:None for name in target_x}
checkpoints={row["families"]:row for row in result["rows"]}
first_full=None
for number,(a,b) in enumerate(result["source_family_masks"],1):
    assert a<b and a^b==cfg["seed_mask"]
    p,q=lift(a),lift(b)
    pair=[left+right for left in (p,-p) for right in (q,-q)]
    vals=set()
    for first in pair:
        for second in fixed[0]:
            part=first+second
            for third in fixed[1]:
                total=part+third
                assert total!=E(0)
                vals.add(enc(total[0]))
    assert len(vals)==32
    if number<=5:
        assert sorted(vals)==old_sets[number-1]
    for x in vals:
        if x in seen:continue
        seen.add(x)
        if base is None:base=x
        else:add(piv,feature(x)^feature(base))
    if number in checkpoints:
        row=checkpoints[number]
        assert row["distinct_x"]==len(seen)
        assert row["quadratic_rank"]==len(piv)
        for name,x in target_x.items():
            assert row["target_checks"][name]["exact"]==(x in seen)
            assert row["target_checks"][name]["quadratic"]==contains(piv,feature(x)^feature(base))
    for name,x in target_x.items():
        if entries[name] is None and contains(piv,feature(x)^feature(base)):
            entries[name]=number
    if first_full is None and len(piv)==8646:
        first_full=number

assert len(piv)==8646 and first_full is not None
assert entries["constructed"]==1
out={"status":"PASS_INDEPENDENT_N131_TRIPLE_X_QUADRATIC_AUDIT",
     "curve_id":result["curve_id"],"families":len(result["source_family_masks"]),
     "distinct_x":len(seen),"quadratic_rank":len(piv),
     "first_full_rank_family":first_full,
     "first_quadratic_hull_entry":entries,
     "wall_seconds":time.monotonic()-started,
     "maxrss_raw":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
     "producer_sha256":sha(HERE/"result.json"),
     "audit_protocol_sha256":sha(HERE/"audit_protocol.json")}
(HERE/"audit_result.json").write_text(json.dumps(out,sort_keys=True,indent=2)+"\n")
signal.alarm(0)
print(json.dumps(out,sort_keys=True))
