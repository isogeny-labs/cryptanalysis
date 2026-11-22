"""Find the first later p = 1 mod 12 with a noncuspidal X0(432) source."""
import json
from math import gcd
from pathlib import Path

from sage.all import CuspForms, EllipticCurve, GF, prime_range

HERE = Path(__file__).resolve().parent


def phi(n):
    return sum(gcd(k, n) == 1 for k in range(1, n + 1))


def rational_cusps(p):
    return sum(phi(gcd(d, 432 // d)) for d in range(1, 433)
               if 432 % d == 0 and (p - 1) % gcd(d, 432 // d) == 0)


def main():
    M = CuspForms(432, 2)
    rows = []
    for pp in prime_range(938, 1200):
        p = int(pp)
        if p % 12 != 1:
            continue
        trace = int(M.hecke_operator(p).trace())
        total = p + 1 - trace
        cusps = rational_cusps(p)
        b_order = int(EllipticCurve(GF(p), [0, 0, 0, 0, -16]).cardinality())
        row = {'prime': p, 'hecke_trace': trace, 'X0_points': total,
               'rational_cusps': cusps, 'noncuspidal_points': total - cusps,
               'B_group_order': b_order}
        assert row['noncuspidal_points'] >= 0 and b_order % 3 == 0
        rows.append(row)
        print(json.dumps(row, sort_keys=True), flush=True)
        if row['noncuspidal_points'] > 0:
            break
    assert rows and rows[-1]['noncuspidal_points'] > 0
    out = {'status': 'FIRST_NONEMPTY_RATIONAL_KERNEL_PRIME_SCREEN',
           'selection_rule': 'smallest prime greater than 937 with p mod 12 = 1 and positive noncuspidal X0(432) count',
           'screened': rows, 'selected_prime': rows[-1]['prime']}
    (HERE / 'screen_result.json').write_text(json.dumps(out, sort_keys=True, indent=2) + '\n')
    print(json.dumps({'selected_prime': out['selected_prime'], 'screened_count': len(rows)}, sort_keys=True))


if __name__ == '__main__':
    main()
