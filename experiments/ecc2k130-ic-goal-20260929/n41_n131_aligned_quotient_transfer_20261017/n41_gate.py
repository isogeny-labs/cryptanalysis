"""Exact two-code-family quotient gate on the frozen aligned N41 source."""
import hashlib
import importlib.util
import json
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent
SOURCE = PARENT / 'n41_n131_w29_rotation_alignment_20261017'
DESIGN = PARENT / 'n41_w9_lazy_source_20261017/circuit.py'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rank_basis(values):
    pivots = {}
    for value in values:
        while value:
            k = value.bit_length() - 1
            if k not in pivots:
                pivots[k] = value
                break
            value ^= pivots[k]
    return pivots


def dual_basis(values, n):
    rows = rank_basis(values)
    out = []
    for bit in range(n):
        if bit in rows:
            continue
        v = 1 << bit
        for pivot in sorted(rows):
            if (v & rows[pivot]).bit_count() & 1:
                v |= 1 << pivot
        assert all(not ((v & x).bit_count() & 1) for x in values)
        out.append(v)
    return out


def run():
    start = time.monotonic()
    spec = importlib.util.spec_from_file_location('n41_gate_design', DESIGN)
    design = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(design)
    F = design.F
    source = json.loads((SOURCE / 'aligned_states.json').read_text())
    audit = json.loads((SOURCE / 'n41_audit_result.json').read_text())
    assert source['rotations'] == [0, 0, 12, 12, 24]
    assert audit['status'] == 'PASS_INDEPENDENT_N41_ALIGNED_PUBLIC_RELATION'
    assert audit['state_ids'][:2] == [105, 244]

    def add(a, b):
        if a is None:
            return b
        if b is None:
            return a
        x1, y1 = a
        x2, y2 = b
        if x1 == x2:
            if y1 != y2 or x1 == 0:
                return None
            lam = x1 ^ F.mul(y1, F.inverse(x1))
            x3 = F.square(lam) ^ lam
            y3 = F.square(x1) ^ F.mul(lam ^ 1, x3)
        else:
            lam = F.mul(y1 ^ y2, F.inverse(x1 ^ x2))
            x3 = F.square(lam) ^ lam ^ x1 ^ x2
            y3 = F.mul(lam, x1 ^ x3) ^ x3 ^ y1
        return (x3, y3)

    def neg(point):
        return None if point is None else (point[0], point[1] ^ point[0])

    def frob(point, n):
        return tuple(F.frob(x, n) for x in point)

    def on_curve(point):
        if point is None:
            return True
        x, y = point
        return F.square(y) ^ F.mul(x, y) == F.mul(F.square(x), x) ^ 1

    states = [[tuple(row['point']) for row in slot] for slot in source['states']]
    assert all(on_curve(p) for slot in states for p in slot)
    public = frob(tuple(source['target_raw_point']), audit['orientation'])
    suffix = None
    for slot, sid in enumerate(audit['state_ids'][2:], 2):
        suffix = add(suffix, states[slot][sid])
    need = add(public, neg(suffix))
    assert need == add(states[0][105], states[1][244]) and need is not None
    assert need[0]

    diff = [F.mul(v, F.inverse(design.C)) for v in design.PB]
    dual = dual_basis([F.frob(v, r) for r in (0, 12, 24) for v in diff], 41)
    assert len(dual) == 17

    def label(point):
        if point is None or not point[0]:
            return None
        z = F.inverse(point[0])
        return sum(((z & v).bit_count() & 1) << i for i, v in enumerate(dual))

    target_label = label(need)
    assert target_label is not None
    build_start = time.monotonic()
    family_labels = []
    family_points = []
    exceptional = 0
    distinct_hist = {}
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
            family_labels.append(labels)
            family_points.append(points)
            distinct_hist[len(labels)] = distinct_hist.get(len(labels), 0) + 1
    build_seconds = time.monotonic() - build_start
    query_start = time.monotonic()
    label_hits = [k for k, labels in enumerate(family_labels) if target_label in labels]
    label_query_seconds = time.monotonic() - query_start
    exact_start = time.monotonic()
    exact_hits = [k for k, points in enumerate(family_points) if need in points]
    exact_query_seconds = time.monotonic() - exact_start
    witness_index = sum(71 - i - 1 for i in range(105//4)) + (244//4 - 105//4 - 1)
    assert witness_index in label_hits and witness_index in exact_hits
    assert set(exact_hits).issubset(label_hits)
    result = {
        'status': 'PASS_EXACT_N41_TWO_CODE_QUOTIENT_GATE',
        'curve_id': source['curve_id'], 'rotations': source['rotations'],
        'target_orientation': audit['orientation'],
        'public_target': list(public), 'fixed_suffix_state_ids': audit['state_ids'][2:],
        'required_partial_point': list(need), 'target_label': target_label,
        'dual_masks': dual, 'quotient_bits': len(dual),
        'two_code_families': len(family_labels),
        'family_x_label_cardinality_histogram': dict(sorted(distinct_hist.items())),
        'exceptional_partial_assignments': exceptional,
        'quotient_surviving_families': len(label_hits),
        'exact_surviving_families': len(exact_hits),
        'quotient_surviving_indices': label_hits,
        'exact_surviving_indices': exact_hits,
        'witness_family_index': witness_index,
        'partial_additions': 16*len(family_labels),
        'precompute_seconds': build_seconds,
        'online_quotient_lookup_seconds': label_query_seconds,
        'online_exact_lookup_seconds': exact_query_seconds,
        'total_seconds': time.monotonic() - start,
        'source_sha256': {name: sha(path) for name, path in {
            'script': Path(__file__), 'design': DESIGN,
            'states': SOURCE / 'aligned_states.json',
            'audit': SOURCE / 'n41_audit_result.json'}.items()},
    }
    (HERE / 'n41_result.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps({key: result[key] for key in (
        'status', 'two_code_families', 'family_x_label_cardinality_histogram',
        'quotient_surviving_families', 'exact_surviving_families',
        'precompute_seconds', 'total_seconds')}))


if __name__ == '__main__':
    run()
