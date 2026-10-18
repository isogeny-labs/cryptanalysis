"""Freeze ordered staged-S3 inputs before the comparator build."""
import hashlib
import json
from pathlib import Path

here=Path(__file__).resolve().parent
root=here.parent
base=json.loads((here/'build_protocol.json').read_text())
out=here/'ordered_build_protocol.json'
assert not out.exists()
paths=[here/'build_ordered.py',here/'formula.xcnf',here/'input_wires.json',
       here/'build_result.json',here/'audit_result.json',
       root/'n41_w9_equal_rotation_order_20261018/OrderSymmetry.lean',
       Path(base['panel']),Path(base['states'])]
record={'status':'FROZEN_BEFORE_N41_STAGED_S3_ORDERED_BUILD',
        'candidate_id':None,'curve_id':base['curve_id'],
        'baseline_formula':str(here/'formula.xcnf'),
        'input_wires':str(here/'input_wires.json'),
        'panel':base['panel'],'states':base['states'],
        'sources':{str(path):hashlib.sha256(path.read_bytes()).hexdigest()
                   for path in paths}}
out.write_text(json.dumps(record,sort_keys=True,indent=2)+'\n')
print(hashlib.sha256(out.read_bytes()).hexdigest())
