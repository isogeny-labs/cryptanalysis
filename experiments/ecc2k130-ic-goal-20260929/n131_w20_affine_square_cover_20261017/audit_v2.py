"""Independent W20 source check of the weight-two affine cover."""
import hashlib
import json
from pathlib import Path

D = Path(__file__).resolve().parent
SOURCE = D.parent / 'n131_w20_sevenpair_gate_20261010'
sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
p = json.loads((D/'protocol_v2.json').read_text())
r = json.loads((D/'result_v2.json').read_text())
assert sha(D/'audit_v2.py') == p['auditor_sha256']
assert sha(D/'groups_v2.tsv') == r['groups_sha256']
seed = json.loads((D/'protocol.json').read_text())['selected_seed_mask']
pivot = seed.bit_length()-1
positions = [i for i in range(20) if i != pivot]
source = {}
for line in (SOURCE/'support_w20.tsv').open():
    mask, column, _ = map(int, line.split())
    source[mask] = column
valid = set()
for mask, col in source.items():
    mate = mask^seed
    if mask < mate and mate in source and col != source[mate]:
        valid.add(sum(((mask >> bit)&1)<<i for i,bit in enumerate(positions)))
assert len(valid) == r['valid_codes']
seen = set()
counts = {'square':0,'pair':0,'single':0}
weight2_square_count = 0
for line in (D/'groups_v2.tsv').open():
    kind, x, y, z = line.split()
    a,d1,d2 = int(x),int(y),int(z)
    assert 0 <= a < (1<<19)
    if kind == 'square':
        assert 1 <= d1.bit_count() <= 2 and 1 <= d2.bit_count() <= 2 and d1 != d2
        members = (a,a^d1,a^d2,a^d1^d2)
        assert len(set(members)) == 4 and members[0]^members[1]^members[2]^members[3] == 0
        if d1.bit_count() == 2 or d2.bit_count() == 2:
            weight2_square_count += 1
    elif kind == 'pair':
        assert 1 <= d1.bit_count() <= 2 and d2 == 0
        members = (a,a^d1)
    else:
        assert kind == 'single' and d1 == d2 == 0
        members = (a,)
    assert all(code in valid and code not in seen for code in members)
    seen.update(members)
    counts[kind] += 1
assert seen == valid
assert counts == {'square':r['squares'],'pair':r['pairs'],'single':r['singles']}
assert sum(counts.values()) == r['groups']
record = {'status':'PASS_INDEPENDENT_W20_WEIGHT2_AFFINE_COVER',
          'source_codes':len(valid), 'groups':counts,
          'squares_using_weight2_direction':weight2_square_count,
          'all_codes_covered_once':True,
          'source_sha256':sha(SOURCE/'support_w20.tsv'),
          'groups_sha256':sha(D/'groups_v2.tsv'),
          'result_sha256':sha(D/'result_v2.json')}
with (D/'audit_result_v2.json').open('x') as out:
    json.dump(record,out,sort_keys=True,indent=2);out.write('\n')
print(json.dumps(record,sort_keys=True))
