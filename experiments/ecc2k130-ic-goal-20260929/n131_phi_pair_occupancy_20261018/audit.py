"""Independent direct four-sign enumeration of the Q1358 two-slot domain."""
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


def main():
    cfg = json.loads((HERE / 'audit_protocol.json').read_text())
    for name, item in cfg['sources'].items():
        assert sha(item['path']) == item['sha256'], name
    result = json.loads((HERE / 'result.json').read_text())
    assert result['status'] == 'COMPLETE_EXACT_SIGNED_PAIR_OCCUPANCY'
    geometry = json.loads(Path(cfg['sources']['geometry']['path']).read_text())
    onb = field.Onb(131)
    curve = curves.Curve(onb)
    basis = [int(v, 16) for v in geometry['domain']['basis_coordinate_masks_hex']]
    start = time.monotonic()

    def make_slot(shift):
        points = []
        for code in range(1 << len(basis)):
            mask = 0
            for bit, basis_mask in enumerate(basis):
                if (code >> bit) & 1:
                    mask ^= basis_mask
            if not mask:
                continue
            phi = onb.frob(onb.fromCoords(mask), shift)
            point = curve.pointFromX(onb.add(onb.inv(phi), onb.one()))
            if point is not None:
                points.append((code, point))
        return points

    left = make_slot(0)
    right = make_slot(1)
    assert len(left) == len(right) == 532
    seen = set()
    combinations = 0
    first_collision = None
    for code0, p in left:
        for code1, q in right:
            for a in (p, curve.neg(p)):
                for b in (q, curve.neg(q)):
                    summed = curve.add(a, b)
                    key = None if summed is None else (onb.toCoords(summed[0]), onb.toCoords(summed[1]))
                    if key in seen and first_collision is None:
                        first_collision = [code0, code1, key]
                    seen.add(key)
                    combinations += 1
    assert combinations == 532 * 532 * 4
    assert len(seen) == result['distinct_partial_sums']
    assert combinations - len(seen) == result['collision_excess']
    audit = {'status': 'PASS_INDEPENDENT_DIRECT_PAIR_ENUMERATION',
             'curve_id': cfg['curve_id'],
             'combinations': combinations,
             'distinct_partial_sums': len(seen),
             'collision_excess': combinations - len(seen),
             'first_collision': first_collision,
             'wall_seconds': time.monotonic() - start,
             'peak_rss_bytes': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
             'audit_protocol_sha256': sha(HERE / 'audit_protocol.json'),
             'result_sha256': sha(HERE / 'result.json')}
    with (HERE / 'audit_result.json').open('x') as handle:
        json.dump(audit, handle, sort_keys=True, indent=2)
        handle.write('\n')
    print(json.dumps({k: audit[k] for k in ('status', 'distinct_partial_sums',
                                             'collision_excess', 'wall_seconds')}, sort_keys=True))


if __name__ == '__main__':
    main()
