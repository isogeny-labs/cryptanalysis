"""Independent source reconstruction and exact affine-cover audit."""
import hashlib
import json
from pathlib import Path

D = Path(__file__).resolve().parent
SOURCE = D.parent / 'n131_w20_sevenpair_gate_20261010'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
p = json.loads((D / 'protocol.json').read_text())
r = json.loads((D / 'result.json').read_text())
assert sha(D / 'audit.py') == p['source_sha256']['auditor']
assert sha(D / 'groups.tsv') == r['groups_sha256']
rows = [tuple(map(int, line.split())) for line in (SOURCE / 'support_w20.tsv').open()]
by_mask = {mask: col for mask, col, _ in rows}
assert len(by_mask) == len(rows)
seed = p['selected_seed_mask']
pivot = seed.bit_length() - 1
selector_positions = [bit for bit in range(20) if bit != pivot]
valid = set()
for mask, col, _ in rows:
    other = mask ^ seed
    if mask < other and other in by_mask and col != by_mask[other]:
        code = 0
        for position, source_bit in enumerate(selector_positions):
            code |= ((mask >> source_bit) & 1) << position
        assert code not in valid
        valid.add(code)
assert len(valid) == r['valid_codes'] == p['expected_valid_codes']
seen = set()
count = {'square': 0, 'pair': 0, 'single': 0}
for line in (D / 'groups.tsv').open():
    kind, a, i, j = line.split()
    a, i, j = int(a), int(i), int(j)
    if kind == 'square':
        assert 0 <= i < j < 19
        members = [a, a ^ (1 << i), a ^ (1 << j), a ^ (1 << i) ^ (1 << j)]
        assert members[0] ^ members[1] ^ members[2] ^ members[3] == 0
    elif kind == 'pair':
        assert 0 <= i < 19 and j == -1
        members = [a, a ^ (1 << i)]
    elif kind == 'single':
        assert i == j == -1
        members = [a]
    else:
        raise AssertionError(kind)
    assert all(x in valid and x not in seen for x in members)
    seen.update(members)
    count[kind] += 1
assert seen == valid
assert count == {'square': r['squares'], 'pair': r['pairs'], 'single': r['singles']}
assert sum(count.values()) == r['groups']
record = {'status': 'PASS_INDEPENDENT_AFFINE_COVER',
          'source_rows': len(rows), 'source_codes': len(valid),
          'groups': count, 'all_codes_covered_once': True,
          'source_sha256': sha(SOURCE / 'support_w20.tsv'),
          'result_sha256': sha(D / 'result.json'),
          'groups_sha256': sha(D / 'groups.tsv')}
with (D / 'audit_result.json').open('x') as out:
    json.dump(record, out, sort_keys=True, indent=2); out.write('\n')
print(json.dumps(record, sort_keys=True))
