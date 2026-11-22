"""Build a free-code N41 five-pair circuit with the shared w eliminated."""
import hashlib
import json
import resource
import signal
import sys
import time
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
protocol=json.loads((HERE/"build_protocol.json").read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


for path,digest in protocol["sources"].items():
    assert sha(path)==digest,path
assert not (HERE/"formula.xcnf").exists()
assert protocol["curve_id"]=="EC1N41Ckb1h7d5e80d3c4d0"
signal.signal(signal.SIGALRM,lambda _s,_f: (_ for _ in ()).throw(TimeoutError("Bezout build cap")))
signal.alarm(protocol["wall_cap_seconds"])
start=time.monotonic()

sys.path.insert(0,str(ROOT/"n41_w8_quotient_first_pair_20261015"))
sys.path.insert(0,str(ROOT/"n41_w8_three_code_resultant_20261015"))
import circuit as previous
from tower_circuit import TowerCircuit,f4

source=json.loads(Path(protocol["states"]).read_text())
fixture=json.loads(Path(protocol["fixture"]).read_text())
panel=json.loads(Path(protocol["panel"]).read_text())
F=previous.F
N=41


def frob(value,k):
    for _ in range(k):
        value=F.square(value)
    return value


def xor(values):
    out=0
    for value in values:
        out^=value
    return out


bits=[i for i in range(9) if i!=5]
assert source["rotations"]==[0,0,12,12,24]
seed=source["seed"]<<1
h0=F.square(F.halftrace(seed))
base_products=[F.mul((1<<bit)<<1,((1<<bit)<<1)^seed) for bit in bits]
allowed={}
columns={}
for ordinal in range(71):
    state=source["states"][0][4*ordinal]
    mask=state["masks"][0]
    code=sum(((mask>>bit)&1)<<j for j,bit in enumerate(bits))
    assert code not in allowed
    assert xor(base_products[j] for j in range(8) if code>>j&1)==F.mul(mask<<1,(mask^source["seed"])<<1)
    allowed[code]=mask
    columns[code]=frozenset(state["columns"])
assert len(allowed)==71

circ=previous.old.KaratsubaCircuit(N,[0,3])
alg=previous.old.Algebra(circ,previous.Field(),dense_and_threshold=3000)
codes=[[circ.variable() for _ in range(8)] for _ in range(5)]
zbits=[circ.variable() for _ in range(N)]


def mismatch(wires,code):
    return [-wire if code>>j&1 else wire for j,wire in enumerate(wires)]


for slot in range(5):
    for forbidden in range(256):
        if forbidden not in allowed:
            circ.clauses.append(" ".join(map(str,mismatch(codes[slot],forbidden)))+" 0")
collision_clauses=0
for i in range(5):
    for j in range(i+1,5):
        for ac,acol in columns.items():
            for bc,bcol in columns.items():
                if acol&bcol:
                    circ.clauses.append(" ".join(map(str,mismatch(codes[i],ac)+mismatch(codes[j],bc)))+" 0")
                    collision_clauses+=1


def const(value):
    return alg.expression(((-1,value),))


add,mul,square=alg.add,alg.mul,alg.square
one=alg.one
zero=alg.zero
z=alg.from_bits(zbits)
relations=[]
for slot in range(3):
    rotation=source["rotations"][slot]
    h=frob(h0,rotation)
    c=1^h
    assert h and c
    cinv=F.inv(c)
    alpha=alg.expression(zip(codes[slot],[F.mul(frob(p,rotation),cinv) for p in base_products]))
    beta=const(F.mul(h,cinv))
    relations.append((alpha,beta))

a,b,c=[TowerCircuit.basis(alg,relations,i) for i in range(3)]
left=f4(a,b,c,TowerCircuit.constant(alg,relations,z),TowerCircuit.constant(alg,relations,one))
after_f4=time.monotonic()
for bit in range(3):
    left=left.norm(bit)
assert all(not expr.terms for expr in left.coeffs[1:])
after_left=time.monotonic()


def scale(expr,value):
    return mul(expr,const(value))


def code_product(slot):
    rot=source["rotations"][slot]
    return alg.expression(zip(codes[slot],[frob(v,rot) for v in base_products]))


def quartic_coeffs(x,p,rotation):
    h=frob(h0,rotation)
    c=1^h
    x2=square(x)
    x4=square(x2)
    p2=square(p)
    xp=mul(x,p)
    m0=add(const(h),scale(x2,c))
    m2=add(scale(x2,h),const(c))
    return [add(square(m0),mul(x2,p2)),
            mul(xp,m0),
            add(mul(add(one,x4),p2),scale(x2,F.mul(c,h))),
            mul(xp,m2),
            square(add(xp,m2))]


f=quartic_coeffs(z,code_product(3),12)
g=quartic_coeffs(const(fixture["public_reciprocal"]),code_product(4),24)
after_quartics=time.monotonic()
B=[[zero for _ in range(4)] for _ in range(4)]
contributions=[[[] for _ in range(4)] for _ in range(4)]
for m in range(1,5):
    for n in range(m):
        value=add(mul(f[m],g[n]),mul(f[n],g[m]))
        for r in range(m-n):
            contributions[m-1-r][n+r].append(value)
for i in range(4):
    for j in range(4):
        B[i][j]=add(*contributions[i][j])
assert all(B[i][j].terms==B[j][i].terms for i in range(4) for j in range(4))
after_bezout=time.monotonic()

d=[B[i][i] for i in range(4)]
at=lambda i,j:B[i][j]
pf=add(mul(at(0,1),at(2,3)),mul(at(0,2),at(1,3)),mul(at(0,3),at(1,2)))
diag_pairs={(i,j):mul(d[i],d[j]) for i in range(4) for j in range(i+1,4)}
terms=[mul(diag_pairs[(0,1)],diag_pairs[(2,3)]),square(pf)]
for i in range(4):
    for j in range(i+1,4):
        other=tuple(k for k in range(4) if k not in (i,j))
        terms.append(mul(square(at(i,j)),diag_pairs[other]))
det=add(*terms)
after_det=time.monotonic()


def output_zero(expr,assignment):
    return all((0 if wire==0 else 1 if wire==-1 else assignment[wire])==0 for wire in expr.bits())


checked=[]
for row in panel:
    initial={wire:(row["code3"]>>j)&1 for j,wire in enumerate(codes[3])}
    initial.update({wire:(row["code4"]>>j)&1 for j,wire in enumerate(codes[4])})
    for slot in range(3):
        mask=source["states"][slot][row["state_ids"][slot]]["masks"][0]
        code=sum(((mask>>bit)&1)<<j for j,bit in enumerate(bits))
        initial.update({wire:(code>>j)&1 for j,wire in enumerate(codes[slot])})
    initial.update({wire:(row["z"]>>j)&1 for j,wire in enumerate(zbits)})
    assignment=previous.old.complete_assignment(circ,initial)
    assert output_zero(left.coeffs[0],assignment)
    hit=output_zero(det,assignment)
    assert hit==(row["kind"]=="positive")
    checked.append({"kind":row["kind"],"control_index":row.get("control_index"),"det_zero":hit})
after_controls=time.monotonic()

circ.require_zero(left.coeffs[0].bits())
circ.require_zero(det.bits())
positive=panel[0]
initial={wire:(positive["code3"]>>j)&1 for j,wire in enumerate(codes[3])}
initial.update({wire:(positive["code4"]>>j)&1 for j,wire in enumerate(codes[4])})
for slot in range(3):
    mask=source["states"][slot][positive["state_ids"][slot]]["masks"][0]
    code=sum(((mask>>bit)&1)<<j for j,bit in enumerate(bits))
    initial.update({wire:(code>>j)&1 for j,wire in enumerate(codes[slot])})
initial.update({wire:(positive["z"]>>j)&1 for j,wire in enumerate(zbits)})
previous.old.check_assignment(circ,previous.old.complete_assignment(circ,initial))
after_constraints=time.monotonic()

circ.write(HERE/"formula.xcnf")
wire_record={"codes":codes,"left_reciprocal":zbits,
             "allowed_code_words":sorted(allowed),
             "source_mask_for_code":{str(k):v for k,v in allowed.items()},
             "public_reciprocal":fixture["public_reciprocal"]}
(HERE/"input_wires.json").write_text(json.dumps(wire_record,sort_keys=True,indent=2)+"\n")
finished=time.monotonic()
signal.alarm(0)
out={"status":"PASS_N41_TWO_QUARTIC_BEZOUT_CIRCUIT",
     "candidate_id":None,"curve_id":source["curve_id"],
     "public_point":fixture["public_point"],
     "and_gates":circ.and_count,"variables":circ.next_var-1,
     "clauses":len(circ.clauses),"native_xor_rows":len(circ.xors),
     "collision_clauses":collision_clauses,
     "formula_bytes":(HERE/"formula.xcnf").stat().st_size,
     "formula_sha256":sha(HERE/"formula.xcnf"),
     "input_wires_sha256":sha(HERE/"input_wires.json"),
     "controls_checked":checked,
     "phase_seconds":{"left_f4":after_f4-start,"left_norm":after_left-after_f4,
                      "quartics":after_quartics-after_left,
                      "bezout_matrix":after_bezout-after_quartics,
                      "determinant":after_det-after_bezout,
                      "panel_controls":after_controls-after_det,
                      "constraints_and_positive_replay":after_constraints-after_controls,
                      "serialization":finished-after_constraints},
     "wall_seconds":finished-start,
     "self_maxrss_bytes":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
     "protocol_sha256":sha(HERE/"build_protocol.json")}
(HERE/"build_result.json").write_text(json.dumps(out,sort_keys=True,indent=2)+"\n")
print(json.dumps({k:out[k] for k in ("status","and_gates","variables","clauses",
                                   "native_xor_rows","formula_bytes","wall_seconds",
                                   "self_maxrss_bytes")},sort_keys=True))
