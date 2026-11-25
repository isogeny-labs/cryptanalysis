"""Cover exact W20 valid codes with disjoint affine 2-flats, then pairs."""
import hashlib
import json
import resource
import signal
import time
from pathlib import Path

D = Path(__file__).resolve().parent
SOURCE = D.parent / 'n131_w20_sevenpair_gate_20261010'
BASE = D.parent / 'n131_symbolic_rect_projection_20261015'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
protocol = json.loads((D / 'protocol.json').read_text())
signal.alarm(protocol['wall_cap_s'])
assert sha(D / 'run.py') == protocol['source_sha256']['worker']
assert sha(SOURCE / 'support_w20.tsv') == protocol['source_sha256']['support']
assert sha(SOURCE / 'count_result_v2.json') == protocol['source_sha256']['count']
assert sha(BASE / 'prefix_result.json') == protocol['source_sha256']['prefix_result']
start = time.monotonic()
support = {}
for line in (SOURCE / 'support_w20.tsv').open():
    mask, column, _ = map(int, line.split())
    support[mask] = column
seed = protocol['selected_seed_mask']
pivot = seed.bit_length() - 1
bits = [i for i in range(20) if i != pivot]
valid = []
for mask, column in support.items():
    mate = mask ^ seed
    if mask < mate and mate in support and column != support[mate]:
        valid.append(sum(((mask >> bit) & 1) << i for i, bit in enumerate(bits)))
valid.sort()
assert len(valid) == protocol['expected_valid_codes'] == len(set(valid))
loaded = time.monotonic()
active = bytearray(1 << 19)
for code in valid:
    active[code] = 1
groups = []
squares = 0
for index, a in enumerate(valid):
    if index % 1024 == 0 and resource.getrusage(resource.RUSAGE_SELF).ru_maxrss > protocol['rss_cap_bytes']:
        raise MemoryError('self peak exceeds frozen RSS cap')
    if not active[a]:
        continue
    selected = None
    for i in range(19):
        b = a ^ (1 << i)
        if not active[b]:
            continue
        for j in range(i + 1, 19):
            c = a ^ (1 << j)
            d = b ^ (1 << j)
            if active[c] and active[d]:
                selected = (a, b, c, d, i, j)
                break
        if selected is not None:
            break
    if selected is not None:
        a, b, c, d, i, j = selected
        active[a] = active[b] = active[c] = active[d] = 0
        groups.append(('square', a, i, j))
        squares += 1
square_done = time.monotonic()
pairs = singles = 0
for a in valid:
    if not active[a]:
        continue
    neighbor = -1
    for i in range(19):
        b = a ^ (1 << i)
        if active[b]:
            neighbor = i
            active[b] = 0
            break
    active[a] = 0
    if neighbor >= 0:
        groups.append(('pair', a, neighbor, -1))
        pairs += 1
    else:
        groups.append(('single', a, -1, -1))
        singles += 1
assert 4 * squares + 2 * pairs + singles == len(valid)
assert not any(active)
with (D / 'groups.tsv').open('x') as out:
    for kind, a, i, j in groups:
        out.write(f'{kind}\t{a}\t{i}\t{j}\n')
done = time.monotonic()
prefix = json.loads((BASE / 'prefix_result.json').read_text())
record = {'status': 'PASS_EXACT_W20_AFFINE_COVER', 'candidate_id': None,
          'curve_id': protocol['curve_id'], 'valid_codes': len(valid),
          'squares': squares, 'pairs': pairs, 'singles': singles,
          'groups': len(groups), 'fixed_low_two_bit_nonempty_prefixes': prefix['nonempty_prefixes_per_slot'],
          'covered_by_squares': 4 * squares,
          'full_cartesian_group_pairs_before_exclusions': len(groups)**2,
          'phase_s': {'source_load': loaded - start, 'square_greedy': square_done - loaded,
                      'pair_fallback_and_write': done - square_done},
          'wall_s': done - start,
          'self_peak_rss_bytes_darwin': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
          'protocol_sha256': sha(D / 'protocol.json'),
          'groups_sha256': sha(D / 'groups.tsv')}
with (D / 'result.json').open('x') as out:
    json.dump(record, out, sort_keys=True, indent=2); out.write('\n')
print(json.dumps(record, sort_keys=True))
