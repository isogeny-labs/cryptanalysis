"""Build the N41 five-pair circuit with a two-quadratic final root gate."""
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
signal.signal(signal.SIGALRM,lambda _s,_f: (_ for _ in ()).throw(TimeoutError("kernel build cap")))
signal.alarm(protocol["wall_cap_seconds"])
start=time.monotonic()

sys.path.insert(0,str(ROOT/"n41_w8_quotient_first_pair_20261015"))
sys.path.insert(0,str(ROOT/"n41_w8_three_code_resultant_20261015"))
import circuit as previous
from tower_circuit import TowerCircuit,f4

source=json.loads(Path(protocol["states"]).read_text())
fixture=json.loads(Path(protocol["fixture"]).read_text())
panel=json.loads(Path(protocol["panel"]).read_text())
joint=json.loads(Path(protocol["join_rows"]).read_text())
assert len(joint["rows"])==len(panel)
assert all(a["state_ids"]==b["state_ids"] for a,b in zip(joint["rows"],panel))
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
root_bits=[circ.variable() for _ in range(N)]
pair_bits=[circ.variable() for _ in range(N)]
pair3_bits=[circ.variable() for _ in range(N)]
right_sum_bits=[circ.variable() for _ in range(N)]


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
after_quartics=time.monotonic()
root=alg.from_bits(root_bits)
pair_root=alg.from_bits(pair_bits)
pair3_root=alg.from_bits(pair3_bits)
right_sum=alg.from_bits(right_sum_bits)


def evaluate_quartic(coeffs):
    value=coeffs[4]
    for index in (3,2,1,0):
        value=add(mul(value,root),coeffs[index])
    return value


preceding_quartic=evaluate_quartic(f)
after_evaluation=time.monotonic()
h4=frob(h0,24)
c4=1^h4
assert c4
p4=code_product(4)
pair_gate=add(scale(square(pair_root),c4),mul(p4,pair_root),const(h4))
t=fixture["public_reciprocal"]
tu=scale(pair_root,t)
s3_a=add(one,square(tu))
s3_b=tu
s3_d=add(const(F.square(t)),square(pair_root))
s3_gate=add(mul(s3_a,square(root)),mul(s3_b,root),s3_d)
after_quadratics=time.monotonic()


def s3(u,v,w):
    uv=mul(u,v)
    return add(add(mul(add(one,square(uv)),square(w)),mul(uv,w)),
               add(square(u),square(v)))


h3=frob(h0,12)
c3=1^h3
pair3_gate=add(scale(square(pair3_root),c3),
               mul(code_product(3),pair3_root),const(h3))
preceding_s3_gate=s3(z,pair3_root,root)
right_sum_gate=s3(pair3_root,pair_root,right_sum)
joint_target_gate=s3(z,right_sum,const(t))
after_joint=time.monotonic()


def initial_for(row):
    initial={wire:(row["code3"]>>j)&1 for j,wire in enumerate(codes[3])}
    initial.update({wire:(row["code4"]>>j)&1 for j,wire in enumerate(codes[4])})
    for slot in range(3):
        mask=source["states"][slot][row["state_ids"][slot]]["masks"][0]
        code=sum(((mask>>bit)&1)<<j for j,bit in enumerate(bits))
        initial.update({wire:(code>>j)&1 for j,wire in enumerate(codes[slot])})
    initial.update({wire:(row["z"]>>j)&1 for j,wire in enumerate(zbits)})
    initial.update({wire:(row["w"]>>j)&1 for j,wire in enumerate(root_bits)})
    final_state=source["states"][4][row["state_ids"][4]]
    pair_value=F.inv(final_state["point"][0])
    initial.update({wire:(pair_value>>j)&1 for j,wire in enumerate(pair_bits)})
    join_row=joint["rows"][panel.index(row)]
    initial.update({wire:(join_row["pair3_reciprocal"]>>j)&1
                    for j,wire in enumerate(pair3_bits)})
    initial.update({wire:(join_row["right_sum_reciprocal"]>>j)&1
                    for j,wire in enumerate(right_sum_bits)})
    return initial


def output_zero(expr,assignment):
    return all((0 if wire==0 else 1 if wire==-1 else assignment[wire])==0 for wire in expr.bits())


checked=[]
for row,join_row in zip(panel,joint["rows"]):
    assignment=previous.old.complete_assignment(circ,initial_for(row))
    assert output_zero(left.coeffs[0],assignment)
    pair_zero=output_zero(pair_gate,assignment)
    s3_zero=output_zero(s3_gate,assignment)
    hit=output_zero(preceding_quartic,assignment)
    assert pair_zero and s3_zero and hit==(row["kind"]=="positive")
    pair3_zero=output_zero(pair3_gate,assignment)
    preceding_s3_zero=output_zero(preceding_s3_gate,assignment)
    right_sum_zero=output_zero(right_sum_gate,assignment)
    joint_target_zero=output_zero(joint_target_gate,assignment)
    assert pair3_zero and right_sum_zero
    assert preceding_s3_zero==join_row["preceding_link_zero"]
    assert joint_target_zero==join_row["target_link_zero"]
    checked.append({"kind":row["kind"],"control_index":row.get("control_index"),
                    "pair_zero":pair_zero,"s3_zero":s3_zero,"preceding_zero":hit,
                    "pair3_zero":pair3_zero,"preceding_s3_zero":preceding_s3_zero,
                    "right_sum_zero":right_sum_zero,"joint_target_zero":joint_target_zero})
after_controls=time.monotonic()

circ.require_zero(left.coeffs[0].bits())
for expr in (preceding_quartic,pair_gate,s3_gate,pair3_gate,
             preceding_s3_gate,right_sum_gate,joint_target_gate):
    circ.require_zero(expr.bits())
positive=panel[0]
previous.old.check_assignment(circ,previous.old.complete_assignment(circ,initial_for(positive)))
after_constraints=time.monotonic()

circ.write(HERE/"formula.xcnf")
wire_record={"codes":codes,"left_reciprocal":zbits,
             "root_witness":root_bits,
             "final_pair_reciprocal":pair_bits,
             "preceding_pair_reciprocal":pair3_bits,
             "right_two_pair_reciprocal":right_sum_bits,
             "allowed_code_words":sorted(allowed),
             "source_mask_for_code":{str(k):v for k,v in allowed.items()},
             "public_reciprocal":fixture["public_reciprocal"]}
(HERE/"input_wires.json").write_text(json.dumps(wire_record,sort_keys=True,indent=2)+"\n")
finished=time.monotonic()
signal.alarm(0)
out={"status":"PASS_N41_JOINT_RIGHT_S3_CIRCUIT",
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
                      "quartic_evaluation":after_evaluation-after_quartics,
                      "final_pair_quadratics":after_quadratics-after_evaluation,
                      "joint_right_s3":after_joint-after_quadratics,
                      "panel_controls":after_controls-after_joint,
                      "constraints_and_positive_replay":after_constraints-after_controls,
                      "serialization":finished-after_constraints},
     "wall_seconds":finished-start,
     "self_maxrss_bytes":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
     "protocol_sha256":sha(HERE/"build_protocol.json")}
(HERE/"build_result.json").write_text(json.dumps(out,sort_keys=True,indent=2)+"\n")
print(json.dumps({k:out[k] for k in ("status","and_gates","variables","clauses",
                                   "native_xor_rows","formula_bytes","wall_seconds",
                                   "self_maxrss_bytes")},sort_keys=True))
