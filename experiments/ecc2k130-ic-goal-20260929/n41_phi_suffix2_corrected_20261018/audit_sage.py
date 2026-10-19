"""Independent group and XCNF mapping audit for corrected partial8 support."""
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
GOAL = HERE.parent
BASE = GOAL / 'n41_phi_second_link_control_20261009'
OLD = GOAL / 'n41_phi_suffix2_guided_20261009'
ROOT = GOAL.parents[1]
TEMPLATE = GOAL / 'n131_phi_torsion_frobenius_domains_20261005/m16_static'
sys.path[:0] = [str(ROOT / 'ecc2k130/codegen'), str(TEMPLATE)]
import curves
import field
import phi_frobenius_sat_gate_m16_sparse_seed_v1 as template

N, DIM, M = 41, 6, 12
PARTIAL8 = 2 + M * DIM + 8 * N


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def point_for(onb, curve, basis, code, position):
    mask = 0
    for bit, b in enumerate(basis):
        if code >> bit & 1:
            mask ^= b
    phi = onb.frob(onb.fromCoords(mask), position)
    point = curve.pointFromX(onb.add(onb.inv(phi), onb.one()))
    assert point is not None
    return point


def phi_mask(onb, point):
    assert point is not None and point[0] != onb.one()
    return onb.toCoords(onb.inv(onb.add(point[0], onb.one())))


def main():
    cfg = json.loads((HERE / 'protocol.json').read_text())
    for name, item in cfg['sources'].items():
        assert sha(item['path']) == item['sha256'], name
    previous = json.loads((BASE / 'protocol.json').read_text())
    table = json.loads((BASE / 'table.json').read_text())
    suffix = json.loads((OLD / 'suffix_masks.json').read_text())
    onb = field.Onb(N)
    curve = curves.Curve(onb)
    basis, codes = table['basis_coordinate_masks'], table['valid_codes']
    endpoint = tuple(onb.fromCoords(v) for v in cfg['endpoint_coordinates'])
    target = tuple(onb.fromCoords(v) for v in cfg['target_coordinates'])
    assert curve.mul(endpoint, 4) == target
    assert len(codes) == 30
    template.N = N
    template.DIM = DIM
    template.M = M
    formula, primary, *_ = template.build_formula(onb, basis, codes,
                                                  [phi_mask(onb, endpoint)] * 4)
    assert primary['partial8'] == list(range(PARTIAL8, PARTIAL8 + N))
    temp = HERE / 'rebuilt_source.xcnf'
    formula.writeDimacs(temp)
    assert sha(temp) == cfg['sources']['source_formula']['sha256']
    temp.unlink()
    options = []
    for pos in (10, 11):
        options.append([signed for code in codes
                        for point in [point_for(onb, curve, basis, code, pos)]
                        for signed in (point, curve.neg(point))])
    masks = set()
    negative_masks = set()
    for p10 in options[0]:
        for p11 in options[1]:
            pair = curve.add(p10, p11)
            p8 = curve.add(endpoint, curve.neg(pair))
            assert curve.add(p8, pair) == endpoint
            masks.add(phi_mask(onb, p8))
            opposite = curve.add(curve.neg(endpoint), curve.neg(pair))
            negative_masks.add(phi_mask(onb, opposite))
    assert masks == negative_masks == set(suffix['masks'])
    assert len(masks) == 3577
    src_path = BASE / 'source.xcnf'
    dst_path = HERE / 'guided_partial8.xcnf'
    with src_path.open('rt', encoding='ascii') as src, dst_path.open('rt', encoding='ascii') as dst:
        old = src.readline().split()
        new = dst.readline().split()
        assert old == cfg['source_header'] and new == cfg['guided_header']
        for line in src:
            assert dst.readline() == line
        for index, mask in enumerate(suffix['masks']):
            selector = int(old[2]) + index + 1
            for bit in range(N):
                variable = primary['partial8'][bit]
                literal = variable if mask >> bit & 1 else -variable
                assert dst.readline() == '%d %d 0\n' % (-selector, literal)
        expected = ' '.join(str(int(old[2]) + index + 1) for index in range(len(masks))) + ' 0\n'
        assert dst.readline() == expected and dst.readline() == ''
    result = {'status': 'PASS_GROUP_AND_PARTIAL8_FORMULA_AUDIT',
              'source_formula_sha256': sha(src_path), 'guided_formula_sha256': sha(dst_path),
              'protocol_sha256': sha(HERE / 'protocol.json'),
              'signed_pair_cases': len(options[0]) * len(options[1]),
              'distinct_finite_masks': len(masks), 'partial_index': 8,
              'partial_variables': primary['partial8'],
              'public_point_transport': '4*endpoint=target',
              'opposite_endpoint_mask_set_equal': True}
    with (HERE / 'audit.json').open('x') as out:
        json.dump(result, out, sort_keys=True, indent=2)
        out.write('\n')
    print(json.dumps({'status': result['status'], 'masks': len(masks),
                      'partial_variables': [primary['partial8'][0],
                                            primary['partial8'][-1]]}, sort_keys=True))


if __name__ == '__main__':
    main()
