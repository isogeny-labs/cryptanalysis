"""Independent opposite-pivot audit of four target-translated certificates."""
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
    for i, b in enumerate(basis):
        if code >> i & 1:
            mask ^= b
    assert mask
    phi = onb.frob(onb.fromCoords(mask), position)
    point = curve.pointFromX(onb.add(onb.inv(phi), onb.one()))
    assert point is not None and curve.onCurve(point)
    return point


def feature_row(x):
    indices = [i for i in range(131) if x >> i & 1]
    row = 1
    for i in indices:
        row += 1 << (i + 1)
    offsets = []
    cursor = 132
    for i in range(131):
        offsets.append(cursor)
        cursor += 130 - i
    for i in indices:
        for j in indices:
            if i < j:
                column = offsets[i] + j - i - 1
                row += 1 << column
    return row


def main():
    cfg = json.loads((HERE / 'translated_audit_protocol.json').read_text())
    assert cfg['status'] == 'FROZEN_BEFORE_TRANSLATED_AUDIT'
    for name, item in cfg['sources'].items():
        assert sha(item['path']) == item['sha256'], name
    initial = json.loads(Path(cfg['sources']['witness']['path']).read_text())
    extra = json.loads(Path(cfg['sources']['extra']['path']).read_text())
    witness = initial + extra
    indices = json.loads(Path(cfg['sources']['indices']['path']).read_text())
    assert len(indices) == 4 and all(len(row) == 8647 for row in indices)
    onb = field.Onb(131)
    curve = curves.Curve(onb)
    geo = json.loads(Path(cfg['sources']['geometry']['path']).read_text())
    basis = [int(v, 16) for v in geo['domain']['basis_coordinate_masks_hex']]
    endpoints = [tuple(onb.fromCoords(int(v)) for v in record['target_coordinates'])
                 for record in geo['official_single_target_cofactor_fiber']['four_verified_lifts']]
    assert len(endpoints) == 4
    cache = {}

    def pair_sum(k):
        if k not in cache:
            code0, sign0, code1, xhex = witness[k]
            p0 = point_for_code(onb, curve, basis, code0, 0)
            p1 = point_for_code(onb, curve, basis, code1, 1)
            if sign0:
                p0 = curve.neg(p0)
            summed = curve.add(p0, p1)
            assert summed is not None and curve.onCurve(summed)
            assert onb.toCoords(summed[0]) == int(xhex, 16)
            cache[k] = summed
        return cache[k]

    start = time.monotonic()
    ranks = []
    for endpoint_index, endpoint in enumerate(endpoints):
        pivots = {}
        for k in indices[endpoint_index]:
            residual = curve.add(endpoint, curve.neg(pair_sum(k)))
            assert residual is not None and curve.onCurve(residual)
            row = feature_row(onb.toCoords(residual[0]))
            while row:
                bit = (row & -row).bit_length() - 1
                old = pivots.get(bit)
                if old is None:
                    pivots[bit] = row
                    break
                row ^= old
            else:
                raise AssertionError((endpoint_index, k, 'dependent row'))
        ranks.append(len(pivots))
    assert ranks == [8647] * 4
    result = {'status':'PASS_FOUR_TRANSLATED_LOW_PIVOT_REPLAYS',
              'rank_by_lift':ranks,'feature_dimension':8647,
              'distinct_pair_witnesses_reconstructed':len(cache),
              'wall_seconds':time.monotonic()-start,
              'peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    (HERE/'translated_audit_result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(result,sort_keys=True),flush=True)


if __name__ == '__main__':
    main()
