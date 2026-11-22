"""Checked-Sage execution of the exact N41 two-code quotient census."""
import hashlib
import importlib.util
import json
import time
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

from n41_gate import dual_basis

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent
SOURCE = PARENT / 'n41_n131_w29_rotation_alignment_20261017'
DESIGN = PARENT / 'n41_w9_lazy_source_20261017/circuit.py'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


spec = importlib.util.spec_from_file_location('n41_quotient_design_sage', DESIGN)
design = importlib.util.module_from_spec(spec)
spec.loader.exec_module(design)
source = json.loads((SOURCE / 'aligned_states.json').read_text())
audit = json.loads((SOURCE / 'n41_audit_result.json').read_text())
assert source['rotations'] == [0, 0, 12, 12, 24]
assert audit['state_ids'] == [105, 244, 66, 47, 111]

R = PolynomialRing(GF(2), 'u')
u = R.gen()
F = GF(2**41, name='u', modulus=u**41 + u**3 + 1)
E = EllipticCurve(F, [1, 0, 0, 0, 1])


def dec(word):
    return F(R([(int(word) >> i) & 1 for i in range(41)]))


def enc(value):
    return sum(int(coefficient) << i for i, coefficient in enumerate(value.polynomial().list()))


def pair(point):
    return [enc(point[0]), enc(point[1])]


start = time.monotonic()
states = [[E(dec(row['point'][0]), dec(row['point'][1])) for row in slot]
          for slot in source['states']]
public_raw = E(dec(source['target_raw_point'][0]), dec(source['target_raw_point'][1]))
public = E(public_raw[0]**(1 << audit['orientation']),
           public_raw[1]**(1 << audit['orientation']))
suffix = sum((states[slot][sid] for slot, sid in enumerate(audit['state_ids'][2:], 2)), E(0))
need = public - suffix
assert need == states[0][105] + states[1][244]
assert need != E(0) and need[0]

diff = [design.F.mul(v, design.F.inverse(design.C)) for v in design.PB]
dual = dual_basis([design.F.frob(v, r) for r in (0, 12, 24) for v in diff], 41)
assert len(dual) == 17
label_cache = {}
exceptional = 0


def label(point):
    global exceptional
    if point == E(0) or not point[0]:
        exceptional += 1
        return None
    x = point[0]
    if x not in label_cache:
        z = enc(1/x)
        label_cache[x] = sum(((z & v).bit_count() & 1) << i for i, v in enumerate(dual))
    return label_cache[x]


target_label = label(need)
build_start = time.monotonic()
families = []
histogram = {}
for i in range(71):
    for j in range(i + 1, 71):
        labels = set()
        points = set()
        for a in states[0][4*i:4*i+4]:
            for b in states[1][4*j:4*j+4]:
                q = a + b
                points.add(q)
                value = label(q)
                if value is not None:
                    labels.add(value)
        families.append((labels, points))
        histogram[len(labels)] = histogram.get(len(labels), 0) + 1
build_seconds = time.monotonic() - build_start
query_start = time.monotonic()
label_hits = [i for i, (labels, _) in enumerate(families) if target_label in labels]
label_query_seconds = time.monotonic() - query_start
exact_start = time.monotonic()
exact_hits = [i for i, (_, points) in enumerate(families) if need in points]
exact_query_seconds = time.monotonic() - exact_start
witness_index = sum(71-i-1 for i in range(105//4)) + (244//4 - 105//4 - 1)
assert witness_index in label_hits and witness_index in exact_hits
assert set(exact_hits).issubset(label_hits)
result = {
    'status': 'PASS_EXACT_N41_TWO_CODE_QUOTIENT_GATE',
    'curve_id': source['curve_id'], 'rotations': source['rotations'],
    'target_orientation': audit['orientation'], 'public_target': pair(public),
    'fixed_suffix_state_ids': audit['state_ids'][2:],
    'required_partial_point': pair(need), 'target_label': target_label,
    'dual_masks': dual, 'quotient_bits': len(dual),
    'two_code_families': len(families),
    'family_x_label_cardinality_histogram': dict(sorted(histogram.items())),
    'exceptional_partial_assignments': exceptional,
    'quotient_surviving_families': len(label_hits),
    'exact_surviving_families': len(exact_hits),
    'quotient_surviving_indices': label_hits,
    'exact_surviving_indices': exact_hits,
    'witness_family_index': witness_index,
    'partial_additions': 16*len(families),
    'distinct_partial_x_values': len(label_cache),
    'precompute_seconds': build_seconds,
    'online_quotient_lookup_seconds': label_query_seconds,
    'online_exact_lookup_seconds': exact_query_seconds,
    'total_seconds': time.monotonic() - start,
    'source_sha256': {name: sha(path) for name, path in {
        'script': Path(__file__), 'design': DESIGN,
        'states': SOURCE / 'aligned_states.json',
        'audit': SOURCE / 'n41_audit_result.json',
        'runtime': HERE / 'sage_runtime_info.json'}.items()},
}
(HERE / 'n41_result.json').write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
print(json.dumps({key: result[key] for key in (
    'status', 'two_code_families', 'family_x_label_cardinality_histogram',
    'quotient_surviving_families', 'exact_surviving_families',
    'precompute_seconds', 'total_seconds')}))
