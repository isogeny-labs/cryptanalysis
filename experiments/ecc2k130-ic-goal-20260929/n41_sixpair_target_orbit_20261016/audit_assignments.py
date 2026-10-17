"""Check all 41 independently found orbit relations against one public XCNF."""
import hashlib
import json
from pathlib import Path
import circuit

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
protocol=json.loads((HERE/'assignment_protocol.json').read_text())
for path,digest in protocol['sources'].items():assert sha(path)==digest,path
g=circuit.geometry();F=circuit.F
build=json.loads((HERE/'build_result.json').read_text())
join=json.loads((HERE/'join_result.json').read_text())
target=F.inv(g['positive_control']['raw_target'][0])
machine,wires,e=circuit.build(target)
assert machine.and_count==build['panels'][1]['and_gates']
assert len(machine.clauses)==build['panels'][1]['clauses']
assert len(machine.xors)==build['panels'][1]['xor_rows']
assert wires['target_orbit']==build['panels'][1]['target_orbit']
def assignment(j,states):
    values={}
    def bind(bits,number):values.update({wire:(number>>i)&1 for i,wire in enumerate(bits)})
    basis=g['blocks'][0]['basis'];rotated=[]
    for slot,state in enumerate(states):
        rotation=g['rotations'][slot]
        c_rot=circuit.standard(state['z'])
        c=circuit.frob(c_rot,circuit.N-rotation)
        bind(wires['outputs'][slot],c);bind(wires['inverses'][slot],F.inv(c))
        w1=circuit.xor((F.square(basis[i])^basis[i]) for i in range(8) if state['a']>>i&1)
        w2=w1^e['seed']
        assert w1 and w2
        bind(wires['endpoints'][slot],F.inv(F.mul(w1,w2)))
        rotated.append(c_rot)
    nodes=[tuple(s['raw_sum']) for s in states]
    intermediates=[]
    for left,right,out in circuit.BALANCED_LINKS:
        P=circuit.replay.add(F,nodes[left],nodes[right])
        assert P and P[0]
        if out==10:
            assert F.inv(P[0])==wires['target_orbit'][j]
        else:
            assert out==len(nodes)
            nodes.append(P);intermediates.append(F.inv(P[0]))
    for bits,value in zip(wires['middle'],intermediates):bind(bits,value)
    for k,wire in enumerate(wires['target_selector']):values[wire]=int(k==j)
    coords=rotated+intermediates+[wires['target_orbit'][j]]
    for k,(left,right,out) in enumerate(circuit.BALANCED_LINKS):
        a,b,z=(coords[i] for i in (left,right,out))
        total=a^b^z
        branch=F.mul(F.mul(a,b),z)^F.halftrace(F.square(total))
        assert branch in (0,1)
        values[wires['branches'][k]]=branch
    return values
receipts=[]
for j,line in enumerate(join['hits']):
    parts=line.split();assert parts[0]=='ORBIT_HIT' and int(parts[1])==j
    ids=list(map(int,parts[2:8]))
    states=[g['blocks'][slot]['states'][sid] for slot,sid in enumerate(ids)]
    initial=assignment(j,states)
    complete=circuit.old.complete_assignment(machine,initial)
    checked=circuit.old.check_assignment(machine,complete)
    assert checked=={'clauses':build['panels'][1]['clauses'],
                     'native_xor_rows':build['panels'][1]['xor_rows']}
    receipts.append({'orbit_index':j,'state_ids':ids,'initial_variables':len(initial),
                     'assigned_variables':len(complete),'checked':checked})
out={'status':'PASS_41_PUBLIC_ORBIT_XCNF_ASSIGNMENTS','count':len(receipts),
     'and_gates':machine.and_count,'clauses':len(machine.clauses),
     'native_xor_rows':len(machine.xors),'receipts':receipts,
     'protocol_sha256':sha(HERE/'assignment_protocol.json')}
(HERE/'assignment_audit.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
print(out['status'],out['count'])
