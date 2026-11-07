"""Independent F_23[u]/(u²+2u+17) arithmetic audit of both local rows."""
import json
from hashlib import sha256
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
P = 23


def element(text):
    value = text.replace(' ', '')
    if 'u' not in value:
        return (int(value) % P, 0)
    coefficient, tail = value.split('*u')
    constant = int(tail) if tail else 0
    return (constant % P, int(coefficient) % P)


def add(x, y):
    return ((x[0] + y[0]) % P, (x[1] + y[1]) % P)


def neg(x):
    return ((-x[0]) % P, (-x[1]) % P)


def mul(x, y):
    # u² = -2u - 17.
    a, b = x
    c, d = y
    return ((a * c - 17 * b * d) % P,
            (a * d + b * c - 2 * b * d) % P)


def main():
    protocol_path = HERE / 'protocol.json'
    protocol = json.loads(protocol_path.read_text())
    for name, relative in protocol['input_paths'].items():
        assert sha256((ROOT / relative).read_bytes()).hexdigest() == protocol['input_sha256'][name]
    receipt = json.loads((HERE / 'attempt.json').read_text())
    source_path = HERE / 'run_sage.py'
    assert receipt['status'] == 'COMPLETED' and receipt['returncode'] == 0
    assert receipt['source_sha256'] == sha256(source_path.read_bytes()).hexdigest()
    result_path = HERE / 'result.json'
    result = json.loads(result_path.read_text())
    assert result['status'] == 'PASS_P23_QUADRATIC_CLUSTER_REPLAY'
    assert result['protocol_sha256'] == sha256(protocol_path.read_bytes()).hexdigest()
    assert [(row['side'], row['place_index']) for row in result['rows']] == [
        (site['side'], site['place_index']) for site in protocol['sites']]
    delta = (10, 14)
    witness = (10, 13)
    assert mul(witness, witness) == delta
    for row in result['rows']:
        assert row['residue_quadratic'] == ['17', '2', '1']
        A, B, C = map(element, row['taylor_coefficients_over_residue_extension'])
        calculated = add(mul(B, B), neg(mul((4, 0), mul(A, C))))
        assert calculated == element(row['normalized_discriminant']) == delta
        assert row['quadratic_character'] == 1
        assert row['relative_residue_degrees'] == [2, 2]
    final_path = ROOT / 'experiments/hecke-432-j1728-relative-quartic-local-factor-20261026/final_result.json'
    final = json.loads(final_path.read_text())
    assert sorted(tuple(x) for x in final['parity_case_keys']) == [
        (23, 0, 'left'), (23, 3, 'right')]
    p23 = next(row for row in final['rows'] if row['prime'] == 23)
    for row in result['rows']:
        entry = p23['sides'][row['side']]['places'][row['place_index']]
        assert entry['relative_residue_degrees'] == row['relative_residue_degrees']
    out = {'status': 'PASS_INDEPENDENT_P23_RESIDUE_EXTENSION_AUDIT',
           'result_sha256': sha256(result_path.read_bytes()).hexdigest(),
           'prior_final_result_sha256': sha256(final_path.read_bytes()).hexdigest(),
           'modulus': [17, 2, 1], 'square_root_witness': [10, 13],
           'normalized_discriminant': [10, 14]}
    (HERE / 'audit.json').write_text(json.dumps(out, sort_keys=True, indent=2) + '\n')
    print(json.dumps(out, sort_keys=True))


if __name__ == '__main__':
    main()
