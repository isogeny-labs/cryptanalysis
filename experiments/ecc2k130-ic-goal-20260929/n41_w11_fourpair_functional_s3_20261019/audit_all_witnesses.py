"""Evaluate the functional-S3 circuit on all 32 independently replayed hits."""
import hashlib
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
from build import F, design, extra_constraints, FixedSeed, complete_assignment, check_assignment


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    chart = json.loads((HERE / 'chart_result.json').read_text())
    input_path = ROOT / 'n41_w11_fourpair_public_20261019' / 'join4_input.tsv'
    states = {}
    raw_target = None
    for line in input_path.read_text().splitlines():
        row = line.split()
        if row and row[0] == 'T':
            raw_target = int(row[2]), int(row[3])
        if row and row[0] == 'S':
            states[int(row[1]), int(row[2])] = {'code': int(row[3]),
                'point': (int(row[9]), int(row[10]))}
    assert raw_target and len(states) == 4 * 1124
    fixed = FixedSeed(41, [0, 3], 56, 11)
    targets = [F.frob(F.inverse(raw_target[0]), k) for k in range(41)]
    machine, wires, _ = design.build(targets, input_path)
    extras = extra_constraints(machine, wires)
    with tempfile.NamedTemporaryFile(prefix='functional-s3-audit-', suffix='.xcnf',
                                     dir='/private/tmp') as temporary:
        machine.write(Path(temporary.name))
        formula_sha256 = sha(temporary.name)
    assert formula_sha256 == sha(HERE / 'functional_s3.xcnf')
    checks = []
    for witness in chart['witnesses']:
        orientation = witness['orientation']
        rows = [states[i, sid] for i, sid in enumerate(witness['state_ids'])]
        points = [row['point'] for row in rows]
        middles = [fixed.e.add(points[0], points[1]),
                   fixed.e.add(points[2], points[3])]
        target = fixed.e.frob(raw_target, orientation)
        assert fixed.e.add(*middles) == target
        initial = {}

        def bind(bits, value):
            for j, wire in enumerate(bits):
                assert wire not in initial
                initial[wire] = value >> j & 1

        for slot, row in enumerate(rows):
            code = row['code']
            assert fixed.source_valid(fixed.source_a(code))
            bind(wires['mask'][slot], code)
            bind(wires['source_inverse'][slot], F.inverse(fixed.source_product(code)))
            unrotated = fixed.e.frob(row['point'], (41 - design.ROTATIONS[slot]) % 41)
            bind(wires['out'][slot], F.inverse(unrotated[0]))
        for i, point in enumerate(middles):
            bind(wires['middle'][i], F.inverse(point[0]))
        bind(wires['selector'], orientation)
        for i, (left, right) in enumerate([(0, 1), (2, 3)]):
            a, b = F.inverse(points[left][0]), F.inverse(points[right][0])
            B = F.mul(a, b)
            A = F.square(B) ^ 1
            bind(extras[i]['inverse_a'], F.inverse(A) if A else 0)
            bind(extras[i]['inverse_b'], F.inverse(B))
            initial[extras[i]['zero']] = int(A == 0)
            initial[extras[i]['branch']] = witness['branches'][i] or 0
        checked = check_assignment(machine, complete_assignment(machine, initial))
        assert checked == {'clauses': len(machine.clauses),
                           'xor_rows': len(machine.xors)}
        checks.append({'orientation': orientation,
                       'state_ids': witness['state_ids'], 'assignment_check': checked})
    assert len(checks) == 32
    out = {'status': 'PASS_ALL_32_FUNCTIONAL_S3_ASSIGNMENTS',
           'candidate_id': None, 'curve_id': chart['curve_id'],
           'source_sha256': sha(input_path), 'chart_sha256': sha(HERE / 'chart_result.json'),
           'script_sha256': sha(__file__), 'formula_sha256': formula_sha256,
           'checks': checks}
    (HERE / 'all_witnesses_result.json').write_text(json.dumps(out, sort_keys=True, indent=2) + '\n')
    print(json.dumps({'status': out['status'], 'assignments': len(checks)}, sort_keys=True))


if __name__ == '__main__':
    main()
