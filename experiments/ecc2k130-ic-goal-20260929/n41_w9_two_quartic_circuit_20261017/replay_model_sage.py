"""Independently replay a SAT model as a signed five-pair curve relation."""
import hashlib
import itertools
import json
import time
from pathlib import Path

from sage.all import GF,PolynomialRing

HERE=Path(__file__).resolve().parent
p=json.loads((HERE/"replay_protocol.json").read_text())
for path,digest in p["sources"].items():
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==digest,path
assert not (HERE/"replay_result.json").exists()
started=time.monotonic()
query=json.loads((HERE/"query_result.json").read_text())
assert query["status"]=="SAT_MODEL_UNVERIFIED"
source=json.loads(Path(p["states"]).read_text())
fixture=json.loads(Path(p["fixture"]).read_text())
wires=json.loads((HERE/"input_wires.json").read_text())
lines=(HERE/"solver.stdout").read_text().splitlines()
assert any(line.strip()=="s SATISFIABLE" for line in lines)
assignment={}
for line in lines:
    if not line.startswith("v "):
        continue
    for token in line.split()[1:]:
        lit=int(token)
        if lit:
            assert abs(lit) not in assignment or assignment[abs(lit)]==(lit>0)
            assignment[abs(lit)]=lit>0
required={value for row in wires["codes"] for value in row}|set(wires["left_reciprocal"])
assert required <= assignment.keys()
codes=[sum(int(assignment[wire])<<j for j,wire in enumerate(row))
       for row in wires["codes"]]
z=sum(int(assignment[wire])<<j for j,wire in enumerate(wires["left_reciprocal"]))
assert all(code in wires["allowed_code_words"] for code in codes)

P=PolynomialRing(GF(2),"u")
u=P.gen()
F=GF(2**41,name="u",modulus=u**41+u**3+1)


def dec(n):
    return F(P([(int(n)>>i)&1 for i in range(41)]))


def point(raw):
    return dec(raw[0]),dec(raw[1])


def add(A,B):
    if A is None:return B
    if B is None:return A
    x1,y1=A;x2,y2=B
    if x1==x2:
        if y1+y2==x1:return None
        assert A==B and x1
        slope=x1+y1/x1
        x3=slope**2+slope
        y3=x1**2+(slope+1)*x3
    else:
        slope=(y1+y2)/(x1+x2)
        x3=slope**2+slope+x1+x2
        y3=slope*(x1+x3)+x3+y1
    return x3,y3


bits=[i for i in range(9) if i!=5]


def code_of(state):
    mask=state["masks"][0]
    return sum(((mask>>bit)&1)<<j for j,bit in enumerate(bits))


states=[]
for slot,code in enumerate(codes):
    choices=[(sid,state,point(state["point"]))
             for sid,state in enumerate(source["states"][slot]) if code_of(state)==code]
    assert len(choices)==4
    states.append(choices)

Q=point(fixture["public_point"])
matches=[]
for combination in itertools.product(*states):
    cols=[col for _,state,_ in combination for col in state["columns"]]
    if len(cols)!=len(set(cols)):
        continue
    first=None
    for _,_,value in combination[:3]:
        first=add(first,value)
    if first is None or not first[0] or 1/first[0]!=dec(z):
        continue
    total=first
    for _,_,value in combination[3:]:
        total=add(total,value)
    if total==Q:
        matches.append([sid for sid,_,_ in combination])

out={"status":"PASS_INDEPENDENT_SAGE_MODEL_GROUP_REPLAY" if matches else "SAT_MODEL_GROUP_REPLAY_FAILED",
     "candidate_id":None,"curve_id":source["curve_id"],
     "codes":codes,"preceding_reciprocal":z,
     "source_state_id_witnesses":matches,
     "independent_group_matches":len(matches),
     "public_point":fixture["public_point"],
     "source_choices_checked":4**5,
     "arithmetic_wall_seconds":time.monotonic()-started,
     "protocol_sha256":hashlib.sha256((HERE/"replay_protocol.json").read_bytes()).hexdigest()}
(HERE/"replay_result.json").write_text(json.dumps(out,sort_keys=True,indent=2)+"\n")
print(json.dumps(out,sort_keys=True))
