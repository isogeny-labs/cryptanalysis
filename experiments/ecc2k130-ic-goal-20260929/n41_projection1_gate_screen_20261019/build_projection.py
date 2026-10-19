"""Compile frozen field-equation projections of two resultant nodes."""
import hashlib
import json
import sys
import time
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path[:0] = [str(ROOT/'n41_w9_lazy_source_20261017'),
                str(ROOT/'n131_w20_selector_elimination_v2_20261013')]
import circuit as design
import selector


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


protocol = json.loads((HERE/'build_protocol.json').read_text())
for path, digest in protocol['sources'].items():
    assert sha(path) == digest, path
assert not (HERE/'build_result.json').exists()
source = json.loads(Path(protocol['source_states']).read_text())
projection = protocol['projected_field_bits']
assert len(projection)==len(set(projection))==protocol['bits_per_resultant']
assert all(0<=bit<41 for bit in projection)
F = design.F
S = PolynomialRing(GF(2), 'u')
u = S.gen()
sage_field = GF(2**41, name='u', modulus=u**41+u**3+1)
E = EllipticCurve(sage_field, [1, 0, 0, 0, 1])


def dec(word):
    return sage_field(S([(int(word) >> bit) & 1 for bit in range(41)]))


def enc(value):
    return sum(int(c) << bit for bit,c in enumerate(value.polynomial().list()))


def point(row):
    return E(*map(dec,row['point']))


def reciprocal(group_point):
    assert group_point and group_point[0]
    return enc(1/group_point[0])


circ = design.KaratsubaCircuit(design.N,design.TAPS)
alg = design.Algebra(circ,F,dense_and_threshold=3000)


def const(value):
    return alg.expression(((-1,value),))


def scale(expr,value):
    return alg.expression((wire,F.mul(basis,value)) for wire,basis in expr.terms)


def factor_gate(p,q,t,C,H,D,J):
    """Impose the factored nested resultant, dropping its nonzero C^3 scale."""
    assert C and D
    t2,t4=alg.square(t),None
    t4=alg.square(t2)
    q2=alg.square(q)
    U0=alg.add(const(J),scale(t2,D))
    U2=alg.add(const(D),scale(t2,J))
    q2t2=alg.mul(q2,t2)
    qt=alg.mul(q,t)
    K0=alg.add(alg.square(U0),q2t2)
    K1=alg.mul(qt,U0)
    K2=alg.add(q2,alg.mul(q2,t4),scale(t2,F.mul(D,J)))
    K3=alg.mul(qt,U2)
    K4=alg.add(alg.square(U2),q2t2)
    alpha=scale(p,F.inverse(C))
    beta=F.mul(H,F.inverse(C))
    alpha2=alg.square(alpha)
    alpha3=alg.mul(alpha,alpha2)
    L=alg.add(K1,alg.mul(K2,alpha),
              alg.mul(K3,alg.add(alpha2,const(beta))),
              alg.mul(K4,alpha3))
    M=alg.add(K0,scale(K2,beta),
              alg.mul(K3,scale(alpha,beta)),
              alg.mul(K4,alg.add(scale(alpha2,beta),const(F.square(beta)))))
    LM=alg.mul(L,M)
    residual=alg.add(scale(alg.square(M),C),alg.mul(p,LM),
                     scale(alg.square(L),H))
    bits=residual.bits()
    circ.require_zero([bits[index] for index in projection])


def s3(a,b,z):
    ab=alg.mul(a,b)
    abz=alg.mul(ab,z)
    circ.require_zero(alg.add(alg.square(abz),abz,
                              alg.square(alg.add(a,b)),alg.square(z)).bits())


columns=[]
code_wires=[]
products=[]
for slot,rotation in enumerate(design.ROTATIONS):
    bits=[circ.variable() for _ in design.BITS]
    code_wires.append(bits)
    product=alg.expression((wire,F.frob(basis,rotation))
                           for wire,basis in zip(bits,design.PB))
    products.append(product)
    table={}
    for row in source['states'][slot]:
        mask=row['masks'][0]
        code=sum(((mask>>bit)&1)<<i for i,bit in enumerate(design.BITS))
        assert table.setdefault(code,set(row['columns']))==set(row['columns'])
    assert set(table)==design.ALLOWED_CODES
    columns.append(table)
    for forbidden in range(1<<len(design.BITS)):
        if forbidden not in design.ALLOWED_CODES:
            circ.clauses.append(' '.join(str(-wire if forbidden>>i&1 else wire)
                                         for i,wire in enumerate(bits))+' 0')

