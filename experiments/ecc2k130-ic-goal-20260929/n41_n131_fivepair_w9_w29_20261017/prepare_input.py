"""Serialize the frozen W9 state table for the native five-pair join."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
source_path = HERE / 'n41_states.json'
data = json.loads(source_path.read_text())
assert data['status'] == 'COMPLETE_SOURCE' and len(data['states']) == 5
count = data['states_per_slot']
assert count == 284 and all(len(slot) == count for slot in data['states'])
tx, ty = data['target_raw_point']
lines = [f'ECC2K41 5 {count} {tx} {ty}']
for slot, states in enumerate(data['states']):
    for index, state in enumerate(states):
        a, b = state['masks']
        sa, sb = state['signs']
        ca, cb = state['columns']
        x, y = state['point']
        lines.append(f'S {slot} {index} {a} {b} {sa} {sb} {ca} {cb} {x} {y}')
text = '\n'.join(lines) + '\n'
(HERE / 'join_input.tsv').write_text(text)
result = {'status': 'PREPARED', 'states_per_slot': count,
          'raw_target': [tx, ty],
          'input_sha256': hashlib.sha256(text.encode()).hexdigest(),
          'source_sha256': hashlib.sha256(source_path.read_bytes()).hexdigest(),
          'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
(HERE / 'prepare_result.json').write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
print(json.dumps(result))
