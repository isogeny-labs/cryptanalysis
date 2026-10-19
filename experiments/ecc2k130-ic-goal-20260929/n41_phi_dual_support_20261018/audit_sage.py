"""Independent exact forward-support and dual-XCNF audit."""
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
GOAL = HERE.parent
PREV = GOAL / 'n41_phi_suffix2_corrected_20261018'
BASE = GOAL / 'n41_phi_second_link_control_20261009'
ROOT = GOAL.parents[1]
sys.path.insert(0, str(ROOT / 'ecc2k130/codegen'))
import curves
import field

N, DIM, M = 41, 6, 12
PARTIAL0 = 2 + M * DIM


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


def phi_mask(onb, point):
    if point is None or point[0] == onb.one():
        return None
    return onb.toCoords(onb.inv(onb.add(point[0], onb.one())))


def main():
    cfg = json.loads((HERE / 'protocol.json').read_text())
    for name, item in cfg['sources'].items():
        assert sha(item['path']) == item['sha256'], name
    prior = json.loads((PREV / 'audit.json').read_text())
    assert prior['status'] == 'PASS_GROUP_AND_PARTIAL8_FORMULA_AUDIT'
    table = json.loads((BASE / 'table.json').read_text())
    onb = field.Onb(N)
    curve = curves.Curve(onb)
    basis, codes = table['basis_coordinate_masks'], table['valid_codes']
    options = []
    for pos in (0, 1):
        options.append([signed for code in codes
                        for point in [point_for(onb, curve, basis, code, pos)]
                        for signed in (point, curve.neg(point))])
    masks = set()
    exceptional = 0
    for left in options[0]:
        for right in options[1]:
            mask = phi_mask(onb, curve.add(left, right))
            if mask is None:
                exceptional += 1
            else:
                masks.add(mask)
    support = json.loads((HERE / 'forward_masks.json').read_text())
    assert sorted(masks) == support['masks']
    assert exceptional == support['exceptional_nonfinite_pairs']
    assert support['enumerated_signed_pairs'] == 3600
    source = Path(cfg['sources']['previous_guided_formula']['path'])
    dual = Path(cfg['sources']['dual_formula']['path'])
    with source.open('rt', encoding='ascii') as src, dual.open('rt', encoding='ascii') as dst:
        assert src.readline().split() == cfg['source_header']
        assert dst.readline().split() == cfg['dual_header']
        for line in src:
            assert dst.readline() == line
        old_vars = int(cfg['source_header'][2])
        for index, mask in enumerate(support['masks']):
            selector = old_vars + index + 1
            for bit in range(N):
                var = PARTIAL0 + bit
                lit = var if mask >> bit & 1 else -var
                assert dst.readline() == '%d %d 0\n' % (-selector, lit)
        expected = ' '.join(str(old_vars + i + 1) for i in range(len(masks))) + ' 0\n'
        assert dst.readline() == expected and dst.readline() == ''
    result = {'status': 'PASS_DUAL_END_GROUP_AND_XCNF_AUDIT',
              'forward_signed_pair_cases': 3600, 'forward_distinct_finite_masks': len(masks),
              'forward_exceptional_cases': exceptional,
              'backward_distinct_finite_masks': prior['distinct_finite_masks'],
              'forward_partial_variables': list(range(PARTIAL0, PARTIAL0 + N)),
              'backward_partial_variables': prior['partial_variables'],
              'protocol_sha256': sha(HERE / 'protocol.json'),
              'dual_formula_sha256': sha(dual)}
    with (HERE / 'audit.json').open('x') as out:
        json.dump(result, out, sort_keys=True, indent=2)
        out.write('\n')
    print(json.dumps({'status': result['status'], 'forward_masks': len(masks),
                      'exceptional': exceptional}, sort_keys=True))


if __name__ == '__main__':
    main()
