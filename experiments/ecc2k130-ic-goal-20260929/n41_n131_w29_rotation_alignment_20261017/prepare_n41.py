"""Freeze paired-aligned five-slot geometry from the audited W9 source."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / 'n41_n131_fivepair_w9_w29_20261017'
MAPPING = (0, 0, 2, 2, 4)
ROTATIONS = (0, 0, 12, 12, 24)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


original = json.loads((SOURCE / 'n41_states.json').read_text())
assert original['status'] and original['rotations'] == [0, 6, 12, 18, 24]
assert original['states_per_slot'] == 284 and original['usable_edges'] == 71
assert original['target_raw_point'] == [2026560328086, 1928332930914]
aligned = {key: original[key] for key in
           ('curve_id', 'eligible_mask_count', 'field_modulus_taps',
            'folded_column_count', 'seed', 'states_per_slot', 'target_raw_point',
            'usable_edges', 'width')}
aligned.update({'status': 'FROZEN_PAIRED_ALIGNED_N41_W9_STATES',
                'slot_mapping_from_template': MAPPING,
                'rotations': ROTATIONS,
                'source_template_sha256': sha(SOURCE / 'n41_states.json'),
                'states': [original['states'][i] for i in MAPPING]})
states_path = HERE / 'aligned_states.json'
with states_path.open('x') as out:
    json.dump(aligned, out, sort_keys=True, indent=2)
    out.write('\n')

lines = (SOURCE / 'join_input.tsv').read_text().splitlines()
assert lines[0] == 'ECC2K41 5 284 2026560328086 1928332930914'
source_rows = {slot: [] for slot in range(5)}
for line in lines[1:]:
    parts = line.split(maxsplit=3)
    assert parts[0] == 'S' and len(parts) == 4
    source_rows[int(parts[1])].append((int(parts[2]), parts[3]))
assert all([sid for sid, _ in source_rows[slot]] == list(range(284))
           for slot in range(5))
aligned_lines = [lines[0]]
for slot, old_slot in enumerate(MAPPING):
    for sid, rest in source_rows[old_slot]:
        aligned_lines.append(f'S {slot} {sid} {rest}')
input_path = HERE / 'aligned_input.tsv'
with input_path.open('x') as out:
    out.write('\n'.join(aligned_lines) + '\n')

assert aligned['states'][0] == aligned['states'][1]
assert aligned['states'][2] == aligned['states'][3]
assert aligned['states'][0][0]['point'] == [int(x) for x in aligned_lines[1].split()[-2:]]
result = {'status': 'PASS_PAIRED_ALIGNED_N41_INPUT',
          'curve_id': aligned['curve_id'], 'source_rotations': original['rotations'],
          'aligned_rotations': ROTATIONS, 'slot_mapping': MAPPING,
          'states_per_slot': aligned['states_per_slot'],
          'target_raw_point': aligned['target_raw_point'],
          'source_sha256': {name: sha(path) for name, path in
                            {'script': Path(__file__), 'template_states': SOURCE / 'n41_states.json',
                             'template_input': SOURCE / 'join_input.tsv',
                             'aligned_states': states_path, 'aligned_input': input_path}.items()}}
with (HERE / 'prepare_result.json').open('x') as out:
    json.dump(result, out, sort_keys=True, indent=2)
    out.write('\n')
print(json.dumps({key: result[key] for key in
                  ('status', 'aligned_rotations', 'states_per_slot', 'target_raw_point')}))
