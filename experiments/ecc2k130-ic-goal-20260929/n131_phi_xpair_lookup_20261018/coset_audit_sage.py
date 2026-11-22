"""Audit raw lift torsion classes and their target-query eligibility."""
import hashlib
import json
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
GOAL = HERE.parent
SOURCE = GOAL / 'n131_phi_torsion_frobenius_domains_20261005/m15_d10_static'
sys.path.insert(0, str(ROOT / 'ecc2k130/codegen'))
import curves
import field


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def coords(onb, point):
    return None if point is None else (onb.toCoords(point[0]), onb.toCoords(point[1]))


def main():
    cfg_path = HERE / 'protocol.json'
    cfg = json.loads(cfg_path.read_text())
    geometry_path = Path(cfg['sources']['geometry']['path'])
    manifest_path = SOURCE / 'd10_m15_candidate_manifest_v1.json'
    geometry = json.loads(geometry_path.read_text())
    manifest = json.loads(manifest_path.read_text())
    curve_record = manifest['candidate_record']['curve']
    r = int(curve_record['subgroup_order'])
    assert int(curve_record['curve_order']) == 4 * r
    onb = field.Onb(131)
    curve = curves.Curve(onb)
    basis = [int(v, 16) for v in geometry['domain']['basis_coordinate_masks_hex']]
    base = []
    for code in range(1, 1024):
        mask = 0
        for bit, b in enumerate(basis):
            if code >> bit & 1:
                mask ^= b
        phi = onb.fromCoords(mask)
        point = curve.pointFromX(onb.add(onb.inv(phi), onb.one()))
        if point is not None:
            tor = curve.mul(point, r)
            assert curve.mul(tor, 4) is None
            base.append((code, point, tor))
    assert len(base) == 532
    by_code = {code: (point, tor) for code, point, tor in base}
    raw_classes = {}
    slot1_classes = {}
    for _, _, tor in base:
        raw_classes[coords(onb, tor)] = tor
        tor1 = None if tor is None else curve.frob(tor, 1)
        slot1_classes[coords(onb, tor1)] = tor1
    signed0 = {}
    signed1 = {}
    for tor in raw_classes.values():
        signed0[coords(onb, tor)] = tor
        neg = curve.neg(tor)
        signed0[coords(onb, neg)] = neg
    for tor in slot1_classes.values():
        signed1[coords(onb, tor)] = tor
        neg = curve.neg(tor)
        signed1[coords(onb, neg)] = neg
    pair_classes = {coords(onb, curve.add(a, b))
                    for a in signed0.values() for b in signed1.values()}
    records = geometry['official_single_target_cofactor_fiber']['four_verified_lifts']
    endpoints = [tuple(onb.fromCoords(int(v)) for v in item['target_coordinates'])
                 for item in records]
    endpoint_tor = [curve.mul(point, r) for point in endpoints]
    endpoint_classes = [coords(onb, tor) for tor in endpoint_tor]
    differences_four_torsion = []
    for point in endpoints:
        diff = curve.add(point, curve.neg(endpoints[0]))
        differences_four_torsion.append(curve.mul(diff, 4) is None)
    assert differences_four_torsion == [True] * 4
    rng = random.Random(cfg['ordinary_query_seed'])
    stream = hashlib.sha256()
    eligible = [0] * 4
    for _ in range(cfg['ordinary_right_family_count']):
        right = None
        right_tor = None
        for position in (12, 13, 14):
            code = rng.choice(base)[0]
            point, tor = by_code[code]
            point = curve.frob(point, position)
            tor = None if tor is None else curve.frob(tor, position)
            if rng.randrange(2):
                point, tor = curve.neg(point), curve.neg(tor)
            right = curve.add(right, point)
            right_tor = curve.add(right_tor, tor)
        for index, endpoint in enumerate(endpoints):
            residual = curve.add(endpoint, curve.neg(right))
            x, y = coords(onb, residual)
            stream.update(x.to_bytes(17, 'big') + y.to_bytes(17, 'big'))
            residual_tor = curve.add(endpoint_tor[index], curve.neg(right_tor))
            eligible[index] += int(coords(onb, residual_tor) in pair_classes)
    full = json.loads((HERE / 'full_result.json').read_text())
    xrun = json.loads((HERE / 'x_result.json').read_text())
    assert stream.hexdigest() == full['ordinary_query_key_stream_sha256'] == xrun['ordinary_query_key_stream_sha256']
    result = {'status': 'PASS_EXACT_RAW_LIFT_COSET_AUDIT',
              'curve_id': cfg['curve_id'], 'subgroup_order': r,
              'valid_base_codes_checked': len(base),
              'raw_lift_torsion_classes': len(raw_classes),
              'signed_pair_torsion_classes': len(pair_classes),
              'endpoint_torsion_class_keys': endpoint_classes,
              'endpoint_difference_four_torsion': differences_four_torsion,
              'ordinary_queries_per_endpoint': cfg['ordinary_right_family_count'],
              'torsion_eligible_queries_per_endpoint': eligible,
              'query_key_stream_sha256': stream.hexdigest(),
              'protocol_sha256': sha(cfg_path),
              'geometry_sha256': sha(geometry_path),
              'manifest_sha256': sha(manifest_path),
              'script_sha256': sha(Path(__file__))}
    with (HERE / 'coset_audit.json').open('x') as out:
        json.dump(result, out, sort_keys=True, indent=2)
        out.write('\n')
    print(json.dumps({key: result[key] for key in
                      ('status', 'valid_base_codes_checked',
                       'raw_lift_torsion_classes', 'signed_pair_torsion_classes',
                       'torsion_eligible_queries_per_endpoint')}, sort_keys=True))


if __name__ == '__main__':
    main()
