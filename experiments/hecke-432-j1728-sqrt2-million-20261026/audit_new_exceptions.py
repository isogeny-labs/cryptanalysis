"""Exhaustive finite-field source and E enumeration for new gate exceptions."""
import importlib.util
import json
from collections import Counter, defaultdict
from hashlib import sha256
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load(path):
    spec = importlib.util.spec_from_file_location('frozen_inverse_filter', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def rational(terms, x, y, p):
    total = 0
    for term in terms:
        raw = term['coefficient']
        numerator, denominator = (map(int, raw.split('/')) if '/' in raw
                                   else (int(raw), 1))
        total += (numerator * pow(denominator, -1, p)
                  * pow(x, term['x_power'], p) * pow(y, term['y_power'], p))
    return total % p


def horner(coefficients, z, p):
    value = 0
    for coefficient in reversed(coefficients):
        value = (value * z + coefficient) % p
    return value


def main():
    protocol_path = HERE / 'exception_protocol.json'
    protocol = json.loads(protocol_path.read_text())
    assert protocol['status'] == 'FROZEN_BEFORE_NEW_EXCEPTION_ENUMERATION'
    inputs = {}
    for name, (raw_path, digest) in protocol['inputs'].items():
        path = Path(raw_path)
        assert sha256(path.read_bytes()).hexdigest() == digest
        inputs[name] = path
    scan = json.loads(inputs['scan'].read_text())
    primes = [entry['prime'] for entry in scan['new_exception_cells']]
    assert primes == protocol['expected_new_exceptions']
    coordinates = json.loads(inputs['coordinate_map'].read_text())['source_j']
    resolvent = json.loads(inputs['resolvent'].read_text())
    terms = resolvent['terms']
    branch = json.loads(inputs['branch_formula'].read_text())
    inverse = load(inputs['inverse_filter'])
    cells = []
    for p in primes:
        squares = defaultdict(list)
        for z in range(p):
            squares[z * z % p].append(z)
        half = pow(2, -1, p)
        sources = []
        for x in range(p):
            for z in squares[(4 * (x * x * x - 7) + 1) % p]:
                y = (z - 1) * half % p
                denominator = rational(coordinates['denominator'], x, y, p)
                if (denominator and
                    -rational(coordinates['numerator'], x, y, p)
                    * pow(denominator, -1, p) % p == 1728 % p):
                    sources.append((x, y))
        rows = []
        root_count = 0
        for x, y in sources:
            coefficients = [0] * 13
            for term in terms:
                exponent = term['x_E_exponent']
                coefficients[exponent] = (
                    coefficients[exponent] + int(term['integer_coefficient'])
                    * pow(x, term['x_C_exponent'], p)
                    * pow(y, term['y_C_exponent'], p)) % p
            for xe in range(p):
                if horner(coefficients, xe, p):
                    continue
                root_count += 1
                for ye in squares[(xe * xe * xe + 432) % p]:
                    c_point = (x, y)
                    e_point = (xe, ye)
                    value = inverse.evaluate_pair(c_point, e_point, p,
                                                  resolvent, branch)
                    rows.append({'C_point': list(c_point),
                                 'E_point': list(e_point), **value})
        mix = dict(Counter(row['status'] for row in rows))
        cells.append({'prime': p, 'C_points': len(sources),
                      'rational_x_E_roots': root_count,
                      'rational_CE_pairs': len(rows),
                      'status_mix': mix, 'rows': rows})
        print(json.dumps({key: cells[-1][key] for key in
                          ('prime', 'C_points', 'rational_x_E_roots',
                           'rational_CE_pairs', 'status_mix')}), flush=True)
    output = {'status': 'EXACT_DIRECT_NEW_EXCEPTION_CLASSIFICATION',
              'protocol_sha256': sha256(protocol_path.read_bytes()).hexdigest(),
              'source_sha256': sha256(Path(__file__).read_bytes()).hexdigest(),
              'cells': cells}
    (HERE / 'exception_result.json').write_text(
        json.dumps(output, sort_keys=True, indent=2) + '\n')


if __name__ == '__main__':
    main()
