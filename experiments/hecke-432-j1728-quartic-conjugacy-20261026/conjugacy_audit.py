"""Exact rational-coefficient audit of the sqrt(2) conjugacy identities."""
import json
from fractions import Fraction
from hashlib import sha256
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def vector(values):
    return tuple(Fraction(x) for x in values)


def conjugate(value):
    assert len(value) == 2
    return (vector(value[0]), tuple(-x for x in vector(value[1])))


def normalized(value):
    assert len(value) == 2
    return (vector(value[0]), vector(value[1]))


def main():
    protocol_path = HERE / 'protocol.json'
    protocol = json.loads(protocol_path.read_text())
    paths = {name: ROOT / path for name, path in protocol['input_paths'].items()}
    for name, path in paths.items():
        assert sha256(path.read_bytes()).hexdigest() == protocol['input_sha256'][name]
    split = json.loads(paths['split_certificate'].read_text())
    kummer = json.loads(paths['kummer_result'].read_text())
    factors = next(r for r in split['records'] if r['base_degree'] == 8)['factors']
    left, right = [r['coefficients_low_to_high'] for r in factors]
    assert len(left) == len(right) == 5
    quartic_matches = [conjugate(a) == normalized(b) for a, b in zip(left, right)]
    assert all(quartic_matches)
    sides = {r['side']: r for r in kummer['rows']}
    assert set(sides) == {'left', 'right'}
    a, b = sides['left']['radicands'], sides['right']['radicands']
    assert len(a) == len(b) == 3
    radicand_matches = [conjugate(x) == normalized(y) for x, y in zip(a, b)]
    assert all(radicand_matches)
    out = {'status': 'PASS_EXACT_SQRT2_CONJUGACY',
           'protocol_sha256': sha256(protocol_path.read_bytes()).hexdigest(),
           'source_sha256': sha256(Path(__file__).read_bytes()).hexdigest(),
           'quartic_coefficients_checked': len(left),
           'quartic_conjugate_equalities': quartic_matches,
           'kummer_radicands_checked': len(a),
           'radicand_conjugate_equalities': radicand_matches,
           'coefficient_field': 'Q(alpha)[s]/(s^2-2)'}
    (HERE / 'conjugacy_result.json').write_text(json.dumps(out, sort_keys=True, indent=2) + '\n')
    print(json.dumps(out, sort_keys=True))


if __name__ == '__main__':
    main()
