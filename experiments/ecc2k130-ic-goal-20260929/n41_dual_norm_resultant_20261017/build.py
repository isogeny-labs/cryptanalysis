"""Eliminate one partial coordinate by norming against the public S3."""
import hashlib
import importlib.util
import json
import resource
import sys
import time
from pathlib import Path

D=Path(__file__).resolve().parent
ROOT=D.parent
SOURCE=ROOT/'n41_w8_quotient_first_pair_20261015'
NORM=ROOT/'n41_three_code_nested_norm_20261015'
WITNESS=ROOT/'n41_sixpair_shared_target_20261017'/'join_audit_result.json'
sys.path.insert(0,str(SOURCE))
sys.path.insert(0,str(NORM))
import circuit
from three_norm import Ops,three_source_norm
spec=importlib.util.spec_from_file_location('old_n41_builder',SOURCE/'build.py')
old_build=importlib.util.module_from_spec(spec);spec.loader.exec_module(old_build)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bind(initial,wires,value):
    for i,wire in enumerate(wires):initial[wire]=(value>>i)&1


def nonzero_inverse(value,alg):
    """x^(2^41-2), valid when the explicit x != 0 clause holds."""
    power=value
    for _ in range(1,40):
        power=alg.mul(alg.square(power),value)
    return alg.square(power)


def build_formula():
    geometry=circuit.geometry()
    e=circuit.projector()
    field=circuit.F
    witness=json.loads(WITNESS.read_text())
    assert witness['status'].startswith('PASS')
    assert geometry['curve_id']=='EC1N41Ckb1h7d5e80d3c4d0'
    assert len(witness['pair_rows'])==6
    target=witness['raw_target']
    assert target[0]
    q=field.inv(target[0])
    circ=circuit.old.KaratsubaCircuit(41,[0,3])
    alg=circuit.old.Algebra(circ,circuit.Field(),dense_and_threshold=3000)
    ops=Ops(alg.zero,alg.one,alg.add,alg.mul)
    ops.square=alg.square
    code_wires=[[circ.variable() for _ in range(7)] for _ in range(6)]
    middle_wires=[circ.variable() for _ in range(41)]
    allowed_codes={sum(((mask>>bit)&1)<<j for j,bit in enumerate(e['bits'])):mask
                   for mask in geometry['permitted_canonical_a']}
    assert len(allowed_codes)==40
    for wires in code_wires:
        for forbidden in range(128):
            if forbidden in allowed_codes:continue
            circ.clauses.append(' '.join(str(-wire if forbidden>>j&1 else wire)
                                         for j,wire in enumerate(wires))+' 0')
    columns={int(k):v for k,v in geometry['mask_columns'].items()}
    source_columns={code:{columns[mask],columns[mask^geometry['fixed_seed_sum_code']]}
                    for code,mask in allowed_codes.items()}
    def mismatch(wires,code):
        return [(-wire if code>>j&1 else wire) for j,wire in enumerate(wires)]
    collision_clauses=0
    for i in range(6):
        for j in range(i+1,6):
            for left,lc in source_columns.items():
                for right,rc in source_columns.items():
                    if not lc&rc:continue
                    circ.clauses.append(' '.join(map(str,
                        mismatch(code_wires[i],left)+mismatch(code_wires[j],right)))+' 0')
                    collision_clauses+=1
    h=field.square(field.halftrace(e['seed']))
    coefficients=[]
    for slot in range(6):
        rotation=geometry['rotations'][slot]
        hs=circuit.frob(h,rotation)
        leading=1^hs
        assert leading
        inverse=field.inv(leading)
        alpha=alg.expression((wire,field.mul(circuit.frob(value,rotation),inverse))
                             for wire,value in zip(code_wires[slot],e['basis']))
        beta=alg.expression(((-1,field.mul(hs,inverse)),))
        coefficients.append((alpha,beta))
    t=alg.from_bits(middle_wires)
    first=three_source_norm(*(value for pair in coefficients[:3] for value in pair),t,ops)
    circ.require_zero(first.bits())
    target_const=alg.expression(((-1,q),))
    tq=alg.mul(t,target_const)
    lead_root=alg.add(alg.one,tq)
    circ.clauses.append(' '.join(map(str,lead_root.bits()))+' 0')
    inverse=nonzero_inverse(lead_root,alg)
    inverse_square=alg.square(inverse)
    alpha=alg.mul(tq,inverse_square)
    beta=alg.mul(alg.square(alg.add(t,target_const)),inverse_square)
    zero,one=alg.zero,alg.one
    qadd=lambda x,y:(alg.add(x[0],y[0]),alg.add(x[1],y[1]))
    def qmul(x,y):
        a,b=x;c,d=y
        bd=alg.mul(b,d)
        return (alg.add(alg.mul(a,c),alg.mul(beta,bd)),
                alg.add(alg.mul(a,d),alg.mul(b,c),alg.mul(alpha,bd)))
    def qsquare(x):
        a,b=x
        b2=alg.square(b)
        return (alg.add(alg.square(a),alg.mul(beta,b2)),alg.mul(alpha,b2))
    quadops=Ops((zero,zero),(one,zero),qadd,qmul)
    quadops.square=qsquare
    lift=lambda x:(x,zero)
    second=three_source_norm(*(lift(value) for pair in coefficients[3:]
                               for value in pair),(zero,one),quadops)
    second_norm=alg.add(alg.square(second[0]),
                        alg.mul(alpha,alg.mul(second[0],second[1])),
                        alg.mul(beta,alg.square(second[1])))
    circ.require_zero(second_norm.bits())
    circ.clauses.append(' '.join(map(str,middle_wires))+' 0')
    metadata={'target_reciprocal':q,'allowed_code_count':len(allowed_codes),
              'collision_clauses':collision_clauses,
              'code_wires':code_wires,'middle_wires':middle_wires,
              'source_coefficients':coefficients,'elimination':'right_partial'}
    return circ,metadata


