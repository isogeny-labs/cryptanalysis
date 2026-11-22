"""Independent point and opposite-pivot replay of the quadratic rank witness."""
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


def point_for_code(onb, curve, basis, code, position):
    mask = 0
    for i in range(len(basis)):
        if code & (1 << i):
            mask ^= basis[i]
    assert mask != 0
    phi = onb.frob(onb.fromCoords(mask), position)
    point = curve.pointFromX(onb.add(onb.inv(phi), onb.one()))
    assert point is not None and curve.onCurve(point)
    return point


def feature_row(x):
    row = 1
    for i in range(131):
        if (x >> i) & 1:
            row ^= 1 << (i + 1)
    column = 132
    for i in range(131):
        for j in range(i + 1, 131):
            if (x >> i) & (x >> j) & 1:
                row ^= 1 << column
            column += 1
    assert column == 8647
    return row


def main():
    cfg = json.loads((HERE / 'audit_protocol.json').read_text())
    assert cfg['status'] == 'FROZEN_BEFORE_AUDIT'
    for name, entry in cfg['sources'].items():
        assert sha(entry['path']) == entry['sha256'], name
    witness = json.loads(Path(cfg['sources']['witness']['path']).read_text())
    source_result = json.loads(Path(cfg['sources']['result']['path']).read_text())
    assert source_result['status'] == 'FULL_RANK' and len(witness) == 8647
    onb = field.Onb(131)
    curve = curves.Curve(onb)
    geo = json.loads(Path(cfg['sources']['geometry']['path']).read_text())
    basis = [int(v, 16) for v in geo['domain']['basis_coordinate_masks_hex']]
    valid = set()
    for code in range(1, 1024):
        mask = 0
        for bit, b in enumerate(basis):
            if code >> bit & 1:
                mask ^= b
        if not mask:
            continue
        phi = onb.fromCoords(mask)
        if curve.pointFromX(onb.add(onb.inv(phi), onb.one())) is not None:
            valid.add(code)
    assert len(valid) == 532
    pivots = {}
    seen = set()
    start = time.monotonic()
    for code0, sign0, code1, xhex in witness:
        assert code0 in valid and code1 in valid and sign0 in (0, 1)
        p0 = point_for_code(onb, curve, basis, code0, 0)
        p1 = point_for_code(onb, curve, basis, code1, 1)
        if sign0:
            p0 = curve.neg(p0)
        summed = curve.add(p0, p1)
        assert summed is not None and curve.onCurve(summed)
        x = onb.toCoords(summed[0])
        assert x == int(xhex, 16) and x not in seen
        seen.add(x)
        row = feature_row(x)
        while row:
            bit = (row & -row).bit_length() - 1
            old = pivots.get(bit)
            if old is None:
                pivots[bit] = row
                break
            row ^= old
        else:
            raise AssertionError('dependent audit row')
    result = {
        'status': 'PASS_INDEPENDENT_LOW_PIVOT_REPLAY',
        'rank': len(pivots), 'feature_dimension': 8647,
        'replayed_witnesses': len(witness), 'unique_x': len(seen),
        'wall_seconds': time.monotonic() - start,
        'peak_rss_bytes': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    }
    assert result['rank'] == 8647
    (HERE / 'audit_result.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps(result, sort_keys=True), flush=True)


if __name__ == '__main__':
    main()
