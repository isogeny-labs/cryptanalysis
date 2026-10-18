"""Check a characteristic-two 4x4 Bezout determinant against Sage resultants."""
import hashlib
import json
import resource
import signal
import time
from pathlib import Path

from sage.all import GF, PolynomialRing, matrix

HERE = Path(__file__).resolve().parent
p = json.loads((HERE / "bezout_protocol.json").read_text())
for path, digest in p["sources"].items():
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == digest, path
assert not (HERE / "bezout_result.json").exists()
signal.signal(signal.SIGALRM, lambda _s, _f: (_ for _ in ()).throw(TimeoutError("Bezout cap")))
signal.alarm(p["wall_cap_seconds"])
start = time.monotonic()
panel = json.loads(Path(p["panel"]).read_text())
source = json.loads(Path(p["states"]).read_text())
fixture = json.loads(Path(p["fixture"]).read_text())
P = PolynomialRing(GF(2), "u")
u = P.gen()
F = GF(2**41,name="u",modulus=u**41+u**3+1)
W = PolynomialRing(F,"w")
w = W.gen()


def dec(n):
    return F(P([(int(n)>>i)&1 for i in range(41)]))


seed_int = source["seed"] << 1
seed = dec(seed_int)
h0 = sum((seed ** (1 << (2*j)) for j in range(21)),F.zero())**2
bits = [i for i in range(9) if i != 5]
base = [dec((1 << bit) << 1)*dec(((1 << bit) << 1)^seed_int) for bit in bits]


def product(code, rotation):
    return sum((a**(1 << rotation) for j,a in enumerate(base) if code>>j&1),F.zero())


def quartic(x,p,rotation):
    h=h0**(1 << rotation)
    c=1+h
    b=x*w
    a=1+b**2
    d=x**2+w**2
    m=a*h+c*d
    return a*d*p**2+b*m*p+m**2+c*h*b**2


def bezout(f,g):
    fc=[f[i] for i in range(5)]
    gc=[g[i] for i in range(5)]
    B=[[F.zero() for _ in range(4)] for _ in range(4)]
    for m in range(1,5):
        for n in range(m):
            value=fc[m]*gc[n]+fc[n]*gc[m]
            for r in range(m-n):
                B[m-1-r][n+r]+=value
    assert all(B[i][j]==B[j][i] for i in range(4) for j in range(4))
    return B


def char2_det(B):
    d=[B[i][i] for i in range(4)]
    a=lambda i,j:B[i][j]
    pf=a(0,1)*a(2,3)+a(0,2)*a(1,3)+a(0,3)*a(1,2)
    return (d[0]*d[1]*d[2]*d[3]
            +a(0,1)**2*d[2]*d[3]+a(0,2)**2*d[1]*d[3]
            +a(0,3)**2*d[1]*d[2]+a(1,2)**2*d[0]*d[3]
            +a(1,3)**2*d[0]*d[2]+a(2,3)**2*d[0]*d[1]
            +pf**2)


rows=[]
for row in panel:
    f=quartic(dec(row["z"]),product(row["code3"],12),12)
    g=quartic(dec(fixture["public_reciprocal"]),product(row["code4"],24),24)
    assert f.degree()==g.degree()==4
    B=bezout(f,g)
    value=char2_det(B)
    ordinary=matrix(F,B).det()
    resultant=f.resultant(g)
    assert value==ordinary==resultant
    assert (value==0)==(row["kind"]=="positive")
    rows.append({"kind":row["kind"],"code3":row["code3"],"code4":row["code4"],
                 "zero":bool(value==0),"matrix_rank":int(matrix(F,B).rank())})

end=time.monotonic()
signal.alarm(0)
out={"status":"PASS_CHAR2_BEZOUT_RESULTANT_PANEL",
     "candidate_id":None,"curve_id":source["curve_id"],
     "panel_rows":len(rows),"positive_zero":sum(r["zero"] for r in rows if r["kind"]=="positive"),
     "control_zero":sum(r["zero"] for r in rows if r["kind"]!="positive"),
     "rows":rows,"wall_seconds":end-start,
     "self_maxrss_bytes":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
     "protocol_sha256":hashlib.sha256((HERE / "bezout_protocol.json").read_bytes()).hexdigest()}
(HERE / "bezout_result.json").write_text(json.dumps(out,sort_keys=True,indent=2)+"\n")
print(json.dumps({k:v for k,v in out.items() if k!="rows"},sort_keys=True))
