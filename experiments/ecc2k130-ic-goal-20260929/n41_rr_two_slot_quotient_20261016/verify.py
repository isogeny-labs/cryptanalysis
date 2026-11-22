"""Terminal receipt check for the frozen two-slot quotient diagnostic."""
import hashlib
import json
from pathlib import Path

here = Path(__file__).resolve().parent
root = here.parent
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
protocol = json.loads((here/'protocol.json').read_text())
result = json.loads((here/'result.json').read_text())
audit = json.loads((here/'audit_sage.json').read_text())
assert sha(here/'run.py') == protocol['runner_sha256']
assert sha(here/'protocol.json') == result['protocol_sha256']
for path, digest in protocol['sources'].items():
    assert sha(root/path) == digest == result['source_sha256'][path]
assert result['eligible_states'] == audit['eligible_states'] == [144, 144]
assert result['zero_signature'] == [0, 0]
assert audit['group_pairs_checked'] == 144*144
assert result['matches'] == audit['raw_group_matches'] == audit['distinct_column_group_matches'] == [[12, 122]]
assert audit['runner_result_sha256'] == sha(here/'result.json')
assert audit['status'] == 'PASS'
lean = (here/'lean.stdout.txt').read_text()
assert "'RRQuotient.det2_zero_iff_cross_equal' depends on axioms: [propext, Quot.sound]" in lean
assert not (here/'lean.stderr.txt').read_text()
out = {'status': 'PASS', 'candidate_id': None,
       'result_sha256': sha(here/'result.json'),
       'audit_sha256': sha(here/'audit_sage.json'),
       'lean_sha256': sha(here/'lean.stdout.txt')}
(here/'terminal.json').write_text(json.dumps(out, sort_keys=True, indent=2)+'\n')
print(json.dumps(out, sort_keys=True))
