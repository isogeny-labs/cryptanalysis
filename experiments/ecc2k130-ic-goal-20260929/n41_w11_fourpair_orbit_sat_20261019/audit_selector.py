"""Audit all 64 selector assignments in the frozen orbit circuit."""
import hashlib
import json
from pathlib import Path
import circuit_orbit

HERE=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
cfg=json.loads((HERE/'selector_protocol.json').read_text())
assert cfg['status']=='FROZEN_BEFORE_W11_ORBIT_SELECTOR_AUDIT'
for rec in cfg['sources'].values():assert sha(rec['path'])==rec['sha256']

target_line=Path(cfg['sources']['w11_input']['path']).read_text().splitlines()[1].split()
raw_x=int(target_line[2]);F=circuit_orbit.F
targets=[F.frob(F.inverse(raw_x),k) for k in range(41)]
captured=[]
original=circuit_orbit.KaratsubaCircuit.linear_element
def wrapper(self,variables,values,constant=0):
    result=original(self,variables,values,constant)
    captured.append((list(variables),list(values),list(result)))
    return result
circuit_orbit.KaratsubaCircuit.linear_element=wrapper
try:machine,wires,counts=circuit_orbit.build(targets,cfg['sources']['w11_input']['path'])
finally:circuit_orbit.KaratsubaCircuit.linear_element=original
matches=[row for row in captured if len(row[0])==41 and row[1]==targets]
assert len(matches)==1,(len(captured),len(matches))
choices,constants,target_bits=matches[0]
assert constants==targets and len(choices)==41 and len(target_bits)==41
choice_clause=' '.join(map(str,choices))+' 0'
assert machine.clauses.count(choice_clause)==1
definitions={int(out):('and',int(a),int(b)) for (a,b),out in machine.and_cache.items()}
for line in machine.xors:
    terms=[int(x) for x in line.split()[1:-1]]
    definitions[abs(terms[0])]=('xor',terms)

for code in range(64):
    memo={wire:(code>>j)&1 for j,wire in enumerate(wires['selector'])}
    def bit(wire):
        if wire==0:return 0
        if wire==-1:return 1
        if wire in memo:return memo[wire]
        d=definitions[wire]
        if d[0]=='and':out=bit(d[1])&bit(d[2])
        else:
            terms=d[1];out=int(terms[0]>0)
            for x in terms[1:]:out^=bit(abs(x))^int(x<0)
        memo[wire]=out
        return out
    selected=[i for i,w in enumerate(choices) if bit(w)]
    actual=sum(bit(w)<<j for j,w in enumerate(target_bits))
    if code<41:
        assert selected==[code] and actual==targets[code]
    else:
        assert selected==[] and actual==0
result={'status':'PASS_ALL_64_ORBIT_SELECTOR_CODES','candidate_id':None,
        'valid_codes':41,'excluded_codes':23,'target_count':len(set(targets)),
        'formula_counts':counts,'protocol_sha256':sha(HERE/'selector_protocol.json'),
        'script_sha256':sha(__file__)}
(HERE/'selector_result.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
print(json.dumps(result,sort_keys=True))
