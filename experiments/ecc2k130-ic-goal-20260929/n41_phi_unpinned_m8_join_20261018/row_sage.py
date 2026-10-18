"""Recover and replay the eight-column subgroup relation in folded form."""
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent / 'n41_phi_second_link_control_20261009'
sys.path.insert(0, str(HERE.parents[2] / 'ecc2k130/codegen'))
import curves
import field


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    cfg_path = HERE / 'row_protocol.json'
    cfg = json.loads(cfg_path.read_text())
    for name, item in cfg['sources'].items():
        assert sha(item['path']) == item['sha256'], name
    source = json.loads((BASE / 'protocol.json').read_text())
    table = json.loads((BASE / 'table.json').read_text())
    audit = json.loads((HERE / 'public_audit.json').read_text())
    assert audit['status'] == 'PASS_INDEPENDENT_N41_PHI_EIGHT_LEAF_REPLAY'
    onb = field.Onb(41)
    curve = curves.Curve(onb)
    r = source['subgroup_order']
    basis = table['basis_coordinate_masks']
    codes = table['valid_codes']

    def leaf(code, position, sign):
        mask = 0
        for i, value in enumerate(basis):
            if code >> i & 1:
                mask ^= value
        phi = onb.frob(onb.fromCoords(mask), position)
        p = curve.pointFromX(onb.add(onb.inv(phi), onb.one()))
        assert p is not None
        return curve.neg(p) if sign else p

    def coords(point):
        return tuple(onb.toCoords(v) for v in point)

    canonical = {}
    full = set()
    for code in codes:
        p = curve.mul(leaf(code, 0, 0), 4)
        assert p is not None and curve.mul(p, r) is None
        orbit = []
        for shift in range(41):
            q = curve.frob(p, shift)
            orbit.extend((q, curve.neg(q)))
        assert len(set(orbit)) == 82
        full.update(orbit)
        rep = min(orbit, key=coords)
        canonical[coords(rep)] = rep
    keys = sorted(canonical)
    assert len(keys) == 26 and len(full) == 26 * 82
    lam = curves.frobeniusEigenvalue(curve, canonical[keys[0]], r)
    orbit_map = {}
    for key in keys:
        rep = canonical[key]
        for shift in range(41):
            p = curve.frob(rep, shift)
            c = pow(lam, shift, r)
            for point, coefficient in ((p, c), (curve.neg(p), -c % r)):
                assert point not in orbit_map
                orbit_map[point] = (key, coefficient)
    assert len(orbit_map) == len(full)

    coefficients = {key: 0 for key in keys}
    terms = []
    raw_sum = None
    for position, (code, sign) in enumerate(zip(audit['leaf_codes'], audit['leaf_signs'])):
        raw = leaf(code, position, sign)
        raw_sum = curve.add(raw_sum, raw)
        projected = curve.mul(raw, 4)
        assert projected in orbit_map
        key, coefficient = orbit_map[projected]
        coefficients[key] = (coefficients[key] + coefficient) % r
        terms.append({'position': position, 'code': code, 'sign': sign,
                      'column': keys.index(key), 'coefficient_mod_r': coefficient,
                      'raw_point': coords(raw), 'subgroup_point': coords(projected)})
    target_raw = tuple(onb.fromCoords(v) for v in source['endpoint_coordinates'])
    target_subgroup = tuple(onb.fromCoords(v) for v in source['target_coordinates'])
    assert raw_sum == target_raw and curve.mul(raw_sum, 4) == target_subgroup
    assert len({term['column'] for term in terms}) == 8
    reconstructed = None
    for key, coefficient in coefficients.items():
        if coefficient:
            reconstructed = curve.add(reconstructed, curve.mul(canonical[key], coefficient))
    assert reconstructed == target_subgroup
    nonzero = [{'column': keys.index(key), 'representative': key,
                'coefficient_mod_r': coefficient}
               for key, coefficient in coefficients.items() if coefficient]
    assert len(nonzero) == 8
    result = {'status': 'PASS_UNPINNED_N41_PHI_EIGHT_COLUMN_RELATION',
              'candidate_id': None, 'curve_id': cfg['curve_id'],
              'subgroup_order': r, 'cofactor': 4,
              'factor_base_points_before_folding': len(full),
              'folded_columns': len(keys),
              'frobenius_eigenvalue_mod_r': lam,
              'raw_target': coords(target_raw),
              'subgroup_target': coords(target_subgroup),
              'terms': terms, 'nonzero_row': nonzero,
              'row_protocol_sha256': sha(cfg_path),
              'public_audit_sha256': sha(HERE / 'public_audit.json')}
    (HERE / 'row_result.json').write_text(json.dumps(result, sort_keys=True, indent=2)+'\n')
    print(json.dumps({'status': result['status'],
                      'factor_base_points_before_folding': len(full),
                      'folded_columns': len(keys), 'row_nonzero': len(nonzero)}, sort_keys=True))


if __name__ == '__main__':
    main()
