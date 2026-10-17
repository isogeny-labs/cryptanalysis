"""Adaptive affine 2-flat packing using weight-one/two selector directions."""
import hashlib
import json
import resource
import signal
import time
from pathlib import Path

D = Path(__file__).resolve().parent
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
p = json.loads((D / 'protocol_v2.json').read_text())
assert sha(D / 'run_v2.py') == p['worker_sha256']
assert sha(D / 'groups.tsv') == p['source_groups_sha256']
assert sha(D / 'audit_result.json') == p['source_audit_sha256']
signal.alarm(p['wall_cap_s'])
start = time.monotonic()
codes = set()
for line in (D / 'groups.tsv').open():
    kind, base, i, j = line.split()
    a, i, j = int(base), int(i), int(j)
    if kind == 'square':
        members = (a, a^(1<<i), a^(1<<j), a^(1<<i)^(1<<j))
    elif kind == 'pair':
        members = (a, a^(1<<i))
    else:
        assert kind == 'single'
        members = (a,)
    codes.update(members)
valid = sorted(codes)
assert len(valid) == json.loads((D / 'result.json').read_text())['valid_codes']
directions = [1<<i for i in range(19)]
directions += [(1<<i)|(1<<j) for i in range(19) for j in range(i+1,19)]
directions[19:] = sorted(directions[19:])
active = bytearray(1<<19)
for a in valid:
    active[a] = 1
loaded = time.monotonic()
groups = []
squares = 0
for index, a in enumerate(valid):
    if index % 1024 == 0 and resource.getrusage(resource.RUSAGE_SELF).ru_maxrss > p['rss_cap_bytes']:
        raise MemoryError('self peak exceeds frozen RSS cap')
    if not active[a]:
        continue
    neighbors = [d for d in directions if active[a^d]]
    found = None
    for k, d1 in enumerate(neighbors):
        for d2 in neighbors[k+1:]:
            if active[a^d1^d2]:
                found = (d1,d2)
                break
        if found is not None:
            break
    if found is not None:
        d1,d2 = found
        active[a] = active[a^d1] = active[a^d2] = active[a^d1^d2] = 0
        groups.append(('square',a,d1,d2))
        squares += 1
square_done = time.monotonic()
pairs = singles = 0
for a in valid:
    if not active[a]:
        continue
    found = next((d for d in directions if active[a^d]), None)
    active[a] = 0
    if found is None:
        groups.append(('single',a,0,0)); singles += 1
    else:
        active[a^found] = 0
        groups.append(('pair',a,found,0)); pairs += 1
assert not any(active)
assert 4*squares+2*pairs+singles == len(valid)
with (D / 'groups_v2.tsv').open('x') as out:
    for kind,a,d1,d2 in groups:
        out.write(f'{kind}\t{a}\t{d1}\t{d2}\n')
done = time.monotonic()
old = json.loads((D / 'result.json').read_text())
r = {'status': 'PASS_EXACT_W20_AFFINE_COVER_WEIGHT2',
     'candidate_id': None, 'valid_codes': len(valid),
     'squares': squares, 'pairs': pairs, 'singles': singles,
     'groups': len(groups), 'covered_by_squares': 4*squares,
     'group_pairs_before_exclusions': len(groups)**2,
     'fixed_low_two_bit_prefixes': old['fixed_low_two_bit_nonempty_prefixes'],
     'weight1_groups': old['groups'],
     'phase_s': {'load_prior_exact_source': loaded-start,
                 'square_greedy': square_done-loaded,
                 'fallback_and_write': done-square_done},
     'wall_s': done-start,
     'self_peak_rss_bytes_darwin': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
     'protocol_sha256': sha(D/'protocol_v2.json'),
     'groups_sha256': sha(D/'groups_v2.tsv')}
with (D / 'result_v2.json').open('x') as out:
    json.dump(r,out,sort_keys=True,indent=2);out.write('\n')
print(json.dumps(r,sort_keys=True))
