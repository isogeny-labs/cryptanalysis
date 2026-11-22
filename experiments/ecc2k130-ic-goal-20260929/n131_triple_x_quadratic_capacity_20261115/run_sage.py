"""Quadratic x-feature hull for ascending source-valid W23 three-pair families."""
import hashlib
import json
import resource
import signal
import time
from pathlib import Path

import psutil
from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
cfg = json.loads((HERE / "protocol.json").read_text())
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
for name, row in cfg["sources"].items():
    assert sha(row["path"]) == row["sha256"], name
assert cfg["curve_id"] == "EC1N131Ckb1heb5f1998f20b"
assert not (HERE / "result.json").exists()
signal.alarm(cfg["wall_cap_seconds"])
started = time.monotonic()

R = PolynomialRing(GF(2), "t")
t = R.gen()
F = GF(2**131, name="t", modulus=t**131+t**13+t**2+t+1)
E = EllipticCurve(F, [1,0,0,0,1])
def dec(value):
    return F(R([(int(value)>>i)&1 for i in range(131)]))
def enc(value):
    return sum(int(b)<<i for i,b in enumerate(value.polynomial().list()))
def point(raw):
    return E(dec(raw[0]),dec(raw[1]))

panel = json.loads(Path(cfg["sources"]["panel"]["path"]).read_text())
prior = json.loads(Path(cfg["sources"]["sixpair"]["path"]).read_text())["n131"]
public = json.loads(Path(cfg["sources"]["public"]["path"]).read_text())
assert public["curve_id"] == cfg["curve_id"]
assert len(panel["variants"]) == 4
fixed = [[point(row) for root in prior["edges"][slot]["roots"] for row in root]
         for slot in (1,2)]
assert all(len(row)==4 for row in fixed)
constructed = sum((point(edge["roots"][0][0]) for edge in prior["edges"]),E(0))
suffix = sum((point(prior["edges"][slot]["roots"][0][0]) for slot in (3,4,5)),E(0))
residuals = {"constructed":constructed-suffix,
             "panel_public":point(panel["target"])-suffix,
             "public":point(public["raw_point"])-suffix}
assert all(v != E(0) for v in residuals.values())
target_x = {name:enc(v[0]) for name,v in residuals.items()}

seed = cfg["seed_mask"]
def halftrace(w):
    v,out=w,F.zero()
    for _ in range(66):
        out += v
        v = v**4
    assert out*out+out == w
    return out
cache = {}
def source(mask):
    if mask not in cache:
        w = dec(mask<<1)
        assert w and w.trace()==0 and (1/w).trace()==0
        x = 1 + 1/halftrace(w)
        roots=E.lift_x(x,all=True)
        assert len(roots)==2
        cache[mask]=roots[0]
    return cache[mask]
def orbit_key(mask):
    p=4*source(mask)
    assert p!=E(0)
    x=p[0]
    smallest=None
    for _ in range(131):
        value=enc(x)
        smallest=value if smallest is None else min(smallest,value)
        x=x*x
    return smallest

fixed_keys={orbit_key(mask) for edge in prior["edges"][1:] for mask in edge["masks"]}
assert len(fixed_keys)==10
families=[]
for row in panel["variants"]:
    families.append({"masks":row["masks"],
                     "points":[point(raw) for root in row["roots"] for raw in root]})
assert families[0]["masks"]==[3,898617]

def feature(x):
    out=x
    bits=x
    while bits:
        low=bits & -bits
        i=low.bit_length()-1
        bits^=low
        out |= (x>>(i+1)) << (131+i*(261-i)//2)
    return out

def add(pivots,word):
    while word:
        bit=word.bit_length()-1
        old=pivots.get(bit)
        if old is None:
            pivots[bit]=word
            return True
        word^=old
    return False
def contains(pivots,word):
    while word:
        bit=word.bit_length()-1
        old=pivots.get(bit)
        if old is None:
            return False
        word^=old
    return True

base=None
linear_pivots={}
quadratic_pivots={}
seen=set()
rows=[]
source_start=time.monotonic()
next_mask=47
process=psutil.Process()
peak_rss=0
for count in range(1,cfg["family_cap"]+1):
    if count>len(families):
        while True:
            mask=next_mask
            next_mask+=1
            if next_mask>=cfg["mask_scan_cap"]:
                raise RuntimeError("mask scan cap before family cap")
            mate=mask^seed
            if mask>=mate or mask==0 or mate==0:
                continue
            a,b=dec(mask<<1),dec(mate<<1)
            if a.trace() or b.trace() or (1/a).trace() or (1/b).trace():
                continue
            keys=(orbit_key(mask),orbit_key(mate))
            if keys[0]==keys[1] or any(k in fixed_keys for k in keys):
                continue
            p,q=source(mask),source(mate)
            states=[u+v for u in (p,-p) for v in (q,-q)]
            assert all(s!=E(0) for s in states)
            assert len({enc(s[0]) for s in states})==2
            families.append({"masks":[mask,mate],"points":states})
            break
    family=families[count-1]
    values=set()
    for a in family["points"]:
        for b in fixed[0]:
            ab=a+b
            for c in fixed[1]:
                total=ab+c
                assert total!=E(0)
                values.add(enc(total[0]))
    assert len(values)==32
    for x in sorted(values):
        if x in seen:continue
        seen.add(x)
        if base is None:
            base=x
        else:
            add(linear_pivots,x^base)
            add(quadratic_pivots,feature(x)^feature(base))
    if count in cfg["checkpoints"]:
        row={"families":count,"distinct_x":len(seen),
             "linear_rank":len(linear_pivots),"quadratic_rank":len(quadratic_pivots),
             "linear_codim":131-len(linear_pivots),
             "quadratic_codim":8646-len(quadratic_pivots),
             "target_checks":{name:{"exact":x in seen,
                  "linear":contains(linear_pivots,x^base),
                  "quadratic":contains(quadratic_pivots,feature(x)^feature(base))}
                  for name,x in target_x.items()},
             "wall_seconds":time.monotonic()-source_start}
        rows.append(row)
    peak_rss=max(peak_rss,process.memory_info().rss)
    if peak_rss>cfg["rss_cap_bytes"]:
        raise MemoryError("RSS cap")

out={"status":"PASS_N131_W23_TRIPLE_X_QUADRATIC_CAPACITY",
     "candidate_id":None,"curve_id":cfg["curve_id"],
     "source_family_masks":[f["masks"] for f in families],
     "residual_x":target_x,"rows":rows,
     "scan_next_mask":next_mask,"source_seconds":time.monotonic()-source_start,
     "total_seconds":time.monotonic()-started,"peak_rss_sample_bytes":peak_rss,
     "maxrss_raw":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
     "protocol_sha256":sha(HERE/"protocol.json")}
(HERE/"result.json").write_text(json.dumps(out,sort_keys=True,indent=2)+"\n")
signal.alarm(0)
print(json.dumps({"status":out["status"],"seconds":out["source_seconds"],
                  "ranks":[(r["families"],r["linear_rank"],r["quadratic_rank"])
                           for r in rows]}))
