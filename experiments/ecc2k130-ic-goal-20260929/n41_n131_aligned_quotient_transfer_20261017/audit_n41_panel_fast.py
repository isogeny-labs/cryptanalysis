"""Independent integer-field replay of the full N41 two-code census."""
import hashlib
import json
import random
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / 'n41_n131_w29_rotation_alignment_20261017'
MOD = (1 << 41) | (1 << 3) | 1


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def mul(a, b):
    result = 0
    while b:
        if b & 1:
            result ^= a
        b >>= 1
        a <<= 1
        if a & (1 << 41):
            a ^= MOD
    return result


def inv(a):
    assert a
    x, y = a, MOD
    u, v = 1, 0
    while x != 1:
        k = x.bit_length() - y.bit_length()
        if k < 0:
            x, y = y, x
            u, v = v, u
            k = -k
        x ^= y << k
        u ^= v << k
    while u.bit_length() > 41:
        u ^= MOD << (u.bit_length() - 42)
    assert mul(a, u) == 1
    return u


def add(p, q):
    if p is None:
        return q
    if q is None:
        return p
    x1, y1 = p
    x2, y2 = q
    if x1 == x2:
        if y1 != y2 or x1 == 0:
            return None
        slope = x1 ^ mul(y1, inv(x1))
        x3 = mul(slope, slope) ^ slope
        y3 = mul(x1, x1) ^ mul(slope ^ 1, x3)
    else:
        slope = mul(y1 ^ y2, inv(x1 ^ x2))
        x3 = mul(slope, slope) ^ slope ^ x1 ^ x2
        y3 = mul(slope, x1 ^ x3) ^ x3 ^ y1
    return (x3, y3)


def frob(p, n):
    x, y = p
    for _ in range(n):
        x, y = mul(x, x), mul(y, y)
    return (x, y)


def curve(p):
    if p is None:
        return True
    x, y = p
    return mul(y, y) ^ mul(x, y) == mul(mul(x, x), x) ^ 1


start = time.monotonic()
protocol = json.loads((HERE / 'n41_panel_protocol.json').read_text())
producer = json.loads((HERE / 'n41_panel_result.json').read_text())
source = json.loads((SOURCE / 'aligned_states.json').read_text())
audit = json.loads((SOURCE / 'n41_audit_result.json').read_text())
assert sha(HERE / 'n41_gate_panel_sage.py') == protocol['source_sha256']['script']
assert sha(SOURCE / 'aligned_states.json') == protocol['source_sha256']['states']
assert sha(SOURCE / 'n41_audit_result.json') == protocol['source_sha256']['public_witness_audit']
states = [[tuple(row['point']) for row in slot] for slot in source['states']]
assert all(curve(p) for slot in states for p in slot)
for slot in states[:2]:
    for i in range(71):
        rows = source['states'][0 if slot is states[0] else 1][4*i:4*i+4]
        assert len({tuple(row['masks']) for row in rows}) == 1
        assert len({tuple(row['columns']) for row in rows}) == 1
public = frob(tuple(source['target_raw_point']), audit['orientation'])
suffix = None
for slot, sid in enumerate(audit['state_ids'][2:], 2):
    suffix = add(suffix, states[slot][sid])
need = add(public, None if suffix is None else (suffix[0], suffix[1] ^ suffix[0]))
assert need == add(states[0][105], states[1][244])
assert list(need) == producer['required_partial_point']
dual = producer['dual_masks']
assert len(dual) == 17 and len(set(dual)) == 17


def label(p):
    if p is None or p[0] == 0:
        return None
    z = inv(p[0])
    return sum(((z & mask).bit_count() & 1) << i for i, mask in enumerate(dual))


target_label = label(need)
assert target_label == producer['target_label']
histogram = {}
label_hits = []
exact_hits = []
exceptional = 0
families = []
for i in range(71):
    for j in range(i + 1, 71):
        labels = set()
        points = set()
        for a in states[0][4*i:4*i+4]:
            for b in states[1][4*j:4*j+4]:
                q = add(a, b)
                points.add(q)
                value = label(q)
                if value is None:
                    exceptional += 1
                else:
                    labels.add(value)
        index = sum(71-h-1 for h in range(i)) + (j-i-1)
        histogram[len(labels)] = histogram.get(len(labels), 0) + 1
        families.append((labels, points))
        if target_label in labels:
            label_hits.append(index)
        if need in points:
            exact_hits.append(index)
assert histogram == {int(k): v for k, v in producer['family_x_label_cardinality_histogram'].items()}
assert label_hits == producer['quotient_surviving_indices']
assert exact_hits == producer['exact_surviving_indices']
assert exceptional == producer['exceptional_partial_assignments']
rng = random.Random(202610171902)
panel = []
draws = 0
while len(panel) < 64:
    ids = [rng.randrange(284) for _ in range(3)]
    draws += 1
    columns = [column for slot, sid in enumerate(ids, 2)
               for column in source['states'][slot][sid]['columns']]
    if len(set(columns)) != 6:
        continue
    selected = None
    for slot, sid in enumerate(ids, 2):
        selected = add(selected, states[slot][sid])
    required = public if selected is None else add(
        public, (selected[0], selected[1] ^ selected[0]))
    if required is None or required[0] == 0:
        continue
    selected_label = label(required)
    label_count = sum(selected_label in labels for labels, _ in families)
    exact_count = sum(required in points for _, points in families)
    panel.append({'suffix_state_ids': ids, 'required_partial_point': list(required),
                  'required_label': selected_label,
                  'quotient_surviving_families': label_count,
                  'exact_surviving_families': exact_count})
assert panel == producer['miss_panel']
assert draws == producer['miss_panel_draws']
result = {
    'status': 'PASS_INDEPENDENT_N41_QUOTIENT_SUFFIX_PANEL',
    'families': sum(histogram.values()), 'histogram': histogram,
    'label_hits': label_hits, 'exact_hits': exact_hits,
    'exceptional_partial_assignments': exceptional,
    'miss_panel_draws': draws,
    'miss_panel_quotient_survivors': sum(row['quotient_surviving_families'] for row in panel),
    'miss_panel_exact_survivors': sum(row['exact_surviving_families'] for row in panel),
    'elapsed_seconds': time.monotonic() - start,
    'source_sha256': {'script': sha(Path(__file__)),
                      'producer': sha(HERE / 'n41_panel_result.json'),
                      'protocol': sha(HERE / 'n41_panel_protocol.json'),
                      'states': sha(SOURCE / 'aligned_states.json')},
}
(HERE / 'n41_panel_audit_result.json').write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
print(json.dumps(result, sort_keys=True))
