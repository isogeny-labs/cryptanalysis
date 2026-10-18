"""Exact signed two-slot sum occupancy for the frozen Q1358 phi domain."""
import hashlib
import json
import resource
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / 'ecc2k130/codegen'))
import curves
import field


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def coordinates(onb, point):
    return None if point is None else (onb.toCoords(point[0]), onb.toCoords(point[1]))


def write_result(record):
    with (HERE / 'result.json').open('x') as handle:
        json.dump(record, handle, sort_keys=True, indent=2)
        handle.write('\n')


def main():
    protocol_path = HERE / 'protocol.json'
    protocol = json.loads(protocol_path.read_text())
    for label, item in protocol['sources'].items():
        assert sha(item['path']) == item['sha256'], label
    assert protocol['curve_id'] == 'EC1N131Ckb1heb5f1998f20b'
    start = time.monotonic()
    onb = field.Onb(131)
    curve = curves.Curve(onb)
    geometry = json.loads(Path(protocol['sources']['geometry']['path']).read_text())
    basis = [int(mask, 16) for mask in geometry['domain']['basis_coordinate_masks_hex']]
    assert len(basis) == 10
    masks = [0]
    for b in basis:
        masks += [v ^ b for v in masks]
    assert len(set(masks)) == 1024
    base = []
    for code, mask in enumerate(masks):
        if not mask:
            continue
        phi = onb.fromCoords(mask)
        x = onb.add(onb.inv(phi), onb.one())
        point = curve.pointFromX(x)
        if point is not None:
            assert curve.onCurve(point)
            base.append((code, point))
    assert len(base) == 532
    slot0 = [(code, point) for code, point in base]
    slot1 = [(code, curve.frob(point, 1)) for code, point in base]
    assert all(curve.onCurve(p) for _, p in slot1)
    build_seconds = time.monotonic() - start
    sums = {}
    additions = 0
    duplicate_witnesses = []
    zero_count = 0
    deadline = start + protocol['wall_cap_seconds']
    # Negating both inputs negates the sum. Thus two signs on slot 0 and
    # the positive sign on slot 1 cover all four signed combinations.
    for i, (code0, p0) in enumerate(slot0):
        for sign0, a in ((0, p0), (1, curve.neg(p0))):
            for code1, b in slot1:
                s = curve.add(a, b)
                additions += 1
                for sign1, value in ((0, s), (1, curve.neg(s))):
                    if value is None:
                        zero_count += 1
                    key = coordinates(onb, value)
                    witness = (code0, sign0 ^ sign1, code1, sign1)
                    old = sums.setdefault(key, witness)
                    if old != witness and len(duplicate_witnesses) < 16:
                        duplicate_witnesses.append((old, witness, key))
        if i % 8 == 0 and (time.monotonic() > deadline or
                           resource.getrusage(resource.RUSAGE_SELF).ru_maxrss >
                           protocol['rss_cap_bytes']):
            status = ('BOUNDED_UNKNOWN_WALL_CAP' if time.monotonic() > deadline
                      else 'BOUNDED_UNKNOWN_RSS_CAP')
            write_result({'status': status,
                          'curve_id': protocol['curve_id'],
                          'completed_first_slot_codes': i + 1,
                          'total_first_slot_codes': 532,
                          'additions': additions,
                          'distinct_partial_sums': len(sums),
                          'wall_seconds': time.monotonic() - start,
                          'protocol_sha256': sha(protocol_path)})
            return
    elapsed = time.monotonic() - start
    # Each sum occupies two sign choices; full signed Cartesian product
    # has 532^2*4 elements. The recorded witness is only for replay.
    total = len(base) * len(base) * 4
    assert additions == len(base) * len(base) * 2
    result = {'status': 'COMPLETE_EXACT_SIGNED_PAIR_OCCUPANCY',
              'curve_id': protocol['curve_id'], 'candidate_id': None,
              'slots': [0, 1], 'valid_x_lifts_per_slot': len(base),
              'signed_states_per_slot': 2 * len(base),
              'signed_pair_combinations': total,
              'group_additions': additions,
              'distinct_partial_sums': len(sums),
              'collision_excess': total - len(sums),
              'zero_sum_witnesses': zero_count,
              'first_duplicate_witnesses': duplicate_witnesses,
              'build_seconds': build_seconds,
              'wall_seconds': elapsed,
              'peak_rss_bytes': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
              'protocol_sha256': sha(protocol_path)}
    write_result(result)
    print(json.dumps({key: result[key] for key in
                      ('status', 'distinct_partial_sums', 'collision_excess',
                       'wall_seconds', 'peak_rss_bytes')}, sort_keys=True), flush=True)


if __name__ == '__main__':
    main()
