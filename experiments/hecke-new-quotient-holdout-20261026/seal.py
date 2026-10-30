"""Hash the frozen holdout bundle, excluding caches and this generated seal."""
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
PATHS = [
    'SELECTION_PROTOCOL.md','select_candidate.py','selection.json',
    'PRODUCER_PROTOCOL.md','RESULT.md','runtime-info.json',
    'fiber_gate.py','run_gate.py','fiber_gate.json','gate_launch.json',
    'gate.stdout','gate.stderr','gate_wrapper_failure.txt',
    'tools/exp11_class_walk.py','tools/hecke11.py',
    'run_producer.py','producer_launch.json','producer.stdout','producer.stderr',
    'data/exp11_class_walk_D2631_f6.json','audit.py','audit.json','audit.stdout','audit.stderr',
    'floor_audit.py','floor_audit.json','floor_audit.stdout','floor_audit.stderr',
    'validate.py','validation.json','formal/MixedSix.lean','formal/lean-toolchain',
    'formal/lakefile.toml','formal/lake-manifest.json','formal/build-output.txt','seal.py',
]

result = {'status':'SEALED_D2631_F6_MIXED_HOLDOUT',
          'files':{name:hashlib.sha256((HERE/name).read_bytes()).hexdigest() for name in PATHS}}
destination = HERE/'SEAL.json'
encoded = json.dumps(result,indent=2,sort_keys=True)+'\n'
if '--check' in sys.argv:
    assert destination.read_text()==encoded
    print(result['status'],len(PATHS),'verified')
else:
    destination.write_text(encoded)
    print(result['status'],len(PATHS),'written')
