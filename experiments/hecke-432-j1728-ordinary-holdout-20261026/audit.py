"""Independent finite-field audit of the ordinary j=1728 screens."""
import json
from collections import Counter
from hashlib import sha256
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def value(terms, x, y, p, xe=None):
    out = 0
    for t in terms:
        if xe is None:
            raw = t['coefficient']
            a, b = (map(int, raw.split('/')) if '/' in raw else (int(raw), 1))
            out += a * pow(b, -1, p) * pow(x, t['x_power'], p) * pow(y, t['y_power'], p)
        else:
            out += int(t['integer_coefficient']) * pow(x, t['x_C_exponent'], p) * pow(y, t['y_C_exponent'], p) * pow(xe, t['x_E_exponent'], p)
    return out % p


def horner(a, x, p):
    z = 0
    for c in reversed(a):
        z = (z * x + c) % p
    return z


def audit_cell(cell, coordinate, resolvent, eliminant):
    p = cell['prime']
    ys = {}
    for y in range(p):
        ys.setdefault(y*y % p, []).append(y)
    cs = []
    half = pow(2, -1, p)
    for x in range(p):
        for z in ys.get((4*(x*x*x-7)+1) % p, []):
            y = (z-1)*half % p
            den = value(coordinate['source_j']['denominator'], x, y, p)
            if den and (-value(coordinate['source_j']['numerator'], x, y, p)*pow(den, -1, p)) % p == 1728 % p:
                cs.append((x,y))
    assert sorted(cs) == sorted(map(tuple, cell['j1728_C_points']))
    roots = [x for x in range(p) if horner(eliminant, x, p) == 0]
    assert sorted(set(x for x,_ in cs)) == roots
    pairs = 0
    for x,y in cs:
        coefficients = [0]*13
        for t in resolvent['terms']:
            e = t['x_E_exponent']
            coefficients[e] = (coefficients[e] + int(t['integer_coefficient'])
                               * pow(x, t['x_C_exponent'], p)
                               * pow(y, t['y_C_exponent'], p)) % p
        for xe in range(p):
            if horner(coefficients, xe, p) == 0:
                pairs += len(ys.get((xe**3+432) % p, []))
    assert pairs == cell['resolvent_pairs']
    return {'prime': p, 'eliminant_x_roots': len(roots), 'C_points': len(cs), 'rational_CE_pairs': pairs}


def main():
    coordinate_path = ROOT/'experiments/hecke-27-coordinate-bridge-20261025/coordinate_map.json'
    resolvent_path = ROOT/'experiments/hecke-432-relative-resolvent-20261025/relative_resolvent.json'
    eliminant_path = ROOT/'experiments/hecke-432-j1728-cubic-twist-holdout-20261026/elimination_result.json'
    coordinate = json.loads(coordinate_path.read_text())
    resolvent = json.loads(resolvent_path.read_text())
    eliminant = list(map(int, json.loads(eliminant_path.read_text())['factors'][0]['coefficients_low_to_high']))
    results = {}
    for name in ('sieve', 'sieve_split'):
        path = HERE/f'{name}_result.json'
        screen = json.loads(path.read_text())
        rows = [audit_cell(c, coordinate, resolvent, eliminant) for c in screen['cells']]
        results[name] = {'screen_sha256': sha256(path.read_bytes()).hexdigest(),
                         'cells': len(rows), 'C_nonempty_primes': [r['prime'] for r in rows if r['C_points']],
                         'C_points': sum(r['C_points'] for r in rows),
                         'rational_CE_pairs': sum(r['rational_CE_pairs'] for r in rows),
                         'eliminant_root_histogram': dict(Counter(r['eliminant_x_roots'] for r in rows))}
    out = {'status':'PASS_INDEPENDENT_ORDINARY_J1728_CE_AUDIT',
           'input_sha256': {str(p.relative_to(ROOT)):sha256(p.read_bytes()).hexdigest()
                            for p in (coordinate_path,resolvent_path,eliminant_path)},
           'results':results}
    (HERE/'audit.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
    print(json.dumps(out['results'],sort_keys=True))


if __name__ == '__main__':
    main()
