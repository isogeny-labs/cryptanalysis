"""Build an N41 W11 four-pair circuit with functional intermediate S3 roots."""
import hashlib
import json
import resource
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PRIOR = ROOT / 'n41_w11_fourpair_orbit_sat_20261019'
sys.path.insert(0, str(PRIOR))
sys.path.insert(0, str(ROOT / 'output_first_fifth_20261019'))
import circuit_orbit as design
from build_control_orbit import complete_assignment, check_assignment
from output_first_math import FixedSeed

F = design.F
N = design.N


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def mul(*values):
    out = 1
    for value in values:
        out = F.mul(out, value)
    return out


def extra_constraints(circ, wires):
    alg = design.Algebra(circ, F, dense_and_threshold=3000)
    extras = []
    for left, right, middle in [(0, 1, 0), (2, 3, 1)]:
        a = alg.from_bits(circ.linear_element(wires['out'][left],
            [F.frob(1 << bit, design.ROTATIONS[left]) for bit in range(N)]))
        b = alg.from_bits(circ.linear_element(wires['out'][right],
            [F.frob(1 << bit, design.ROTATIONS[right]) for bit in range(N)]))
        ab = alg.mul(a, b)
        A = alg.add(alg.square(ab), alg.one)
        B = ab
        D = alg.square(alg.add(a, b))
        inv_a_bits = [circ.variable() for _ in range(N)]
        inv_b_bits = [circ.variable() for _ in range(N)]
        zero = circ.variable()
        branch = circ.variable()
        inv_a = alg.from_bits(inv_a_bits)
        inv_b = alg.from_bits(inv_b_bits)
        zero_expr = alg.expression(((zero, 1),))
        branch_expr = alg.expression(((branch, 1),))
        circ.require_zero(alg.add(alg.mul(A, inv_a), alg.one, zero_expr).bits())
        circ.require_zero(alg.mul(zero_expr, A).bits())
        circ.require_zero(alg.mul(zero_expr, inv_a).bits())
        circ.require_zero(alg.add(alg.mul(B, inv_b), alg.one).bits())
        q = alg.mul(alg.mul(A, D), alg.square(inv_b))
        circ.require_zero([circ.xor(wire for wire, coeff in q.terms
                               if design.trace(coeff))])
        h = alg.expression((wire, design.halftrace(coeff ^ design.trace(coeff)))
                           for wire, coeff in q.terms)
        quad = alg.mul(alg.mul(B, inv_a), alg.add(h, branch_expr))
        linear = alg.mul(D, inv_b)
        z = alg.add(quad, alg.mul(zero_expr, linear))
        circ.require_zero(alg.add(z, alg.from_bits(wires['middle'][middle])).bits())
        extras.append({'inverse_a': inv_a_bits, 'inverse_b': inv_b_bits,
                       'zero': zero, 'branch': branch})
    return extras


def main():
    protocol = json.loads((HERE / 'build_protocol.json').read_text())
    assert protocol['status'] == 'FROZEN_BEFORE_FUNCTIONAL_S3_BUILD'
    for item in protocol['sources'].values():
        assert sha(item['path']) == item['sha256']
    chart = json.loads((HERE / 'chart_result.json').read_text())
    assert chart['status'] == 'PASS_N41_W11_S3_CHART_AUDIT'
    audit = json.loads((ROOT / 'n41_w11_fourpair_public_20261019' / 'audit_result.json').read_text())
    fixed = FixedSeed(41, [0, 3], 56, 11)
    raw_target = tuple(audit['raw_target_point'])
    targets = [F.frob(F.inverse(raw_target[0]), k) for k in range(41)]
    start = time.monotonic()
    circ, wires, _ = design.build(targets,
        ROOT / 'n41_w11_fourpair_public_20261019' / 'join4_input.tsv')
    extra = extra_constraints(circ, wires)
    built = time.monotonic()
    initial = {}

    def bind(bits, value):
        for i, wire in enumerate(bits):
            assert wire not in initial
            initial[wire] = (value >> i) & 1

    points = []
    for slot, row in enumerate(audit['rows']):
        code = row['source_code']
        bind(wires['mask'][slot], code)
        bind(wires['source_inverse'][slot], F.inverse(fixed.source_product(code)))
        point = tuple(row['pair_point'])
        points.append(point)
        unrotated = fixed.e.frob(point, (41 - row['rotation']) % 41)
        bind(wires['out'][slot], F.inverse(unrotated[0]))
    middles = [fixed.e.add(points[0], points[1]), fixed.e.add(points[2], points[3])]
    for i, point in enumerate(middles):
        bind(wires['middle'][i], F.inverse(point[0]))
    bind(wires['selector'], 3)
    for i, (left, right) in enumerate([(0, 1), (2, 3)]):
        a = F.inverse(points[left][0])
        b = F.inverse(points[right][0])
        z = F.inverse(middles[i][0])
        ab = F.mul(a, b)
        A, B, D = F.square(ab) ^ 1, ab, F.square(a ^ b)
        bind(extra[i]['inverse_b'], F.inverse(B))
        bind(extra[i]['inverse_a'], F.inverse(A) if A else 0)
        initial[extra[i]['zero']] = int(A == 0)
        if A:
            q = mul(A, D, F.square(F.inverse(B)))
            h = design.halftrace(q)
            unit = mul(B, F.inverse(A))
            roots = [mul(unit, h), mul(unit, h) ^ unit]
            initial[extra[i]['branch']] = roots.index(z)
        else:
            initial[extra[i]['branch']] = 0
    checked = check_assignment(circ, complete_assignment(circ, initial))
    formula = HERE / 'functional_s3.xcnf'
    circ.write(formula)
    result = {'status': 'PASS_FUNCTIONAL_S3_FULL_ASSIGNMENT', 'candidate_id': None,
              'curve_id': protocol['curve_id'], 'build_seconds': built - start,
              'control_seconds': time.monotonic() - built,
              'counts': {'variables': circ.next_var - 1, 'and_gates': circ.and_count,
                         'clauses': len(circ.clauses), 'xor_rows': len(circ.xors)},
              'assignment_check': checked, 'formula_sha256': sha(formula),
              'protocol_sha256': sha(HERE / 'build_protocol.json'),
              'script_sha256': sha(__file__),
              'peak_rss_raw': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    (HERE / 'build_result.json').write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
