"""Freeze public-target-independent N41 code boxes around two fixed slots."""
import hashlib
import json
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SOURCE = ROOT / 'n41_n131_w29_rotation_alignment_20261017/aligned_states.json'
RELATION = ROOT / 'n41_n131_w29_rotation_alignment_20261017/n41_audit_result.json'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


source = json.loads(SOURCE.read_text())
relation = json.loads(RELATION.read_text())
assert source['usable_edges'] == 71 and source['states_per_slot'] == 284
assert source['rotations'] == [0, 0, 12, 12, 24]
assert relation['orientation'] == 6
assert relation['state_ids'] == [105, 244, 66, 47, 111]
fixed = [105, 111]
positive = [244 // 4, 66 // 4, 47 // 4]


def column_pair(slot, code):
    rows = source['states'][slot][4*code:4*code+4]
    assert len(rows) == 4
    assert all(row['columns'] == rows[0]['columns'] for row in rows)
    return rows[0]['columns']


fixed_cols = (source['states'][0][fixed[0]]['columns'] +
              source['states'][4][fixed[1]]['columns'])
assert len(set(fixed_cols)) == 4


def eligible(codes):
    columns = fixed_cols[:]
    for slot, code in enumerate(codes, 1):
        columns += column_pair(slot, code)
    return len(set(columns)) == 10


assert eligible(positive)
rng = random.Random(202610171731)
boxes = [{'kind': 'archived_positive', 'codes': positive}]
seen = {tuple(positive)}
draws = 0
while len(boxes) < 1025:
    codes = [rng.randrange(71) for _ in range(3)]
    draws += 1
    key = tuple(codes)
    if key in seen or not eligible(codes):
        continue
    seen.add(key)
    boxes.append({'kind': 'source_draw', 'codes': codes})

panel = {
    'status': 'FROZEN_N41_TRIPLE_CODE_BOX_PANEL',
    'curve_id': source['curve_id'], 'orientation': 6,
    'fixed_slot_state_ids': {'0': fixed[0], '4': fixed[1]},
    'positive_relation_state_ids': relation['state_ids'],
    'sample_seed': 202610171731, 'draws': draws,
    'source_sha256': {'states': sha(SOURCE), 'relation': sha(RELATION)},
    'boxes': boxes,
}
assert not (HERE / 'panel.json').exists()
(HERE / 'panel.json').write_text(json.dumps(panel, sort_keys=True, indent=2)+'\n')
print(json.dumps({'status': panel['status'], 'boxes': len(boxes), 'draws': draws}))
