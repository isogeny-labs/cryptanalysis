"""Rebuild the exact Q1358 formula and verify the frozen leaf-variable map."""
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
    cfg = json.loads((HERE / 'protocol.json').read_text())
    receipt = json.loads(Path(cfg['sources']['formula_receipt']['path']).read_text())
    template_path = SOURCE / 'm16_static/phi_frobenius_sat_gate_m16_sparse_seed_v1.py'
    builder_path = SOURCE / 'm15_d10_static/build_d10_m15_formula.py'
    assert sha(template_path) == receipt['inputs_sha256']['formula_template']
    assert sha(builder_path) == receipt['source_sha256']
    geometry = json.loads(Path(cfg['sources']['geometry']['path']).read_text())
    basis = [int(value, 16) for value in geometry['domain']['basis_coordinate_masks_hex']]
    onb = field.Onb(131)
    curve = curves.Curve(onb)
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
    stats = formula.stats()
    assert stats['vars'] == receipt['formula_counts']['variables']
    assert stats['clauses'] == receipt['formula_counts']['clauses']
    assert stats['xors'] == receipt['formula_counts']['native_xors']
    leaf_map = {str(position): primary['leaf%d' % position]
                for position in range(3)}
    for position in range(3):
        assert leaf_map[str(position)] == list(range(2 + 10 * position, 12 + 10 * position))
    output = HERE / 'rebuilt_formula.xcnf'
    formula.writeDimacs(output)
    assert sha(output) == cfg['sources']['formula']['sha256']
    output.unlink()
    result = {'status': 'PASS_EXACT_FORMULA_AND_LEAF_VARIABLE_MAP',
              'leaf_map': leaf_map, 'formula_sha256': cfg['sources']['formula']['sha256'],
              'template_sha256': sha(template_path), 'builder_sha256': sha(builder_path),
              'protocol_sha256': sha(HERE / 'protocol.json')}
    with (HERE / 'mapping_audit.json').open('x') as handle:
        json.dump(result, handle, sort_keys=True, indent=2)
        handle.write('\n')
    print(json.dumps({'status': result['status'], 'leaf_map': leaf_map}, sort_keys=True))


if __name__ == '__main__':
    main()
