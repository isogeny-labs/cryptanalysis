"""Exact full-point and negation-quotiented pair indexes on frozen Q1358."""
import argparse
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


def coords(onb, point):
    return None if point is None else (onb.toCoords(point[0]), onb.toCoords(point[1]))


def digest_keys(keys):
    h = hashlib.sha256()
    for key in sorted(keys):
        h.update(int(key).to_bytes(17, 'big'))
    return h.hexdigest()


def code_point(onb, curve, basis, code, position):
    mask = 0
    for bit, b in enumerate(basis):
        if code >> bit & 1:
            mask ^= b
    phi = onb.frob(onb.fromCoords(mask), position)
    point = curve.pointFromX(onb.add(onb.inv(phi), onb.one()))
    assert point is not None
    return point


def build_base(onb, curve, basis):
    base = []
    for code in range(1024):
        mask = 0
        for bit, b in enumerate(basis):
            if code >> bit & 1:
                mask ^= b
        if not mask:
            continue
        phi = onb.fromCoords(mask)
        point = curve.pointFromX(onb.add(onb.inv(phi), onb.one()))
        if point is not None:
            assert curve.onCurve(point)
            base.append((code, point))
    assert len(base) == 532
    return base


def lookup(onb, curve, index, mode, target, base_by_code):
    key = coords(onb, target)
    if mode == 'full':
        witness = index.get(key)
        if witness is None:
            return None
        code0, sign0, code1, sign1 = witness
    else:
        entry = index.get(key[0])
        if entry is None:
            return None
        code0, sign0, code1, stored_y = entry
        sign1 = 0
        if key[1] != stored_y:
            sign0 ^= 1
            sign1 = 1
    p0 = base_by_code[code0]
    p1 = curve.frob(base_by_code[code1], 1)
    if sign0:
        p0 = curve.neg(p0)
    if sign1:
        p1 = curve.neg(p1)
    assert curve.add(p0, p1) == target
    return (code0, sign0, code1, sign1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=('full', 'x'), required=True)
    args = parser.parse_args()
    protocol_path = HERE / 'protocol.json'
    cfg = json.loads(protocol_path.read_text())
    assert cfg['status'] == 'FROZEN_BEFORE_INDEX'
    for name, item in cfg['sources'].items():
        assert sha(item['path']) == item['sha256'], name
    start = time.monotonic()
    onb = field.Onb(131)
    curve = curves.Curve(onb)
    geometry = json.loads(Path(cfg['sources']['geometry']['path']).read_text())
    basis = [int(v, 16) for v in geometry['domain']['basis_coordinate_masks_hex']]
    base = build_base(onb, curve, basis)
    base_by_code = dict(base)
    slot1 = [(code, curve.frob(point, 1)) for code, point in base]
    index = {}
    additions = 0
    for i, (code0, raw0) in enumerate(base):
        for sign0, p0 in ((0, raw0), (1, curve.neg(raw0))):
            for code1, p1 in slot1:
                summed = curve.add(p0, p1)
                assert summed is not None
                x, y = coords(onb, summed)
                if args.mode == 'x':
                    assert x not in index
                    index[x] = (code0, sign0, code1, y)
                else:
                    neg = curve.neg(summed)
                    nk = coords(onb, neg)
                    assert (x, y) not in index and nk not in index
                    index[(x, y)] = (code0, sign0, code1, 0)
                    index[nk] = (code0, sign0 ^ 1, code1, 1)
                additions += 1
        if i % 8 == 0 and (time.monotonic() - start > cfg['build_wall_cap_seconds'] or
                          resource.getrusage(resource.RUSAGE_SELF).ru_maxrss > cfg['rss_cap_bytes']):
            status = ('BOUNDED_UNKNOWN_BUILD_WALL_CAP' if
                      time.monotonic() - start > cfg['build_wall_cap_seconds'] else
                      'BOUNDED_UNKNOWN_RSS_CAP')
            result = {'status': status, 'mode': args.mode,
                      'completed_first_slot_codes': i + 1, 'additions': additions,
                      'entries': len(index), 'wall_seconds': time.monotonic() - start,
                      'protocol_sha256': sha(protocol_path)}
            with (HERE / (args.mode + '_result.json')).open('x') as out:
                json.dump(result, out, sort_keys=True, indent=2)
                out.write('\n')
            print(json.dumps(result, sort_keys=True))
            return
    build_seconds = time.monotonic() - start
    expected = 566048 if args.mode == 'x' else 1132096
    assert len(index) == expected and additions == 566048
    x_keyset = set(index) if args.mode == 'x' else {x for x, _ in index}
    assert len(x_keyset) == 566048
    keyset_digest = digest_keys(x_keyset)
    rng = random.Random(cfg['positive_seed'])
    positive_receipts = []
    positive_start = time.monotonic()
    for i in range(cfg['positive_query_count']):
        code0, code1 = rng.choice(base)[0], rng.choice(base)[0]
        sign0, sign1 = rng.randrange(2), rng.randrange(2)
        p0, p1 = base_by_code[code0], curve.frob(base_by_code[code1], 1)
        if sign0:
            p0 = curve.neg(p0)
        if sign1:
            p1 = curve.neg(p1)
        target = curve.add(p0, p1)
        witness = lookup(onb, curve, index, args.mode, target, base_by_code)
        assert witness == (code0, sign0, code1, sign1)
        if i < 8:
            positive_receipts.append({'target_coordinates': coords(onb, target),
                                      'input_witness': [code0, sign0, code1, sign1],
                                      'returned_witness': list(witness)})
    positive_seconds = time.monotonic() - positive_start
    public_fiber = [tuple(onb.fromCoords(int(v)) for v in rec['target_coordinates'])
                    for rec in geometry['official_single_target_cofactor_fiber']['four_verified_lifts']]
    query_rng = random.Random(cfg['ordinary_query_seed'])
    h = hashlib.sha256()
    ordinary_hits = []
    ordinary_start = time.monotonic()
    for i in range(cfg['ordinary_right_family_count']):
        right = None
        for position in (12, 13, 14):
            code = query_rng.choice(base)[0]
            point = code_point(onb, curve, basis, code, position)
            if query_rng.randrange(2):
                point = curve.neg(point)
            right = curve.add(right, point)
        for endpoint_index, endpoint in enumerate(public_fiber):
            residual = curve.add(endpoint, curve.neg(right))
            x, y = coords(onb, residual)
            h.update(x.to_bytes(17, 'big') + y.to_bytes(17, 'big'))
            witness = lookup(onb, curve, index, args.mode, residual, base_by_code)
            if witness is not None:
                ordinary_hits.append({'family': i, 'endpoint': endpoint_index,
                                      'witness': list(witness)})
    ordinary_seconds = time.monotonic() - ordinary_start
    result = {'status': 'COMPLETE_EXACT_PAIR_LOOKUP', 'mode': args.mode,
              'candidate_id': None, 'curve_id': cfg['curve_id'],
              'workload_id': cfg['workload_id'],
              'signed_pairs_covered': 1132096, 'group_additions': additions,
              'index_entries': len(index), 'x_keyset_sha256': keyset_digest,
              'index_build_seconds': build_seconds,
              'positive_query_count': cfg['positive_query_count'],
              'positive_query_seconds': positive_seconds,
              'positive_receipts': positive_receipts,
              'ordinary_right_family_count': cfg['ordinary_right_family_count'],
              'ordinary_target_query_count': cfg['ordinary_right_family_count'] * 4,
              'ordinary_query_key_stream_sha256': h.hexdigest(),
              'ordinary_hits': ordinary_hits,
              'ordinary_target_query_seconds': ordinary_seconds,
              'total_script_seconds': time.monotonic() - start,
              'peak_rss_bytes': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
              'protocol_sha256': sha(protocol_path)}
    with (HERE / (args.mode + '_result.json')).open('x') as out:
        json.dump(result, out, sort_keys=True, indent=2)
        out.write('\n')
    print(json.dumps({key: result[key] for key in
                      ('status', 'mode', 'index_entries', 'index_build_seconds',
                       'ordinary_target_query_count', 'ordinary_hits',
                       'total_script_seconds', 'peak_rss_bytes')}, sort_keys=True))


if __name__ == '__main__':
    main()
