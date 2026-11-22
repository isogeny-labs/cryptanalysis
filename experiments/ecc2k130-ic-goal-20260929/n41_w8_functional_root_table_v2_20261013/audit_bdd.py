"""Exhaustively evaluate the generated Boolean root decision diagram."""
import hashlib,json
from pathlib import Path
import circuit
HERE=Path(__file__).resolve().parent
p=json.loads((HERE/'bdd_protocol.json').read_text())
for path,digest in p['sources'].items():
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==digest,path
e=circuit.projector();roots=circuit.root_table(e);F=circuit.F
circ=circuit.old.KaratsubaCircuit(circuit.N,[0,3])
inputs=[circ.variable() for _ in range(7)];branch=circ.variable();cache={}
root_bits=[circuit.bdd(circ,inputs,[((roots[code][0]>>i)&1) if code in roots else 0
                                   for code in range(128)],cache)
           for i in range(circuit.N)]
h2=F.square(F.halftrace(e['seed']));constant=1^h2
basis=[F.mul(v,F.inv(constant)) for v in e['basis']]
delta_bits=circ.linear_element(inputs,basis)
outputs=[circ.xor((root_bits[i],circ.and_(branch,delta_bits[i]))) for i in range(circuit.N)]
checked=0
for code,expected in roots.items():
    for choice in (0,1):
        initial={wire:(code>>j)&1 for j,wire in enumerate(inputs)}
        initial[branch]=choice
        values=circuit.old.complete_assignment(circ,initial)
        got=sum(values[wire]<<i for i,wire in enumerate(outputs) if wire>0)
        # The exact 0 and 1 constants are supported by the evaluator too.
        got=0
        for i,wire in enumerate(outputs):
            bit=1 if wire==-1 else 0 if wire==0 else values[wire]
            got|=bit<<i
        assert got==expected[choice],(code,choice,got,expected[choice])
        checked+=1
result={'status':'PASS_EXHAUSTIVE_N41_FUNCTIONAL_ROOT_BDD',
        'valid_pair_codes':len(roots),'root_branches_checked':checked,
        'bdd_unique_nodes':len(cache),'variables':circ.next_var-1,
        'and_gates':circ.and_count,'native_xor_rows':len(circ.xors),
        'formula_sha256':hashlib.sha256((HERE/'public.xcnf').read_bytes()).hexdigest()}
with (HERE/'bdd_result.json').open('x') as out:
    json.dump(result,out,sort_keys=True,indent=2);out.write('\n')
print(result['status'],checked,len(cache))
