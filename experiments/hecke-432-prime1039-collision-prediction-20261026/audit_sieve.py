"""Independent B-polynomial replay of the prospectively selected prime sieve."""
import json
from collections import defaultdict
from hashlib import sha256
from pathlib import Path

HERE = Path(__file__).resolve().parent


def c_points(p):
    roots = defaultdict(list)
    for z in range(p):
        roots[z*z % p].append(z)
    return [(x, (z-1)*pow(2, -1, p) % p)
            for x in range(p) for z in roots[(4*(x*x*x-7)+1) % p]]


def eval_terms(terms, c, v, p, variable):
    x, y = c
    return sum(int(t['integer_coefficient']) *
               pow(x, t['x_C_exponent'], p) * pow(y, t['y_C_exponent'], p) *
               pow(v, t[variable], p) for t in terms) % p


def special_b(p):
    xs = [x for x in range(p) if pow(x, 3, p) == 1]
    ys = [y for y in range(p) if y*y % p == (-15) % p]
    assert len(xs) == 3 and len(ys) == 2
    return [(x, y) for x in xs for y in ys]


def main():
    protocol_path = HERE/'sieve_protocol.json'
    protocol = json.loads(protocol_path.read_text())
    for name, record in protocol['inputs'].items():
        assert sha256(Path(record['path']).read_bytes()).hexdigest() == record['sha256'], name
    base = json.loads((HERE/'protocol.json').read_text())
    b_record = base['inputs']['b_resolvent']
    assert sha256(Path(b_record['path']).read_bytes()).hexdigest() == b_record['sha256']
    bpoly = json.loads(Path(b_record['path']).read_text())
    branch = json.loads(Path(protocol['inputs']['branch']['path']).read_text())
    sieve = json.loads((HERE/'sieve_result.json').read_text())
    assert sieve['protocol_sha256'] == sha256(protocol_path.read_bytes()).hexdigest()
    previous = json.loads(Path(protocol['inputs']['prior_p1039_screen']['path']).read_text())
    zero_1039 = []
    for shard in previous['shards']:
        path = HERE/shard['file']
        assert sha256(path.read_bytes()).hexdigest() == shard['sha256']
        zero_1039.extend(row for row in json.loads(path.read_text())
                         if row['status'] == 'VALID' and pow(row['B_point'][0], 3, 1039) == 1)
    assert not zero_1039
    cells = []
    for cell in sieve['cells']:
        p = cell['prime']
        valid = []
        polynomial_hits = 0
        for c in c_points(p):
            for xb, yb in special_b(p):
                if eval_terms(bpoly['terms'], c, xb, p, 'x_B_exponent'):
                    continue
                polynomial_hits += 1
                xe = (xb**3-64)*pow(xb*xb, -1, p) % p
                ye = yb*(xb**3+128)*pow(xb, -3, p) % p
                n = eval_terms(branch['numerator_terms'], c, xe, p, 'x_E_exponent')
                d = eval_terms(branch['denominator_terms'], c, xe, p, 'x_E_exponent')
                if d and n == d*xb % p:
                    valid.append({'C_point': list(c), 'E_point': [xe, ye],
                                  'B_point': [xb, yb]})
        actual = {(*r['C_point'], *r['E_point'], *r['B_point']) for r in valid}
        expected = {(*r['C_point'], *r['E_point'], *r['B_point']) for r in cell['hits']}
        assert len(actual) == len(valid) and actual == expected
        cells.append({'prime': p, 'B_polynomial_roots': polynomial_hits,
                      'valid_special_triples': len(actual)})
    assert [x['prime'] for x in cells] == [1051, 1171, 1231]
    assert [x['valid_special_triples'] for x in cells] == [0, 0, 72]
    out = {'status': 'PASS_INDEPENDENT_SPECIAL_B_SIEVE_AUDIT',
           'sieve_protocol_sha256': sha256(protocol_path.read_bytes()).hexdigest(),
           'p1039_valid_special_triples': len(zero_1039), 'cells': cells}
    (HERE/'sieve_audit.json').write_text(json.dumps(out, sort_keys=True, indent=2)+'\n')
    print(json.dumps(out, sort_keys=True))


if __name__ == '__main__':
    main()
