"""Enforce the exact trace-zero projection at each all-seed pair/sum node."""
import hashlib,json,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
BASE=HERE.parent/'n131_w18_allseed_fourpair_20261012'
sys.path.insert(0,str(BASE))
from fourpair_v2 import build,check_assignment,field_config

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def trace(field,a):
    result=0
    for _ in range(field.n):result^=a;a=field.square(a)
    assert result in (0,1)
    return result

def trace_extend(circuit,wires,field):
    basis=[trace(field,1<<i) for i in range(field.n)]
    projected=[]
    for bits in [*wires['pair_outputs'],*wires['middle']]:
        parity=circuit.xor(wire for wire,t in zip(bits,basis) if t)
        circuit.require_zero([parity])
        projected.append(parity)
    return {'trace_basis_nonzero':sum(basis),'trace_rows':len(projected),
            'trace_node_wires':projected}

def main():
    protocol=json.loads((HERE/'protocol.json').read_text())
    paths={'source':HERE/'trace_circuit.py','base_builder':BASE/'fourpair_v2.py',
           'fixture':BASE/'n41_diagonal/control_fixture.json',
           'base_protocol':BASE/'v2_protocol.json'}
    assert {k:sha(v) for k,v in paths.items()}==protocol['sha256']
    fixture=json.loads(paths['fixture'].read_text())
    field,_,rotations=field_config('n41')
    start=time.monotonic_ns()
    circuit,wires,meta=build('n41',int(fixture['target_reciprocal']))
    before={'variables':circuit.next_var-1,'clauses':len(circuit.clauses),'xor_rows':len(circuit.xors)}
    assert trace(field,int(fixture['target_reciprocal']))==0
    trace_meta=trace_extend(circuit,wires,field)
    built=time.monotonic_ns()
    check=check_assignment(circuit,wires,fixture,field,rotations)
    checked=time.monotonic_ns()
    formula=HERE/'ordinary.xcnf';assert not formula.exists();circuit.write(formula)
    end=time.monotonic_ns()
    result={'status':'PASS_N41_TRACE_PROJECTED_PUBLIC_FORMULA','candidate_id':None,
            'curve_id':'EC1N41Ckb1h7d5e80d3c4d0','public_target':fixture['public_target'],
            'predecessor':before,'variables':circuit.next_var-1,
            'clauses':len(circuit.clauses),'xor_rows':len(circuit.xors),
            'formula_bytes':formula.stat().st_size,'formula_sha256':sha(formula),
            'build_ns':built-start,'check_ns':checked-built,'write_ns':end-checked,
            'control_check':check,'trace':trace_meta,'base_metadata':meta,
            'protocol_sha256':sha(HERE/'protocol.json')}
    (HERE/'formula_result.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(result['status'],result['variables'],flush=True)
if __name__=='__main__':main()
