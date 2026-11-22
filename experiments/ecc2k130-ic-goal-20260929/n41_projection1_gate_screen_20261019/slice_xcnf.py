"""Remove dead AND/XOR definitions from a frozen projected XCNF circuit."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


protocol=json.loads((HERE/'slice_protocol.json').read_text())
for path,digest in protocol['sources'].items():
    assert sha(path)==digest,path
assert not (HERE/'slice_result.json').exists()
lines=(HERE/'fivepair_projection.xcnf').read_text().splitlines()
header=lines[0].split()
assert header[:2]==['p','cnf']
old_n=int(header[2])
assert len(lines)-1==int(header[3])
and_def={}
xor_def={}
constraints=[]
i=1
while i<len(lines):
    line=lines[i]
    if line.startswith('x '):
        words=line.split()
        assert words[-1]=='0' and len(words)>=4
        out=abs(int(words[1]))
        deps=tuple(abs(int(word)) for word in words[2:-1])
        assert out not in xor_def and out not in and_def
        xor_def[out]=(deps,words)
        i+=1
        continue
    words=line.split()
    assert words[-1]=='0'
    lits=[int(word) for word in words[:-1]]
    if len(lits)==3 and lits[0]<0 and lits[1]<0 and lits[2]>0 and i+2<len(lines):
        a,b,out=-lits[0],-lits[1],lits[2]
        second=[int(word) for word in lines[i+1].split()]
        third=[int(word) for word in lines[i+2].split()]
        if second==[a,-out,0] and third==[b,-out,0]:
            assert out not in and_def and out not in xor_def
            and_def[out]=((a,b),(lits,second[:-1],third[:-1]))
            i+=3
            continue
    constraints.append(lits)
    i+=1

definitions={**{out:deps for out,(deps,_) in and_def.items()},
             **{out:deps for out,(deps,_) in xor_def.items()}}
assert len(definitions)==len(and_def)+len(xor_def)
seeds={abs(lit) for clause in constraints for lit in clause}
required=set(seeds)
pending=list(seeds)
while pending:
    var=pending.pop()
    for dep in definitions.get(var,()):
        if dep not in required:
            required.add(dep)
            pending.append(dep)
assert all(1<=var<=old_n for var in required)
retained_ands={var:and_def[var] for var in required if var in and_def}
retained_xors={var:xor_def[var] for var in required if var in xor_def}
mapping={old:index+1 for index,old in enumerate(sorted(required))}


def relit(lit):
    return mapping[abs(lit)]*(1 if lit>0 else -1)


outlines=[]
for clause in constraints:
    outlines.append(' '.join(map(str,(relit(lit) for lit in clause)))+' 0')
for out,(_,clauses) in sorted(retained_ands.items()):
    for clause in clauses:
        outlines.append(' '.join(map(str,(relit(lit) for lit in clause)))+' 0')
for out,(_,words) in sorted(retained_xors.items()):
    outlines.append('x '+' '.join(map(str,(relit(int(word)) for word in words[1:-1])))+' 0')
assert len(outlines)==len(constraints)+3*len(retained_ands)+len(retained_xors)
formula=HERE/'fivepair_projection_sliced.xcnf'
assert not formula.exists()
formula.write_text(f'p cnf {len(mapping)} {len(outlines)}\n'+'\n'.join(outlines)+'\n')
map_path=HERE/'slice_map.json'
assert not map_path.exists()
map_path.write_text(json.dumps({str(old):new for old,new in mapping.items()},
                               sort_keys=True,separators=(',',':'))+'\n')
result={'status':'PASS_XCNF_DEAD_DEFINITION_SLICE','candidate_id':None,
        'curve_id':protocol['curve_id'],'old_variables':old_n,
        'old_clause_xor_rows':int(header[3]),'old_and_gates':len(and_def),
        'old_xor_definitions':len(xor_def),'independent_constraints':len(constraints),
        'new_variables':len(mapping),'new_and_gates':len(retained_ands),
        'new_xor_definitions':len(retained_xors),'new_clause_xor_rows':len(outlines),
        'formula_sha256':sha(formula),'map_sha256':sha(map_path),
        'protocol_sha256':sha(HERE/'slice_protocol.json')}
(HERE/'slice_result.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
print(json.dumps(result,sort_keys=True))
