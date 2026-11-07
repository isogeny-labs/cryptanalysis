"""Frozen source-free search for a prime with observable special B triples."""
import importlib.util
import json
from hashlib import sha256
from pathlib import Path

HERE = Path(__file__).resolve().parent


def prime(n):
    if n < 2:
        return False
    for d in range(2, int(n**0.5)+1):
        if n % d == 0:
            return False
    return True


def main():
    protocol_path = HERE/'sieve_protocol.json'
    protocol = json.loads(protocol_path.read_text())
    assert protocol['status'] == 'FROZEN_BEFORE_SPECIAL_B_SIEVE'
    for name, record in protocol['inputs'].items():
        assert sha256(Path(record['path']).read_bytes()).hexdigest() == record['sha256'], name
    spec = importlib.util.spec_from_file_location('special_sieve_inverse',
                                                  protocol['inputs']['inverse_filter']['path'])
    inverse = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(inverse)
    resolvent = json.loads(Path(protocol['inputs']['resolvent']['path']).read_text())
    branch = json.loads(Path(protocol['inputs']['branch']['path']).read_text())
    cells = []
    selected = None
    for p in range(1040, protocol['prime_cap_exclusive']):
        if not prime(p) or p % 12 != 7 or pow((-15) % p, (p-1)//2, p) != 1:
            continue
        xs = [x for x in range(p) if pow(x, 3, p) == 1]
        ys = [y for y in range(p) if y*y % p == (-15) % p]
        assert len(xs) == 3 and len(ys) == 2
        special = []
        for x in xs:
            for y in ys:
                xe = (x**3-64)*pow(x*x, -1, p) % p
                ye = y*(x**3+128)*pow(x, -3, p) % p
                special.append(((x, y), (xe, ye)))
        hits = []
        c_points = inverse.curve_points(p, 'C')
        for c in c_points:
            coeffs = inverse.resolvent_coefficients(resolvent['terms'], c, p)
            for b, e in special:
                if inverse.horner(coeffs, e[0], p):
                    continue
                value = inverse.evaluate_pair(c, e, p, resolvent, branch)
                if value['status'] == 'VALID' and value['B_point'] == list(b):
                    hits.append({'C_point': list(c), 'E_point': list(e), 'B_point': list(b)})
        cell = {'prime': p, 'C_group_order': len(c_points)+1,
                'special_B_points': len(special), 'valid_special_triples': len(hits),
                'hits': hits}
        cells.append(cell)
        print(json.dumps({'prime': p, 'valid_special_triples': len(hits)}), flush=True)
        if hits:
            selected = p
            break
    result = {'status': 'SELECTED_SPECIAL_B_PRIME' if selected is not None else
              'BOUNDED_NO_SPECIAL_B_PRIME',
              'protocol_sha256': sha256(protocol_path.read_bytes()).hexdigest(),
              'source_code_sha256': sha256(Path(__file__).read_bytes()).hexdigest(),
              'selected_prime': selected, 'cells': cells}
    (HERE/'sieve_result.json').write_text(json.dumps(result, sort_keys=True, indent=2)+'\n')
    print(json.dumps({'status': result['status'], 'selected_prime': selected,
                      'cells': len(cells)}, sort_keys=True))


if __name__ == '__main__':
    main()
