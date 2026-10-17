"""Seal source, proof, groups, audits, and explanatory result."""
import hashlib
import json
from pathlib import Path

D = Path(__file__).resolve().parent
SOURCE = D.parent/'n131_w20_sevenpair_gate_20261010'
BASE = D.parent/'n131_symbolic_rect_projection_20261015'
PRIOR = D.parent/'n131_w20_affine_rectangle_partition_20261016'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
files = ['RESULT.md','PROOF_MAP.md','AffineChart.lean','lean-toolchain',
         'lean.stdout','lean.stderr','freeze.py','run.py','audit.py',
         'freeze_v2.py','run_v2.py','audit_v2.py',
         'terminal.py','verify.py','terminal_v1.json',
         'protocol.json','protocol_v2.json','sage_runtime_info.json',
         'groups.tsv','groups_v2.tsv','result.json','result_v2.json',
         'audit_result.json','audit_result_v2.json',
         'run.stdout','run.stderr','audit.stdout','audit.stderr',
         'run_v2.stdout','run_v2.stderr','audit_v2.stdout','audit_v2.stderr']
result = json.loads((D/'result_v2.json').read_text())
audit = json.loads((D/'audit_result_v2.json').read_text())
assert result['status'] == 'PASS_EXACT_W20_AFFINE_COVER_WEIGHT2'
assert audit['status'] == 'PASS_INDEPENDENT_W20_WEIGHT2_AFFINE_COVER'
record = {'status':'PASS_SOURCE_COMPONENT','schema':1,
          'files':{name:sha(D/name) for name in files},
          'external':{
              'selected_source_support':sha(SOURCE/'support_w20.tsv'),
              'selected_source_count':sha(SOURCE/'count_result_v2.json'),
              'fixed_prefix_result':sha(BASE/'prefix_result.json'),
              'prior_affine_cover_result':sha(PRIOR/'result.json')}}
with (D/'terminal.json').open('x') as out:
    json.dump(record,out,sort_keys=True,indent=2);out.write('\n')
print(sha(D/'terminal.json'))
