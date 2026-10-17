"""Build and independently check a six-pair shared-inverse target circuit."""
import hashlib
import json
import resource
import time
from pathlib import Path

import circuit

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
F=circuit.F
sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()


def six_control(g):
    states=g['positive_control']['states'][:6]
    nodes=[tuple(state['raw_sum']) for state in states]
    intermediates=[]
    for left,right,out in circuit.BALANCED_LINKS:
        point=circuit.replay.add(F,nodes[left],nodes[right])
        assert point and point[0]
        if out==10:
            return states,point,intermediates
        assert out==len(nodes)
        nodes.append(point)
        intermediates.append(F.inv(point[0]))
    raise AssertionError('missing final target')


def control_assignment(wires,g,states,target,intermediates):
    values={}
    def bind(bits,number):
        values.update({wire:(number>>i)&1 for i,wire in enumerate(bits)})
    e=circuit.projector()
    basis=g['blocks'][0]['basis']
    rotated=[]
    for slot,state in enumerate(states):
        rotation=g['rotations'][slot]
        c_rot=circuit.standard(state['z'])
        c=circuit.frob(c_rot,circuit.N-rotation)
        bind(wires['outputs'][slot],c)
        bind(wires['inverses'][slot],F.inv(c))
        w1=circuit.xor((F.square(basis[i])^basis[i]) for i in range(8) if state['a']>>i&1)
        w2=w1^e['seed']
        assert w1 and w2
        assert circuit.trace(F.inv(w1))==circuit.trace(F.inv(w2))==0
        bind(wires['endpoints'][slot],F.inv(F.mul(w1,w2)))
        rotated.append(c_rot)
    for bits,value in zip(wires['middle'],intermediates):bind(bits,value)
    coords=rotated+intermediates+[target]
    for k,(left,right,out) in enumerate(circuit.BALANCED_LINKS):
        a,b,z=(coords[i] for i in (left,right,out))
        total=a^b^z
        branch=F.mul(F.mul(a,b),z)^F.halftrace(F.square(total))
        assert branch in (0,1)
        values[wires['branches'][k]]=branch
    return values


def main():
    g=circuit.geometry()
    states,control_raw,middle=six_control(g)
    control_target=F.inv(control_raw[0])
    public_raw=tuple(g['positive_control']['raw_target'])
    public_target=F.inv(public_raw[0])
    assert control_raw!=public_raw
    panels=[]
    for name,target in (('control',control_target),('public',public_target)):
        start=time.monotonic_ns()
        machine,wires,_=circuit.build(target)
        built=time.monotonic_ns()
        checks=None
        if name=='control':
            initial=control_assignment(wires,g,states,target,middle)
            complete=circuit.old.complete_assignment(machine,initial)
            checks=circuit.old.check_assignment(machine,complete)
        checked=time.monotonic_ns()
        path=HERE/f'{name}.xcnf'
        machine.write(path)
        end=time.monotonic_ns()
        panels.append({'name':name,'target_reciprocal':target,
                       'variables':machine.next_var-1,'and_gates':machine.and_count,
                       'clauses':len(machine.clauses),'xor_rows':len(machine.xors),
                       'xcnf_bytes':path.stat().st_size,'xcnf_sha256':sha(path),
                       'build_ns':built-start,'assignment_check_ns':checked-built,
                       'serialization_ns':end-checked,'control_check':checks})
    result={'status':'COMPLETE_SIXPAIR_CONTROL_AND_PUBLIC_BUILD',
            'curve_id':g['curve_id'],'candidate_id':None,
            'rotations':g['rotations'][:6],
            'topology':[list(x) for x in circuit.BALANCED_LINKS],
            'control_raw_point':list(control_raw),
            'public_raw_point':list(public_raw),
            'public_subgroup_point':g['positive_control']['subgroup_target'],
            'control_pair_masks':[[s['a'],s['b']] for s in states],
            'panels':panels,'peak_rss_raw':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    (HERE/'build_result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:result[k] for k in ('status','control_raw_point','public_raw_point','panels')},indent=2))


if __name__=='__main__':main()
