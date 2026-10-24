"""Replay every exported reciprocal by explicit binary-curve x addition."""
import hashlib
import json
import resource
import signal
import time
from pathlib import Path

from sage.all import GF, PolynomialRing

HERE=Path(__file__).resolve().parent
protocol_path=HERE/"audit_protocol.json"
protocol=json.loads(protocol_path.read_text())
for path,digest in protocol["sources"].items():
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==digest,path
assert not (HERE/"audit_result.json").exists()
signal.signal(signal.SIGALRM,lambda _s,_f:(_ for _ in ()).throw(TimeoutError("arithmetic audit wall cap")))
signal.alarm(protocol["wall_cap_seconds"])
started=time.monotonic()
S=PolynomialRing(GF(2),"u")
u=S.gen()
F=GF(2**41,name="u",modulus=u**41+u**3+1)


def dec(word):
    return F(S([(int(word)>>i)&1 for i in range(41)]))


def enc(value):
    return sum(int(c)<<i for i,c in enumerate(value.polynomial().list()))


source=json.loads(Path(protocol["states"]).read_text())
export=json.loads((HERE/"export_result.json").read_text())
bits=[0,1,2,3,4,6,7,8]


def code(state):
    return sum(((state["masks"][0]>>bit)&1)<<j for j,bit in enumerate(bits))


groups=[]
for slot in (0,1):
    indexed={}
    for state in source["states"][slot]:
        x,y=map(dec,state["point"])
        assert y*y+x*y==x*x*x+1
        indexed.setdefault(code(state),[]).append((x,y))
    groups.append(indexed)
checked=0
doublings=0
for row in export["rows"]:
    c0,c1=row["codes"]
    expected=row["reciprocal_x"]
    k=0
    for x1,y1 in groups[0][c0]:
        for x2,y2 in groups[1][c1]:
            if x1==x2:
                assert y1==y2 and x1
                lam=x1+y1/x1
                x3=lam*lam+lam
                doublings+=1
            else:
                lam=(y1+y2)/(x1+x2)
                x3=lam*lam+lam+x1+x2
            assert x3 and enc(~x3)==expected[k],(c0,c1,k)
            checked+=1
            k+=1
    assert k==16
signal.alarm(0)
result={"status":"PASS_INDEPENDENT_N41_TWO_CODE_X_AUDIT",
        "candidate_id":None,"curve_id":protocol["curve_id"],
        "families":len(export["rows"]),"assignments":checked,
        "doublings":doublings,"wall_seconds":time.monotonic()-started,
        "self_maxrss_raw":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "protocol_sha256":hashlib.sha256(protocol_path.read_bytes()).hexdigest()}
(HERE/"audit_result.json").write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
print(json.dumps(result),flush=True)