def witness_assignment(meta):
    witness=json.loads(WITNESS.read_text())
    e=circuit.projector()
    points=[];initial={}
    for slot,row in enumerate(witness['pair_rows']):
        code=sum(((row['masks'][0]>>bit)&1)<<j for j,bit in enumerate(e['bits']))
        bind(initial,meta['code_wires'][slot],code)
        points.append(tuple(row['raw_sum']))
    add=old_build.prior.add
    left=add(add(points[0],points[1]),points[2])
    right=add(add(points[3],points[4]),points[5])
    assert left is not None and right is not None
    assert add(left,right)==tuple(witness['raw_target'])
    assert left[0] and right[0]
    partials=[circuit.F.inv(left[0]),circuit.F.inv(right[0])]
    bind(initial,meta['middle_wires'],partials[0])
    return initial,partials


def main():
    protocol=json.loads((D/'protocol.json').read_text())
    assert protocol['producer_sha256']==sha(Path(__file__))
    assert all(sha(Path(path))==digest for path,digest in protocol['sources'].items())
    start=time.monotonic()
    formula,meta=build_formula()
    built=time.monotonic()
    initial,partials=witness_assignment(meta)
    witness_check=circuit.old.check_assignment(
        formula,circuit.old.complete_assignment(formula,initial))
    checked=time.monotonic()
    assert witness_check
    formula_path=D/'public.xcnf'
    formula.write(formula_path)
    written=time.monotonic()
    result={'status':'N41_DUAL_NORM_RESULTANT_CONTROL_PASS',
            'protocol_sha256':sha(D/'protocol.json'),
            'target_reciprocal':meta['target_reciprocal'],
            'witness_partial_reciprocals':partials,
            'elimination':meta['elimination'],
            'allowed_code_count':meta['allowed_code_count'],
            'collision_clauses':meta['collision_clauses'],
            'and_gates':formula.and_count,
            'variables':formula.next_var-1,
            'clauses':len(formula.clauses),
            'xor_rows':len(formula.xors),
            'witness_assignment_check':witness_check,
            'formula_sha256':sha(formula_path),
            'formula_bytes':formula_path.stat().st_size,
            'phase_s':{'build':built-start,'control':checked-built,
                       'serialize':written-checked},
            'peak_self_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    (D/'build_result.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ('status','and_gates','variables',
                                           'clauses','xor_rows','formula_bytes','phase_s')},
                     sort_keys=True))


if __name__=='__main__':main()
