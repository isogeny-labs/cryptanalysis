"""Classify the completed single-orientation worker after monitor failure."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


states = json.loads((HERE / 'n41_states.json').read_text())['states']
columns = [[sum(1 << c for c in row['columns']) for row in slot] for slot in states]
left = 0
for a in columns[0]:
    for b in columns[1]:
        if a & b:
            continue
        used = a | b
        left += sum(not (used & c) for c in columns[2])
right = sum(not (a & b) for a in columns[3] for b in columns[4])
lines = (HERE / 'join.stdout').read_text().splitlines()
assert len(lines) == 3 and lines[0].startswith('CHECK_PASS 1420 ')
assert int(lines[1].split()[1]) == left
assert lines[2].split()[:3] == ['MISS_COMPLETE', str(right), '0']
assert not (HERE / 'join.stderr').read_bytes()
result = {'status': 'COMPLETE_MISS', 'monitor_status': 'FAILED_PROCESS_LIST_PERMISSION',
          'native_exit_code': None, 'process_terminal_observed': True,
          'left_triples': left, 'right_pairs': right,
          'target_raw_point': json.loads((HERE / 'n41_states.json').read_text())['target_raw_point'],
          'join_protocol_sha256': sha(HERE / 'join_protocol.json'),
          'stdout_sha256': sha(HERE / 'join.stdout'),
          'stderr_sha256': sha(HERE / 'join.stderr'),
          'auditor_sha256': sha(Path(__file__))}
with (HERE / 'single_result.json').open('x') as out:
    json.dump(result, out, sort_keys=True, indent=2)
    out.write('\n')
print(json.dumps(result, sort_keys=True))
