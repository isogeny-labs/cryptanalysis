"""Subset the frozen N41 W11 four-pair states to code width ten."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
protocol = json.loads((HERE/'prepare_protocol.json').read_text())
assert protocol['status'] == 'FROZEN_BEFORE_W10_PREPARE'
assert sha(PARENT/'join4_input.tsv') == protocol['parent_input_sha256']
assert sha(__file__) == protocol['script_sha256']
old = (PARENT/'join4_input.tsv').read_text().splitlines()
assert old[0] == 'W11FOUR 4 1124 1'
lines = ['W10FOUR 4 520 1',old[1]]
for slot in range(4):
    selected = [line.split() for line in old if line.startswith(f'S {slot} ') and int(line.split()[3]) < 512]
    selected.sort(key=lambda p:(int(p[3]),int(p[4])))
    assert len(selected) == 520
    for sid,p in enumerate(selected):
        assert int(p[4]) == sid%4
        p[2] = str(sid)
        lines.append(' '.join(p))
lines += [line for line in old if line.startswith('C ')]
assert len(lines) == 2+4*520+128
out = HERE/'join4_w10_input.tsv'
out.write_text('\n'.join(lines)+'\n')
result = {'status':'COMPLETE_W10_PREPARE','candidate_id':None,
          'states_per_slot':520,'rotations':[0,12,24,36],
          'public_target':list(map(int,old[1].split()[2:])),
          'input_sha256':sha(out), 'protocol_sha256':sha(HERE/'prepare_protocol.json'),
          'script_sha256':sha(__file__)}
(HERE/'prepare_result.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
print(json.dumps(result,sort_keys=True))
