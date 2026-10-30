"""Select two new D79 primes using only public field and curve-order predicates."""
import json
from pathlib import Path

from sage.all import EllipticCurve, GF, factor, is_prime

HERE = Path(__file__).resolve().parent
PLAN = json.loads((HERE / 'inputs.json').read_text())


def main():
    rule = PLAN['selection']
    checked, selected = [], []
    for v in range(rule['v_start'], rule['v_end'] + 1, rule['v_step']):
        p = v*v + 316
        if not is_prime(p):
            continue
        E = EllipticCurve(GF(p), [0, -1, 1, -10, -20])
        n = int(E.cardinality())
        q = int(max(prime for prime, _ in factor(n)))
        eligible = n % 5 == 0 and (p-1) % 5 != 0 and q >= 53
        row = {'v': v, 'p': p, 'curve_order': n, 'largest_prime_factor': q,
               'eligible': eligible}
        checked.append(row)
        if eligible:
            selected.append(row)
            if len(selected) == rule['take_first']:
                break
    out = {'schema': 'hecke-d79-priority-prescreen-v1',
           'status': 'COMPLETE' if len(selected) == rule['take_first'] else 'INSUFFICIENT_CASES',
           'checked_prime_cases': checked, 'selected': selected}
    (HERE / 'prescreen.json').write_text(json.dumps(out, indent=2, sort_keys=True) + '\n')
    print(json.dumps({'status': out['status'], 'selected': selected}))


if __name__ == '__main__':
    main()
