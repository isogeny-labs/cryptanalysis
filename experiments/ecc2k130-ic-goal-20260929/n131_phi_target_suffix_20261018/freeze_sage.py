"""Freeze exact public-target backward pins and joint end cuts before SAT."""
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PREVIOUS = HERE.parent / 'n131_phi_signed_prefix_20261018'
SOURCE = HERE.parent / 'n131_phi_torsion_frobenius_domains_20261005'
sys.path[:0] = [str(ROOT / 'ecc2k130/codegen'), str(SOURCE / 'm16_static')]
import curves
import field
import phi_frobenius_sat_gate_m16_sparse_seed_v1 as template


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path, obj):
    with path.open('x') as out:
        json.dump(obj, out, sort_keys=True, indent=2)
        out.write('\n')


def leaf_point(onb, curve, basis, position, code):
    mask = 0
    for bit, b in enumerate(basis):
        if code >> bit & 1:
            mask ^= b
    phi = onb.frob(onb.fromCoords(mask), position)
    point = curve.pointFromX(onb.add(onb.inv(phi), onb.one()))
    assert point is not None
    return point


def backward_masks(onb, curve, basis, codes, endpoint):
    running = endpoint
    masks = {}
    for position in (14, 13, 12):
        point = leaf_point(onb, curve, basis, position, codes[position - 12])
        running = curve.add(running, curve.neg(point))
        masks[position - 2] = template.point_phi(onb, running)
    return [masks[i] for i in (10, 11, 12)]


def main():
    prev = json.loads((PREVIOUS / 'protocol.json').read_text())
    for name, item in prev['sources'].items():
        assert sha(item['path']) == item['sha256'], name
    receipt = json.loads(Path(prev['sources']['formula_receipt']['path']).read_text())
    geometry = json.loads(Path(prev['sources']['geometry']['path']).read_text())
    basis = [int(value, 16) for value in geometry['domain']['basis_coordinate_masks_hex']]
    onb = field.Onb(131)
    curve = curves.Curve(onb)
    valid = []
    for code in range(1024):
        mask = 0
        for bit, b in enumerate(basis):
            if code >> bit & 1:
                mask ^= b
        if mask and curve.pointFromX(onb.add(onb.inv(onb.fromCoords(mask)), onb.one())) is not None:
            valid.append(code)
    assert len(valid) == 532
    prefix = prev['codes']
    suffix = prev['codes']
    assert all(c in valid for c in suffix)
    target_records = geometry['official_single_target_cofactor_fiber']['four_verified_lifts']
    endpoints = [tuple(onb.fromCoords(int(v)) for v in item['target_coordinates'])
                 for item in target_records]
    assert [template.point_phi(onb, point) for point in endpoints] == [
        int(item['phi_coordinate']) for item in target_records]
    target_phi = [int(item['phi_coordinate']) for item in target_records]
    template.DIM = 10
    template.M = 15
    formula, primary, _roots, *_ = template.build_formula(onb, basis, valid, target_phi)
    for index in (10, 11, 12):
        assert primary['partial%d' % index] == list(range(152 + 131 * index,
                                                         283 + 131 * index))
    for index in (12, 13, 14):
        assert primary['leaf%d' % index] == list(range(2 + 10 * index,
                                                      12 + 10 * index))
    assert primary['endpoint'] == [1855, 1856]
    temp = HERE / 'rebuilt_formula.xcnf'
    formula.writeDimacs(temp)
    assert sha(temp) == prev['sources']['formula']['sha256']
    temp.unlink()
    branches = []
    for selector, point in enumerate(endpoints):
        for orientation in (0, 1):
            oriented = point if orientation == 0 else curve.neg(point)
            masks = backward_masks(onb, curve, basis, suffix, oriented)
            branches.append({'endpoint_selector': selector, 'endpoint_orientation': orientation,
                             'suffix_signs': [0, 0, 0], 'partial_phi_masks': masks})
    assert len({tuple(b['partial_phi_masks']) for b in branches}) == 8
    source_paths = {'previous_protocol': PREVIOUS / 'protocol.json',
                    'previous_result': PREVIOUS / 'RESULT.md',
                    'formula': Path(prev['sources']['formula']['path']),
                    'formula_receipt': Path(prev['sources']['formula_receipt']['path']),
                    'geometry': Path(prev['sources']['geometry']['path']),
                    'workload': Path(prev['sources']['workload']['path']),
                    'field.py': ROOT / 'ecc2k130/codegen/field.py',
                    'curves.py': ROOT / 'ecc2k130/codegen/curves.py',
                    'template': SOURCE / 'm16_static/phi_frobenius_sat_gate_m16_sparse_seed_v1.py',
                    'builder': SOURCE / 'm15_d10_static/build_d10_m15_formula.py',
                    'solver': Path(prev['sources']['solver']['path']),
                    'freeze_sage.py': HERE / 'freeze_sage.py',
                    'run.py': HERE / 'run.py', 'verify.py': HERE / 'verify.py',
                    'sage_runtime_info': HERE / 'sage_runtime_info.json'}
    sources = {name: {'path': str(path), 'sha256': sha(path)}
               for name, path in source_paths.items()}
    protocol = {'status': 'FROZEN_BEFORE_SOLVER', 'candidate_id': None,
                'curve_id': prev['curve_id'], 'workload_id': prev['workload_id'],
                'target_count': 1, 'public_point': prev['public_point'],
                'prefix_codes': prefix, 'prefix_signs': [0, 0, 0],
                'prefix_partial_phi_masks': prev['branches'][0]['partial_phi_masks'],
                'suffix_codes': suffix, 'branches': branches,
                'invalid_control': dict(branches[0], partial_phi_masks=[
                    branches[0]['partial_phi_masks'][0], branches[0]['partial_phi_masks'][1],
                    branches[0]['partial_phi_masks'][2] ^ 1]),
                'solver_flags': prev['solver_flags'],
                'per_arm_parent_wall_cap_seconds': 25,
                'campaign_parent_wall_cap_seconds': 300,
                'rss_cap_bytes': 4294967296,
                'sources': sources}
    dump(HERE / 'protocol.json', protocol)
    print(json.dumps({'status': protocol['status'], 'branch_count': len(branches),
                      'protocol_sha256': sha(HERE / 'protocol.json')}, sort_keys=True))


if __name__ == '__main__':
    main()
