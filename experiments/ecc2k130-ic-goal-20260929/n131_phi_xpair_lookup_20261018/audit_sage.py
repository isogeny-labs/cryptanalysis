"""Independent four-sign replay of the Q1358 x-quotient pair key set."""
import hashlib
import json
import random
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


def point_for(onb, curve, basis, code, pos):
    mask = 0
    for bit, b in enumerate(basis):
        if code >> bit & 1:
            mask ^= b
    phi = onb.frob(onb.fromCoords(mask), pos)
    point = curve.pointFromX(onb.add(onb.inv(phi), onb.one()))
    assert point is not None
    return point


def keyset_sha(keys):
    h = hashlib.sha256()
    for key in sorted(keys):
        h.update(int(key).to_bytes(17, 'big'))
    return h.hexdigest()


def main():
    cfg_path = HERE / 'protocol.json'
    cfg = json.loads(cfg_path.read_text())
    for name, item in cfg['sources'].items():
        assert sha(item['path']) == item['sha256'], name
    full = json.loads((HERE / 'full_result.json').read_text())
    xrun = json.loads((HERE / 'x_result.json').read_text())
    assert full['status'] == xrun['status'] == 'COMPLETE_EXACT_PAIR_LOOKUP'
    assert full['protocol_sha256'] == xrun['protocol_sha256'] == sha(cfg_path)
    assert full['index_entries'] == 1132096 and xrun['index_entries'] == 566048
    start = time.monotonic()
    onb = field.Onb(131)
    curve = curves.Curve(onb)
    geometry = json.loads(Path(cfg['sources']['geometry']['path']).read_text())
    basis = [int(v, 16) for v in geometry['domain']['basis_coordinate_masks_hex']]
    codes = []
    for code in range(1, 1024):
        mask = 0
        for bit, b in enumerate(basis):
            if code >> bit & 1:
                mask ^= b
        if curve.pointFromX(onb.add(onb.inv(onb.fromCoords(mask)), onb.one())) is not None:
            codes.append(code)
    assert len(codes) == 532
    slot0 = [(code, point_for(onb, curve, basis, code, 0)) for code in codes]
    slot1 = [(code, point_for(onb, curve, basis, code, 1)) for code in codes]
    xkeys = set()
    point_keys = set()
    additions = 0
    for _, p0 in slot0:
        for signed0 in (p0, curve.neg(p0)):
            for _, p1 in slot1:
                for signed1 in (p1, curve.neg(p1)):
                    result = curve.add(signed0, signed1)
                    assert result is not None
                    x, y = onb.toCoords(result[0]), onb.toCoords(result[1])
                    xkeys.add(x)
                    point_keys.add((x, y))
                    additions += 1
    assert additions == len(point_keys) == 1132096
    assert len(xkeys) == 566048
    digest = keyset_sha(xkeys)
    assert digest == full['x_keyset_sha256'] == xrun['x_keyset_sha256']
    by_code = dict(slot0)
    rng = random.Random(cfg['positive_seed'])
    for i in range(cfg['positive_query_count']):
        code0, code1 = rng.choice(slot0)[0], rng.choice(slot0)[0]
        sign0, sign1 = rng.randrange(2), rng.randrange(2)
        p0, p1 = by_code[code0], slot1[codes.index(code1)][1]
        if sign0:
            p0 = curve.neg(p0)
        if sign1:
            p1 = curve.neg(p1)
        target = curve.add(p0, p1)
        assert onb.toCoords(target[0]) in xkeys
        if i < 8:
            expected = [code0, sign0, code1, sign1]
            for run in (full, xrun):
                record = run['positive_receipts'][i]
                assert record['input_witness'] == record['returned_witness'] == expected
                assert record['target_coordinates'] == [onb.toCoords(target[0]),
                                                        onb.toCoords(target[1])]
    public_fiber = [tuple(onb.fromCoords(int(v)) for v in rec['target_coordinates'])
                    for rec in geometry['official_single_target_cofactor_fiber']['four_verified_lifts']]
    rng = random.Random(cfg['ordinary_query_seed'])
    h = hashlib.sha256()
    ordinary_x_hits = 0
    for _ in range(cfg['ordinary_right_family_count']):
        right = None
        for pos in (12, 13, 14):
            code = rng.choice(slot0)[0]
            point = point_for(onb, curve, basis, code, pos)
            if rng.randrange(2):
                point = curve.neg(point)
            right = curve.add(right, point)
        for endpoint in public_fiber:
            residual = curve.add(endpoint, curve.neg(right))
            x, y = onb.toCoords(residual[0]), onb.toCoords(residual[1])
            h.update(x.to_bytes(17, 'big') + y.to_bytes(17, 'big'))
            ordinary_x_hits += int(x in xkeys)
    assert h.hexdigest() == full['ordinary_query_key_stream_sha256'] == xrun['ordinary_query_key_stream_sha256']
    assert len(full['ordinary_hits']) == len(xrun['ordinary_hits']) == 0
    assert ordinary_x_hits == 0
    result = {'status': 'PASS_INDEPENDENT_FOUR_SIGN_KEYSET_AND_QUERY_REPLAY',
              'pair_additions': additions, 'point_keys': len(point_keys),
              'x_keys': len(xkeys), 'x_keyset_sha256': digest,
              'ordinary_target_keys': cfg['ordinary_right_family_count'] * 4,
              'ordinary_x_key_hits': ordinary_x_hits,
              'audit_seconds': time.monotonic() - start,
              'peak_rss_bytes': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
              'protocol_sha256': sha(cfg_path)}
    with (HERE / 'audit_result.json').open('x') as out:
        json.dump(result, out, sort_keys=True, indent=2)
        out.write('\n')
    print(json.dumps({key: result[key] for key in
                      ('status', 'pair_additions', 'point_keys', 'x_keys',
                       'ordinary_x_key_hits', 'audit_seconds', 'peak_rss_bytes')},
                     sort_keys=True))


if __name__ == '__main__':
    main()
