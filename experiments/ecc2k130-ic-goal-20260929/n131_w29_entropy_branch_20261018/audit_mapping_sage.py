"""Rebuild the original W29 XCNF and audit the eight mask-wire units."""
import hashlib
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


cfg = json.loads((HERE / 'mapping_audit_protocol.json').read_text())
assert cfg['status'] == 'FROZEN_BEFORE_MAPPING_AUDIT'
for name, entry in cfg['sources'].items():
    assert sha(entry['path']) == entry['sha256'], name
protocol = json.loads(Path(cfg['sources']['protocol']['path']).read_text())
old_result = json.loads(Path(cfg['sources']['old_result']['path']).read_text())
control = json.loads(Path(cfg['sources']['control']['path']).read_text())
sys.path.insert(0, str(Path(cfg['sources']['circuit']['path']).parent))
import circuit_n131_3p2 as design

machine, wires, counts = design.build(old_result['target_reciprocal'])
assert design.BITS[:8] == list(range(8))
assert wires['mask'][0][:8] == list(range(1, 9))
assert counts['variables'] == 121204
assert counts['clauses'] == 232429 and counts['xor_rows'] == 42502
assert control['pairs'][0]['masks'][0] & 255 == protocol['branch_prefix_value'] == 3
with tempfile.TemporaryDirectory(prefix='n131_w29_mapping_', dir='/private/tmp') as temp:
    rebuilt = Path(temp) / 'rebuilt.xcnf'
    machine.write(rebuilt)
    rebuilt_hash = sha(rebuilt)
assert rebuilt_hash == old_result['formula_sha256']
assert rebuilt_hash == cfg['sources']['original_xcnf']['sha256']
result = {'status':'PASS_EXACT_3P2_FORMULA_AND_MASK_WIRE_REBUILD',
          'first_mask_bits':design.BITS[:8],
          'first_mask_variables':wires['mask'][0][:8],
          'control_prefix_value':control['pairs'][0]['masks'][0]&255,
          'original_formula_sha256':rebuilt_hash,'formula_counts':counts,
          'protocol_sha256':sha(HERE/'protocol.json'),
          'audit_protocol_sha256':sha(HERE/'mapping_audit_protocol.json'),
          'auditor_sha256':sha(Path(__file__))}
(HERE/'mapping_audit_result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps({k:result[k] for k in ('status','first_mask_bits','first_mask_variables','control_prefix_value','original_formula_sha256')},sort_keys=True))
