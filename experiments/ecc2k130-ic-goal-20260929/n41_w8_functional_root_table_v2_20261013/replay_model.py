"""Independently check and decode a SAT model on the balanced N41 public query."""
import hashlib,itertools,json
from pathlib import Path
import circuit
HERE=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
query=json.loads((HERE/'public_result.json').read_text())
assert query['status']=='SAT' and sha(HERE/'solver.stdout')==query['sha256']['solver.stdout']
control=json.loads((HERE/'control_result.json').read_text())
lines=(HERE/'solver.stdout').read_text().splitlines()
assert 's SATISFIABLE' in lines
values={}
for line in lines:
    if line.startswith('v '):
        for token in line.split()[1:]:
            lit=int(token)
            if lit:
                assert abs(lit) not in values
                values[abs(lit)]=lit>0
assert len(values)==control['variables']
def val(lit):return values[abs(lit)] if lit>0 else not values[abs(lit)]
clauses=xors=bad_clauses=bad_xors=0
with (HERE/'public.xcnf').open() as source:
    assert source.readline().split()==['p','cnf',str(control['variables']),
                                     str(control['clauses']+control['xor_rows'])]
    for line in source:
        p=line.split();assert p[-1]=='0'
        if p[0]=='x':
            items=list(map(int,p[1:-1]))
            bad_xors+=(sum(val(v) for v in items)&1)!=1
            xors+=1
        else:
            bad_clauses+=not any(val(int(v)) for v in p[:-1]);clauses+=1
assert (clauses,xors,bad_clauses,bad_xors)==(control['clauses'],control['xor_rows'],0,0)
g=circuit.geometry();target=circuit.F.inv(g['positive_control']['raw_target'][0])
c,w,e=circuit.build(target);assert c.next_var-1==len(values)
def decode(row):return sum(int(values[v])<<i for i,v in enumerate(row))
chosen=[]
for slot in range(7):
    code=decode(w['codes'][slot]);mask=sum(((code>>j)&1)<<bit for j,bit in enumerate(e['bits']))
    a=decode(w['outputs'][slot]);rotated=circuit.frob(a,g['rotations'][slot])
    states=[s for s in g['blocks'][slot]['states']
            if s['a']==mask and circuit.standard(s['z'])==rotated]
    assert len(states)==2,(slot,mask,a,len(states))
    chosen.append(states)
raw=tuple(g['positive_control']['raw_target']);public=tuple(g['positive_control']['subgroup_target'])
hits=[]
for selection in itertools.product(*chosen):
    cols=[col for s in selection for col in s['columns']]
    if len(set(cols))!=14:continue
    total=None
    for s in selection:total=circuit.replay.add(circuit.F,total,tuple(s['raw_sum']))
    if total==raw and circuit.replay.times4(circuit.F,total)==public:
        hits.append([{'a':s['a'],'b':s['b'],'sign_a':s['sign_a'],'sign_b':s['sign_b'],
                      'raw_sum':s['raw_sum'],'columns':s['columns']} for s in selection])
assert hits
result={'status':'PASS_BALANCED_N41_UNPINNED_MODEL_REPLAY',
        'clauses_checked':clauses,'xors_checked':xors,'matches':len(hits),
        'selected':hits[0],'raw_target':list(raw),'public_target':list(public),
        'formula_sha256':sha(HERE/'public.xcnf'),'solver_stdout_sha256':sha(HERE/'solver.stdout')}
with (HERE/'model_replay.json').open('x') as out:
    json.dump(result,out,sort_keys=True,indent=2);out.write('\n')
print(result['status'],result['matches'])
