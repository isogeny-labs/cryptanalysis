"""Check the public formula interface variables against its source builder."""
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SOURCE = ROOT / 'experiments/ecc2k130-ic-goal-20260929/n131_phi_torsion_frobenius_domains_20261005'
sys.path[:0] = [str(ROOT / 'ecc2k130/codegen'), str(SOURCE / 'm16_static')]
import curves
import field
import phi_frobenius_sat_gate_m16_sparse_seed_v1 as template


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    geometry_path = SOURCE / 'm15_d10_static/d10_exact_geometry_v1.json'
    formula_path = SOURCE / 'm15_d10_static/official_q_phi_fiber_d10_m15_v1.xcnf'
    receipt_path = SOURCE / 'm15_d10_static/d10_m15_formula_and_planted_control_v1.json'
    geometry = json.loads(geometry_path.read_text())
    receipt = json.loads(receipt_path.read_text())
    assert sha(formula_path) == receipt['formula_file']['sha256']
    onb = field.Onb(131)
    curve = curves.Curve(onb)
    basis = [int(v, 16) for v in geometry['domain']['basis_coordinate_masks_hex']]
    valid = []
    for code in range(1024):
        mask = 0
        for bit, b in enumerate(basis):
            if code >> bit & 1:
                mask ^= b
        if mask:
            phi = onb.fromCoords(mask)
            if curve.pointFromX(onb.add(onb.inv(phi), onb.one())) is not None:
                valid.append(code)
    assert len(valid) == 532
    target_phi = [int(item['phi_coordinate']) for item in
                  geometry['official_single_target_cofactor_fiber']['four_verified_lifts']]
    template.DIM = 10
    template.M = 15
    formula, primary, _roots, *_ = template.build_formula(onb, basis, valid, target_phi)
    assert formula.stats()['xors'] == receipt['formula_counts']['native_xors']
    leaves = [variable for i in range(3) for variable in primary['leaf%d' % i]]
    endpoint = primary['endpoint']
    assert leaves == list(range(2, 32))
    assert endpoint == [1855, 1856]
    result = {'status': 'PASS_PUBLIC_Q_XOR_INTERFACE_MAP',
              'curve_id': geometry['curve_id'],
              'formula_sha256': sha(formula_path),
              'first_three_leaf_variables': leaves,
              'endpoint_selector_variables': endpoint,
              'constant_true_variable': 1,
              'native_xor_rows': formula.stats()['xors'],
              'geometry_sha256': sha(geometry_path),
              'builder_sha256': sha(SOURCE / 'm16_static/phi_frobenius_sat_gate_m16_sparse_seed_v1.py')}
    with (HERE / 'mapping.json').open('x') as output:
        json.dump(result, output, sort_keys=True, indent=2)
        output.write('\n')
    print(json.dumps({k: result[k] for k in ('status', 'endpoint_selector_variables',
                                             'native_xor_rows')}, sort_keys=True))


if __name__ == '__main__':
    main()
