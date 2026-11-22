"""Independently replay any unpinned N41 SAT model against curve arithmetic."""
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
GOAL = HERE.parent
ROOT = GOAL.parents[1]
BASE = GOAL / 'n41_phi_second_link_control_20261009'
VERIFIER = GOAL / 'n131_phi_torsion_frobenius_domains_20261005/m16_prefix_audit_20261006'
sys.path[:0] = [str(ROOT / 'ecc2k130/codegen'), str(VERIFIER)]
import curves
import field
import verify_xcnf_model as xcnf

spec = importlib.util.spec_from_file_location('n41_base_audit', BASE / 'audit.py')
base_audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base_audit)

N, DIM, M = 41, 6, 12


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def phi_mask(onb, point):
    assert point is not None and point[0] != onb.one()
    return onb.toCoords(onb.inv(onb.add(point[0], onb.one())))


def leaf(onb, curve, basis, code, position):
    mask = 0
    for bit, b in enumerate(basis):
        if code >> bit & 1:
            mask ^= b
    phi = onb.frob(onb.fromCoords(mask), position)
    point = curve.pointFromX(onb.add(onb.inv(phi), onb.one()))
    assert point is not None
    return point


def main():
    cfg = json.loads((HERE / 'protocol.json').read_text())
    table = json.loads((BASE / 'table.json').read_text())
    source = Path(cfg['sources']['source_formula']['path'])
    onb = field.Onb(N)
    curve = curves.Curve(onb)
    endpoint = tuple(onb.fromCoords(value) for value in cfg['endpoint_coordinates'])
    target = tuple(onb.fromCoords(value) for value in cfg['target_coordinates'])
    results = {}
    for name in cfg['arms']:
        arm_dir = HERE / 'arms' / name
        if not arm_dir.exists():
            results[name] = {'status': 'NOT_RUN'}
            continue
        receipt = json.loads((arm_dir / 'receipt.json').read_text())
        if receipt['status'] != 'SAT_REPORTED_NEEDS_INDEPENDENT_REPLAY':
            results[name] = {'status': receipt['status']}
            continue
        formula = Path(receipt['command'][-1])
        stdout = arm_dir / 'stdout.txt'
        checked = xcnf.verify(formula, stdout)
        values = xcnf.model_from_stdout(stdout, checked['variables'])
        source_checked = None
        if name != 'source_unpinned':
            source_checked = base_audit.verify_source_assignment(source, values)
        codes = [sum(1 << bit for bit in range(DIM)
                     if values[2 + position * DIM + bit]) for position in range(M)]
        assert all(code in table['valid_codes'] for code in codes)
        wanted = [sum(1 << bit for bit in range(N)
                      if values[2 + M * DIM + index * N + bit])
                  for index in range(M - 2)]
        points = [leaf(onb, curve, table['basis_coordinate_masks'], code, pos)
                  for pos, code in enumerate(codes)]
        states = [(points[0], [0]), (curve.neg(points[0]), [1])]
        for position in range(1, M):
            matching = []
            for running, signs in states:
                for sign, point in ((0, points[position]), (1, curve.neg(points[position]))):
                    candidate = curve.add(running, point)
                    if candidate is None or candidate[0] == onb.one():
                        continue
                    if position < M - 1:
                        if phi_mask(onb, candidate) == wanted[position - 1]:
                            matching.append((candidate, signs + [sign]))
                    elif candidate in (endpoint, curve.neg(endpoint)):
                        matching.append((candidate, signs + [sign]))
            assert matching, ('curve chain has no signed realization', position)
            states = matching
        total, signs = states[0]
        projected = curve.mul(total, 4)
        assert projected in (target, curve.neg(target))
        result = {'status': 'PASS_VERIFIED_PUBLIC_RELATION',
                  'codes': codes, 'signs': signs, 'partial_phi_masks': wanted,
                  'distinct_folded_code_count': len(set(codes)),
                  'projected_target_sign': 0 if projected == target else 1,
                  'formula_check': checked, 'source_formula_check': source_checked,
                  'formula_sha256': sha(formula), 'stdout_sha256': sha(stdout)}
        results[name] = result
    output = {'protocol_sha256': sha(HERE / 'protocol.json'), 'arms': results}
    with (HERE / 'replay.json').open('x') as out:
        json.dump(output, out, sort_keys=True, indent=2)
        out.write('\n')
    print(json.dumps({name: result['status'] for name, result in results.items()},
                     sort_keys=True))


if __name__ == '__main__':
    main()
