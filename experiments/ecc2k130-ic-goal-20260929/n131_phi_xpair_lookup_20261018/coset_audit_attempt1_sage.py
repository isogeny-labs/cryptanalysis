"""Audit Q1358 endpoint cosets and subgroup relevance of pair queries."""
import hashlib
import json
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


def main():
    cfg_path = HERE / 'protocol.json'
    cfg = json.loads(cfg_path.read_text())
    geometry_path = Path(cfg['sources']['geometry']['path'])
    manifest_path = SOURCE / 'd10_m15_candidate_manifest_v1.json'
    geometry = json.loads(geometry_path.read_text())
    manifest = json.loads(manifest_path.read_text())
    # The candidate manifest stores the exact curve order as four times r.
    curve_record = manifest['candidate_record']['curve']
    r = int(curve_record['subgroup_order'])
    assert int(curve_record['curve_order']) == 4 * r
    onb = field.Onb(131)
    curve = curves.Curve(onb)
    basis = [int(v, 16) for v in geometry['domain']['basis_coordinate_masks_hex']]
    valid = 0
    for code in range(1, 1024):
        mask = 0
        for bit, b in enumerate(basis):
            if code >> bit & 1:
                mask ^= b
        phi = onb.fromCoords(mask)
        point = curve.pointFromX(onb.add(onb.inv(phi), onb.one()))
        if point is not None:
            assert curve.mul(point, r) is None
            valid += 1
    assert valid == 532
    records = geometry['official_single_target_cofactor_fiber']['four_verified_lifts']
    points = [tuple(onb.fromCoords(int(v)) for v in item['target_coordinates'])
              for item in records]
    q = points[0]
    subgroup = [curve.mul(point, r) is None for point in points]
    torsion_differences = []
    for point in points:
        diff = curve.add(point, curve.neg(q))
        torsion_differences.append(curve.mul(diff, 4) is None)
    assert subgroup == [True, False, False, False]
    assert torsion_differences == [True] * 4
    result = {'status': 'PASS_EXACT_ENDPOINT_COSET_AUDIT',
              'curve_id': cfg['curve_id'], 'subgroup_order': r,
              'valid_base_codes_checked': valid,
              'endpoint_in_subgroup': subgroup,
              'endpoint_difference_four_torsion': torsion_differences,
              'subgroup_relevant_endpoint_count': sum(subgroup),
              'subgroup_relevant_queries_per_arm': cfg['ordinary_right_family_count'],
              'coset_control_queries_per_arm': cfg['ordinary_right_family_count'] * 3,
              'protocol_sha256': sha(cfg_path),
              'geometry_sha256': sha(geometry_path),
              'manifest_sha256': sha(manifest_path),
              'script_sha256': sha(Path(__file__))}
    with (HERE / 'coset_audit.json').open('x') as out:
        json.dump(result, out, sort_keys=True, indent=2)
        out.write('\n')
    print(json.dumps({key: result[key] for key in
                      ('status', 'valid_base_codes_checked', 'endpoint_in_subgroup',
                       'subgroup_relevant_queries_per_arm',
                       'coset_control_queries_per_arm')}, sort_keys=True))


if __name__ == '__main__':
    main()
