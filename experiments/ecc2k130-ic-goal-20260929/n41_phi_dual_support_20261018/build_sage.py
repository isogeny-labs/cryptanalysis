"""Freeze exact forward-pair and public-target backward support on N41."""
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


def dump(path, obj):
    with path.open('x') as out:
        json.dump(obj, out, sort_keys=True, indent=2)
        out.write('\n')


def leaf(onb, curve, basis, code, position):
    mask = 0
    for bit, b in enumerate(basis):
        if code >> bit & 1:
            mask ^= b
    phi = onb.frob(onb.fromCoords(mask), position)
    point = curve.pointFromX(onb.add(onb.inv(phi), onb.one()))
    assert point is not None
    return point


def phi_mask(onb, point):
    if point is None or point[0] == onb.one():
        return None
    return onb.toCoords(onb.inv(onb.add(point[0], onb.one())))


def main():
    prev = json.loads((PREV / 'protocol.json').read_text())
    for name, item in prev['sources'].items():
        assert sha(item['path']) == item['sha256'], name
    assert json.loads((PREV / 'audit.json').read_text())['status'] == 'PASS_GROUP_AND_PARTIAL8_FORMULA_AUDIT'
    table = json.loads((BASE / 'table.json').read_text())
    basis, codes = table['basis_coordinate_masks'], table['valid_codes']
    onb = field.Onb(N)
    curve = curves.Curve(onb)
    options = []
    for pos in (0, 1):
        options.append([signed for code in codes
                        for point in [leaf(onb, curve, basis, code, pos)]
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
    masks = sorted(masks)
    support = {'status': 'FROZEN_FORWARD_PAIR_SUPPORT',
               'positions': [0, 1], 'signed_options_per_position': 60,
               'enumerated_signed_pairs': 3600,
               'exceptional_nonfinite_pairs': exceptional,
               'distinct_finite_masks': len(masks), 'masks': masks}
    dump(HERE / 'forward_masks.json', support)
    source = PREV / 'guided_partial8.xcnf'
    destination = HERE / 'dual_guided.xcnf'
    with source.open('rt', encoding='ascii') as src, destination.open('x', encoding='ascii') as out:
        header = src.readline().split()
        assert header == prev['guided_header']
        old_vars, old_records = int(header[2]), int(header[3])
        out.write('p cnf %d %d\n' % (old_vars + len(masks),
                                      old_records + len(masks) * N + 1))
        for line in src:
            out.write(line)
        for index, mask in enumerate(masks):
            selector = old_vars + index + 1
            for bit in range(N):
                variable = PARTIAL0 + bit
                literal = variable if mask >> bit & 1 else -variable
                out.write('%d %d 0\n' % (-selector, literal))
        out.write(' '.join(str(old_vars + index + 1) for index in range(len(masks))) + ' 0\n')
    source_paths = {'previous_protocol': PREV / 'protocol.json',
                    'previous_audit': PREV / 'audit.json',
                    'previous_guided_formula': source,
                    'base_source_formula': BASE / 'source.xcnf',
                    'base_table': BASE / 'table.json',
                    'solver': Path(prev['sources']['solver']['path']),
                    'forward_masks': HERE / 'forward_masks.json',
                    'dual_formula': destination,
                    'build_sage.py': HERE / 'build_sage.py',
                    'audit_sage.py': HERE / 'audit_sage.py',
                    'run.py': HERE / 'run.py',
                    'verify.py': HERE / 'verify.py',
                    'sage_runtime_info': HERE / 'sage_runtime_info.json'}
    sources = {name: {'path': str(path), 'sha256': sha(path)}
               for name, path in source_paths.items()}
    protocol = {'status': 'FROZEN_BEFORE_SOLVER', 'candidate_id': None,
                'curve_id': prev['curve_id'], 'workload_id': prev['workload_id'],
                'target_count': 1, 'target_coordinates': prev['target_coordinates'],
                'endpoint_coordinates': prev['endpoint_coordinates'],
                'source_header': header,
                'dual_header': ['p', 'cnf', str(old_vars + len(masks)),
                                str(old_records + len(masks) * N + 1)],
                'forward_partial_index': 0,
                'forward_partial_variables': list(range(PARTIAL0, PARTIAL0 + N)),
                'backward_partial_index': 8,
                'forward_support_count': len(masks),
                'backward_support_count': prev['finite_mask_count'],
                'solver_flags': prev['solver_flags'],
                'parent_wall_cap_seconds': 240, 'rss_cap_bytes': 4294967296,
                'sources': sources}
    dump(HERE / 'protocol.json', protocol)
    print(json.dumps({'status': protocol['status'],
                      'forward_masks': len(masks), 'exceptional': exceptional,
                      'dual_formula_sha256': sha(destination),
                      'protocol_sha256': sha(HERE / 'protocol.json')}, sort_keys=True))


if __name__ == '__main__':
    main()
