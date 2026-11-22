"""Build all-deferred N41 W9 source circuit on the frozen public point."""
import hashlib
import json
import sys
import time
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=Path('/Volumes/SSD990/cryptanalysis/experiments/ecc2k130-ic-goal-20260929')
sys.path.insert(0,str(ROOT/'n131_w20_selector_elimination_v2_20261013'))
import selector
import circuit_deferred5 as design


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


protocol=json.loads((HERE/'build_protocol.json').read_text())
for path,digest in protocol['sources'].items():
    assert sha(path)==digest,path
assert not (HERE/'build_result.json').exists()
fixture=json.loads(Path(protocol['fixture']).read_text())
started=time.monotonic_ns()
circ,wires,counts=design.build(fixture['oriented_target_reciprocal'],'deferred5')
built=time.monotonic_ns()
assignment={}
for slot,row in enumerate(fixture['pairs']):
    code=sum(((row['masks'][0]>>bit)&1)<<index
             for index,bit in enumerate(design.BITS))
    assignment.update({wire:(code>>index)&1
                       for index,wire in enumerate(wires['mask'][slot])})
    assignment.update({wire:(row['output_reciprocal']>>index)&1
                       for index,wire in enumerate(wires['out'][slot])})
    assert wires['source_inverse'][slot] is None
for bits,value in zip(wires['middle'],fixture['middle_reciprocals']):
    assignment.update({wire:(value>>index)&1
                       for index,wire in enumerate(bits)})
full=selector.old.complete_assignment(circ,assignment)
control=selector.old.check_assignment(circ,full)
assert control=={'clauses':counts['clauses'],
                'native_xor_rows':counts['xor_rows']}
checked=time.monotonic_ns()
formula=HERE/'deferred5.xcnf'
assert not formula.exists()
circ.write(formula)
written=time.monotonic_ns()
result={'status':'PASS_N41_ALL_DEFERRED_BUILD','candidate_id':None,
        'curve_id':protocol['curve_id'],'counts':counts,
        'input_mask_wires':wires['mask'],'output_wires':wires['out'],
        'middle_wires':wires['middle'],
        'formula_bytes':formula.stat().st_size,'formula_sha256':sha(formula),
        'constructed_control':control,
        'build_ns':built-started,'check_ns':checked-built,
        'write_ns':written-checked,
        'protocol_sha256':sha(HERE/'build_protocol.json')}
(HERE/'build_result.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
print(json.dumps({'status':result['status'],'counts':counts,
                  'formula_bytes':result['formula_bytes']}))
