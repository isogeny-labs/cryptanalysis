"""Enumerate the frozen pair source from mask bits and curve arithmetic."""
import hashlib
import json
import sys
from pathlib import Path

D = Path(__file__).resolve().parent
ROOT = D.parent
sys.path.insert(0, str(ROOT.parent / 'koblitz-polynomial-w-pair-20260925'))
from pair_oracle import Curve, Field, coordinate, half_trace

SOURCE = ROOT / 'n41_sixpair_shared_target_20261017' / 'join_input.tsv'
GEOMETRY = ROOT / 'n41_w8_fixed_sum_table_20261009' / 'geometry.json'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def frob(field, value, count):
    for _ in range(count):
        value = field.mul(value, value)
    return value


def endpoint(field, curve, basis, mask):
    u = coordinate(basis, mask)
    assert u not in (0, 1)
    x = field.inv(u) ^ 1
    assert x
    x2 = field.mul(x, x)
    rhs = x ^ field.inv(x2)
    z = half_trace(field, rhs)
    assert field.mul(z, z) ^ z == rhs
    y = field.mul(x, z)
    base = (x, y)
    assert curve.on_curve(base)
    assert curve.neg(base) == (x, y ^ x)
    return base, curve.neg(base)


def main():
    protocol = json.loads((D / 'implicit_protocol.json').read_text())
    assert protocol['source_sha256'] == sha(SOURCE)
    assert protocol['geometry_sha256'] == sha(GEOMETRY)
    assert protocol['producer_sha256'] == sha(Path(__file__))
    geometry = json.loads(GEOMETRY.read_text())
    assert geometry['fixed_seed_sum_code'] == 56
    assert geometry['rotations'][:6] == [0, 6, 12, 18, 24, 30]
    permitted = geometry['permitted_canonical_a']
    assert len(permitted) == 40
    field = Field(41, [0, 3])
    curve = Curve(field, 0)
    basis = geometry['blocks'][0]['basis']
    lines = SOURCE.read_text().splitlines()
    assert lines[0].split()[:3] == ['ECC2K41', '6', '160']
    source = {}
    for line in lines[1:]:
        parts = line.split()
        slot, state = map(int, parts[1:3])
        source[slot, state] = tuple(map(int, parts[9:11]))
    assert len(source) == 960
    mapping = {}
    endpoint_checks = 0
    for code, a in enumerate(permitted):
        b = a ^ 56
        pa = endpoint(field, curve, basis, a)
        pb = endpoint(field, curve, basis, b)
        endpoint_checks += 4
        for slot, rotation in enumerate(geometry['rotations'][:6]):
            points_a = [tuple(frob(field, coordinate, rotation) for coordinate in p)
                        for p in pa]
            points_b = [tuple(frob(field, coordinate, rotation) for coordinate in p)
                        for p in pb]
            expected = {source[slot, 4 * code + sign]: 4 * code + sign
                        for sign in range(4)}
            assert len(expected) == 4
            assigned = []
            for sign_a in range(2):
                for sign_b in range(2):
                    point = curve.add(points_a[sign_a], points_b[sign_b])
                    assert point in expected
                    assigned.append(expected[point])
            assert len(set(assigned)) == 4
            mapping[f'{slot}:{code}'] = assigned
    witness = (12, 122, 116, 47, 128, 34)
    natural = []
    for slot, state in enumerate(witness):
        code = state // 4
        index = mapping[f'{slot}:{code}'].index(state)
        natural.append({'slot': slot, 'code': code,
                        'sign_a': index // 2, 'sign_b': index % 2,
                        'archived_state': state})
    result = {'status': 'ALL_960_IMPLICIT_POINT_OUTPUTS_MATCH',
              'protocol_sha256': sha(D / 'implicit_protocol.json'),
              'source_sha256': sha(SOURCE),
              'geometry_sha256': sha(GEOMETRY),
              'endpoint_checks': endpoint_checks,
              'point_output_checks': 960,
              'code_sign_to_archived_state': mapping,
              'witness_natural_signs': natural}
    (D / 'implicit_result.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps({k: result[k] for k in ('status', 'endpoint_checks',
                                            'point_output_checks', 'witness_natural_signs')}))


if __name__ == '__main__':
    main()
