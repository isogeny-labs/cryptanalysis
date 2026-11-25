"""Freeze and audit the signed three-leaf partial-sum panel before SAT."""
import hashlib
import itertools
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PARENT = HERE.parent / 'n131_phi_three_leaf_prefix_20261018'
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


def masks_for_codes(onb, curve, basis, codes, signs):
    running = None
    partials = []
    for position, (code, sign) in enumerate(zip(codes, signs)):
        base_mask = 0
        for bit, mask in enumerate(basis):
            if code >> bit & 1:
                base_mask ^= mask
        phi = onb.frob(onb.fromCoords(base_mask), position)
        x = onb.add(onb.inv(phi), onb.one())
        point = curve.pointFromX(x)
        assert point is not None
        if sign:
            point = curve.neg(point)
        running = curve.add(running, point)
        if position >= 1:
            partials.append(template.point_phi(onb, running))
    return partials


def main():
    old = json.loads((PARENT / 'protocol.json').read_text())
    for name, item in old['sources'].items():
        assert sha(item['path']) == item['sha256'], name
    assert old['ordinary_prefixes'][0] == [637, 989, 110]
    receipt = json.loads(Path(old['sources']['formula_receipt']['path']).read_text())
    template_path = SOURCE / 'm16_static/phi_frobenius_sat_gate_m16_sparse_seed_v1.py'
    builder_path = SOURCE / 'm15_d10_static/build_d10_m15_formula.py'
    assert sha(template_path) == receipt['inputs_sha256']['formula_template']
    assert sha(builder_path) == receipt['source_sha256']
    geometry = json.loads(Path(old['sources']['geometry']['path']).read_text())
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
    codes = old['ordinary_prefixes'][0]
    assert all(code in valid for code in codes)
    target_phi = [int(item['phi_coordinate']) for item in
                  geometry['official_single_target_cofactor_fiber']['four_verified_lifts']]
    template.DIM = 10
    template.M = 15
    formula, primary, _roots, *_ = template.build_formula(onb, basis, valid, target_phi)
    assert primary['leaf0'] == list(range(2, 12))
    assert primary['leaf1'] == list(range(12, 22))
    assert primary['leaf2'] == list(range(22, 32))
    assert primary['partial0'] == list(range(152, 283))
    assert primary['partial1'] == list(range(283, 414))
    stats = formula.stats()
    assert stats['vars'] == receipt['formula_counts']['variables']
    assert stats['clauses'] == receipt['formula_counts']['clauses']
    assert stats['xors'] == receipt['formula_counts']['native_xors']
    temp = HERE / 'rebuilt_formula.xcnf'
    formula.writeDimacs(temp)
    assert sha(temp) == old['sources']['formula']['sha256']
    temp.unlink()
    branches = []
    for signs in itertools.product(range(2), repeat=3):
        masks = masks_for_codes(onb, curve, basis, codes, signs)
        assert len(masks) == 2
        branches.append({'signs': list(signs), 'partial_phi_masks': masks})
    planted = receipt['planted_control']
    assert masks_for_codes(onb, curve, basis, planted['leaf_codes'][:3],
                           planted['leaf_sign_bits'][:3]) == planted['partial_phi_masks'][:2]
    source_paths = {'old_protocol': PARENT / 'protocol.json',
                    'old_mapping_audit': PARENT / 'mapping_audit.json',
                    'formula': Path(old['sources']['formula']['path']),
                    'formula_receipt': Path(old['sources']['formula_receipt']['path']),
                    'geometry': Path(old['sources']['geometry']['path']),
                    'workload': Path(old['sources']['workload']['path']),
                    'field.py': ROOT / 'ecc2k130/codegen/field.py',
                    'curves.py': ROOT / 'ecc2k130/codegen/curves.py',
                    'template': template_path, 'builder': builder_path,
                    'solver': Path(old['sources']['solver']['path']),
                    'freeze_sage.py': HERE / 'freeze_sage.py',
                    'run.py': HERE / 'run.py', 'verify.py': HERE / 'verify.py',
                    'sage_runtime_info': HERE / 'sage_runtime_info.json'}
    sources = {name: {'path': str(path), 'sha256': sha(path)}
               for name, path in source_paths.items()}
    protocol = {'status': 'FROZEN_BEFORE_SOLVER', 'candidate_id': None,
                'curve_id': old['curve_id'], 'workload_id': old['workload_id'],
                'target_count': 1, 'public_point': old['public_point'],
                'codes': codes, 'branches': branches,
                'invalid_control': {'signs': [0, 0, 0],
                                    'partial_phi_masks': [branches[0]['partial_phi_masks'][0] ^ 1,
                                                          branches[0]['partial_phi_masks'][1]]},
                'leaf_variable_rule': 'leaf i bit j = 2 + 10*i + j',
                'partial_variable_rule': 'partial i bit j = 152 + 131*i + j',
                'solver_flags': old['solver_flags'],
                'per_arm_parent_wall_cap_seconds': 25,
                'campaign_parent_wall_cap_seconds': 300,
                'rss_cap_bytes': 4294967296, 'sources': sources,
                'planted_prefix_control': {
                    'codes': planted['leaf_codes'][:3],
                    'signs': planted['leaf_sign_bits'][:3],
                    'partial_phi_masks': planted['partial_phi_masks'][:2],
                    'original_model_status': planted['status']}}
    dump(HERE / 'protocol.json', protocol)
    print(json.dumps({'status': protocol['status'],
                      'distinct_partial_pairs': len({tuple(b['partial_phi_masks']) for b in branches}),
                      'branch_count': len(branches),
                      'protocol_sha256': sha(HERE / 'protocol.json')}, sort_keys=True))


if __name__ == '__main__':
    main()
