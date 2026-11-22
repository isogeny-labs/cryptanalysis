"""Check the matched two-inverse six-pair control assignment."""
import hashlib
import json
from pathlib import Path

import build
import circuit_two_inverse as baseline

HERE = Path(__file__).resolve().parent
g = baseline.geometry()
states, raw_target, middle = build.six_control(g)
machine, wires, e = baseline.build(baseline.F.inv(raw_target[0]))
values = {}

def bind(bits, number):
    values.update({wire:(number>>i)&1 for i,wire in enumerate(bits)})

rotated = []
for slot,state in enumerate(states):
    rotation = g['rotations'][slot]
    c_rot = baseline.standard(state['z'])
    c = baseline.frob(c_rot, baseline.N-rotation)
    bind(wires['outputs'][slot], c)
    bind(wires['inverses'][slot], baseline.F.inv(c))
    w1 = baseline.xor((baseline.F.square(g['blocks'][0]['basis'][i]) ^ g['blocks'][0]['basis'][i])
                      for i in range(8) if state['a']>>i&1)
    w2 = w1 ^ e['seed']
    bind(wires['endpoints'][slot][0], baseline.F.inv(w1))
    bind(wires['endpoints'][slot][1], baseline.F.inv(w2))
    rotated.append(c_rot)
for bits,value in zip(wires['middle'],middle):
    bind(bits,value)
coords = rotated + middle + [baseline.F.inv(raw_target[0])]
for k,(left,right,out) in enumerate(baseline.BALANCED_LINKS):
    a,b,z = (coords[i] for i in (left,right,out))
    total = a^b^z
    branch = baseline.F.mul(baseline.F.mul(a,b),z)^baseline.F.halftrace(baseline.F.square(total))
    assert branch in (0,1)
    values[wires['branches'][k]] = branch
complete = baseline.old.complete_assignment(machine,values)
check = baseline.old.check_assignment(machine,complete)
result = {'status':'PASS_MATCHED_SIXPAIR_TWO_INVERSE_CONTROL',
          'control_check':check,'and_gates':machine.and_count,
          'source_sha256':hashlib.sha256((HERE/'circuit_two_inverse.py').read_bytes()).hexdigest(),
          'control_raw_point':list(raw_target)}
with (HERE/'two_inverse_check_result.json').open('x') as out:
    json.dump(result,out,sort_keys=True,indent=2)
    out.write('\n')
print(result['status'])