column_conflicts=0
for i in range(5):
    for j in range(i+1,5):
        for code_a,col_a in columns[i].items():
            for code_b,col_b in columns[j].items():
                if col_a.isdisjoint(col_b):
                    continue
                lits=[-wire if code_a>>bit&1 else wire
                      for bit,wire in enumerate(code_wires[i])]
                lits += [-wire if code_b>>bit&1 else wire
                         for bit,wire in enumerate(code_wires[j])]
                circ.clauses.append(' '.join(map(str,lits))+' 0')
                column_conflicts+=1

z_wires={name:[circ.variable() for _ in range(41)]
         for name in ('left','right','middle','pair2')}
for bits in z_wires.values():
    circ.clauses.append(' '.join(map(str,bits))+' 0')
z={name:alg.from_bits(bits) for name,bits in z_wires.items()}
C,H=design.C,design.H
factor_gate(products[0],products[1],z['left'],
            C,H,F.frob(C,6),F.frob(H,6))
factor_gate(products[3],products[4],z['right'],
            F.frob(C,18),F.frob(H,18),F.frob(C,24),F.frob(H,24))
pair2=alg.add(scale(alg.square(z['pair2']),F.frob(C,12)),
              alg.mul(products[2],z['pair2']),const(F.frob(H,12)))
circ.require_zero(pair2.bits())
s3(z['left'],z['pair2'],z['middle'])
target_point=E(*map(dec,protocol['oriented_target_point']))
target_reciprocal=reciprocal(target_point)
s3(z['middle'],z['right'],const(target_reciprocal))

counts={'variables':circ.next_var-1,'clauses':len(circ.clauses),
        'xor_rows':len(circ.xors),'and_gates':circ.and_count,
        'sparse_mul_calls':alg.sparse_mul_calls,
        'generic_mul_calls':alg.generic_mul_calls,
        'column_conflict_clauses':column_conflicts}
formula=HERE/'fivepair_projection.xcnf'
assert not formula.exists()
started=time.monotonic()
circ.write(formula)
write_wall=time.monotonic()-started

ids=protocol['reference_witness_state_ids']
points=[point(source['states'][slot][state_id])
        for slot,state_id in enumerate(ids)]
assert sum(points,E(0))==target_point
partial={'left':points[0]+points[1],
         'right':points[3]+points[4],
         'middle':points[0]+points[1]+points[2],
         'pair2':points[2]}
assignment={}
for slot,state_id in enumerate(ids):
    mask=source['states'][slot][state_id]['masks'][0]
    code=sum(((mask>>bit)&1)<<i for i,bit in enumerate(design.BITS))
    assignment.update({wire:(code>>i)&1
                       for i,wire in enumerate(code_wires[slot])})
for name,group_point in partial.items():
    value=reciprocal(group_point)
    assignment.update({wire:(value>>i)&1
                       for i,wire in enumerate(z_wires[name])})
completed=selector.old.complete_assignment(circ,assignment)
control=selector.old.check_assignment(circ,completed)
assert control=={'clauses':counts['clauses'],
                'native_xor_rows':counts['xor_rows']}

result={'status':'PASS_N41_PROJECTED_FIVEPAIR_BUILD','candidate_id':None,
        'curve_id':protocol['curve_id'],'counts':counts,
        'projected_field_bits':projection,
        'formula_sha256':sha(formula),'formula_bytes':formula.stat().st_size,
        'target_reciprocal':target_reciprocal,
        'reference_witness_state_ids':ids,
        'reference_control':control,
        'input_code_wires':code_wires,'z_wires':z_wires,
        'write_wall_seconds':write_wall,
        'protocol_sha256':sha(HERE/'build_protocol.json')}
(HERE/'build_result.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
print(json.dumps({'status':result['status'],'counts':counts,
                  'formula_bytes':result['formula_bytes'],
                  'write_wall_seconds':write_wall}))
