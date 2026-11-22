"""Read-only receipt and source-bound consistency checks."""
import hashlib
import json
from pathlib import Path

D = Path(__file__).resolve().parent
SOURCE = D.parent/'n131_w20_sevenpair_gate_20261010'
BASE = D.parent/'n131_symbolic_rect_projection_20261015'
PRIOR = D.parent/'n131_w20_affine_rectangle_partition_20261016'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
t = json.loads((D/'terminal.json').read_text())
for name,digest in t['files'].items():
    assert sha(D/name) == digest,name
assert t['external'] == {
    'selected_source_support':sha(SOURCE/'support_w20.tsv'),
    'selected_source_count':sha(SOURCE/'count_result_v2.json'),
    'fixed_prefix_result':sha(BASE/'prefix_result.json'),
    'prior_affine_cover_result':sha(PRIOR/'result.json')}
p1 = json.loads((D/'protocol.json').read_text())
p2 = json.loads((D/'protocol_v2.json').read_text())
r1 = json.loads((D/'result.json').read_text())
r2 = json.loads((D/'result_v2.json').read_text())
a1 = json.loads((D/'audit_result.json').read_text())
a2 = json.loads((D/'audit_result_v2.json').read_text())
assert sha(SOURCE/'support_w20.tsv') == p1['source_sha256']['support'] == a2['source_sha256']
assert sha(BASE/'prefix_result.json') == p1['source_sha256']['prefix_result']
assert sha(D/'run.py') == p1['source_sha256']['worker']
assert sha(D/'audit.py') == p1['source_sha256']['auditor']
assert sha(D/'protocol.json') == r1['protocol_sha256'] == p2['source_protocol_sha256']
assert sha(D/'groups.tsv') == r1['groups_sha256'] == p2['source_groups_sha256']
assert sha(D/'audit_result.json') == p2['source_audit_sha256']
assert sha(D/'run_v2.py') == p2['worker_sha256']
assert sha(D/'audit_v2.py') == p2['auditor_sha256']
assert sha(D/'protocol_v2.json') == r2['protocol_sha256']
assert sha(D/'groups_v2.tsv') == r2['groups_sha256'] == a2['groups_sha256']
assert a1['all_codes_covered_once'] and a2['all_codes_covered_once']
assert 4*r2['squares']+2*r2['pairs']+r2['singles'] == r2['valid_codes'] == 132045
assert r2['groups'] == r2['squares']+r2['pairs']+r2['singles'] == 34078
assert r2['group_pairs_before_exclusions'] == r2['groups']**2
prior = json.loads((PRIOR/'result.json').read_text())
assert prior['group_count_per_slot'] == 33099
assert prior['valid_codes_per_slot'] == r2['valid_codes']
assert 'map_two_bit_chart' in (D/'lean.stdout').read_text()
assert 'pair_product_add' in (D/'lean.stdout').read_text()
print('PASS frozen W20 source, two independently audited covers, Lean receipt')
