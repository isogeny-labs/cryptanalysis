"""Freeze source-valid six-slot boxes without consulting determinant outcomes."""
import hashlib
import json
import random
from pathlib import Path

D = Path(__file__).resolve().parent
S = D.parent / 'n41_sixpair_shared_target_20261017' / 'join_input.tsv'
lines = S.read_text().splitlines()
h = lines[0].split()
assert h[:3] == ['ECC2K41', '6', '160']
rows = {}
for line in lines[1:]:
    v = line.split()
    assert v[0] == 'S'
    j, i = map(int, v[1:3])
    rows[j, i] = {'ca': int(v[7]), 'cb': int(v[8]), 'x': int(v[9]), 'y': int(v[10])}
assert len(rows) == 960
for j in range(6):
    for c in range(40):
        a, b = rows[j, 4*c], rows[j, 4*c+3]
        assert a['x'] == b['x'] and (a['y'] ^ b['y']) == a['x']
        for k in range(4):
            assert (rows[j, 4*c+k]['ca'], rows[j, 4*c+k]['cb']) == (a['ca'], a['cb'])

def cols(c):
    r = rows[0, 4*c]
    return {r['ca'], r['cb']}

def choose(rng, n, required=()):
    chosen = list(required)
    used = set().union(*(cols(c) for c in chosen)) if chosen else set()
    order = list(range(40))
    rng.shuffle(order)
    for c in order:
        if c in chosen or cols(c) & used:
            continue
        chosen.append(c)
        used.update(cols(c))
        if len(chosen) == n:
            return chosen
    raise RuntimeError('insufficient disjoint code edges')

rng = random.Random(20261017)
panels = []
for kind in ('sign', 'root_sign', 'two_code'):
    for trial in range(32):
        cc = choose(rng, 12 if kind == 'two_code' else 6)
        if kind == 'sign':
            slots = [[4*c, 4*c+3] for c in cc[:6]]
        elif kind == 'root_sign':
            slots = [[4*c+k for k in range(4)] for c in cc[:6]]
        else:
            slots = [[4*cc[j], 4*cc[j+6]] for j in range(6)]
        panels.append({'kind': kind, 'trial': trial, 'slots': slots, 'codes': cc})
witness = [12, 122, 116, 47, 128, 34]
wc = [i//4 for i in witness]
assert len(set().union(*(cols(c) for c in wc))) == 12
alts = choose(rng, 12, required=wc)[6:]
panels.append({'kind': 'witness_two_code', 'trial': 0,
               'slots': [[witness[j], 4*alts[j]] for j in range(6)],
               'codes': wc+alts})
assert len(panels) == 97
for panel in panels:
    unique = set(panel['codes'])
    assert len(set().union(*(cols(c) for c in unique))) == 2*len(unique)
    for j, states in enumerate(panel['slots']):
        assert all((j, i) in rows for i in states)

source_sha = hashlib.sha256(S.read_bytes()).hexdigest()
out = {'schema': 1, 'source_sha256': source_sha,
       'target': [int(h[3]), int(h[4])],
       'selection_seed': 20261017, 'panels': panels,
       'witness_states': witness}
(D/'panel.json').write_text(json.dumps(out, indent=2, sort_keys=True)+'\n')
print(json.dumps({'source_sha256': source_sha, 'panel_count': len(panels),
                  'kinds': {k: sum(p['kind'] == k for p in panels)
                            for k in ('sign', 'root_sign', 'two_code', 'witness_two_code')}}))
