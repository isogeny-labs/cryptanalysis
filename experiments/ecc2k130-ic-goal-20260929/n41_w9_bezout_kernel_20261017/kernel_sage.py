"""Check normalized Bezout kernel witnesses against the frozen N41 panel."""
import hashlib
import json
import resource
import signal
import time
from pathlib import Path

from sage.all import GF,PolynomialRing,matrix,vector

HERE=Path(__file__).resolve().parent
p=json.loads((HERE/"kernel_protocol.json").read_text())
for path,digest in p["sources"].items():
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==digest,path
assert not (HERE/"kernel_result.json").exists()
signal.signal(signal.SIGALRM,lambda _s,_f: (_ for _ in ()).throw(TimeoutError("kernel panel cap")))
signal.alarm(p["wall_cap_seconds"])
started=time.monotonic()
panel=json.loads(Path(p["panel"]).read_text())
source=json.loads(Path(p["states"]).read_text())
fixture=json.loads(Path(p["fixture"]).read_text())
P=PolynomialRing(GF(2),"u")
u=P.gen()
F=GF(2**41,name="u",modulus=u**41+u**3+1)
W=PolynomialRing(F,"w")
w=W.gen()


def dec(n):
    return F(P([(int(n)>>i)&1 for i in range(41)]))


seed_int=source["seed"]<<1
seed=dec(seed_int)
h0=sum((seed**(1<<(2*j)) for j in range(21)),F.zero())**2
bits=[i for i in range(9) if i!=5]
base=[dec((1<<bit)<<1)*dec(((1<<bit)<<1)^seed_int) for bit in bits]


def product(code,rotation):
    return sum((a**(1<<rotation) for j,a in enumerate(base) if code>>j&1),F.zero())


def quartic(x,pp,rotation):
    h=h0**(1<<rotation)
    c=1+h
    b=x*w
    a=1+b**2
    d=x**2+w**2
    m=a*h+c*d
    return a*d*pp**2+b*m*pp+m**2+c*h*b**2


def bezout(f,g):
    fc=[f[i] for i in range(5)]
    gc=[g[i] for i in range(5)]
    B=[[F.zero() for _ in range(4)] for _ in range(4)]
    for m in range(1,5):
        for n in range(m):
            value=fc[m]*gc[n]+fc[n]*gc[m]
            for r in range(m-n):
                B[m-1-r][n+r]+=value
    return matrix(F,B)


rows=[]
for row in panel:
    f=quartic(dec(row["z"]),product(row["code3"],12),12)
    g=quartic(dec(fixture["public_reciprocal"]),product(row["code4"],24),24)
    B=bezout(f,g)
    root=dec(row["w"])
    witness=vector(F,[1,root,root**2,root**3])
    fv=f(root)
    gv=g(root)
    rank=int(B.rank())
    zero=all(value==0 for value in B*witness)
    assert gv==0
    assert zero==(fv==0)==(row["kind"]=="positive")
    assert rank==(3 if row["kind"]=="positive" else 4)
    rows.append({"kind":row["kind"],"control_index":row.get("control_index"),
                 "rank":rank,"normalized_witness_zero":zero,
                 "preceding_quartic_at_w_zero":bool(fv==0)})

finished=time.monotonic()
signal.alarm(0)
out={"status":"PASS_NORMALIZED_BEZOUT_KERNEL_PANEL",
     "candidate_id":None,"curve_id":source["curve_id"],
     "positive_rank_three":sum(row["rank"]==3 for row in rows),
     "control_rank_four":sum(row["rank"]==4 for row in rows),
     "rows":rows,"arithmetic_wall_seconds":finished-started,
     "self_maxrss_bytes":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
     "protocol_sha256":hashlib.sha256((HERE/"kernel_protocol.json").read_bytes()).hexdigest()}
(HERE/"kernel_result.json").write_text(json.dumps(out,sort_keys=True,indent=2)+"\n")
print(json.dumps({k:v for k,v in out.items() if k!="rows"},sort_keys=True))
