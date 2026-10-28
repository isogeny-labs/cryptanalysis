"""Independent reduced-form enumeration and sparse modular matrix replay."""
import hashlib
import json
from collections import Counter
from math import gcd, isqrt
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE / 'data' / 'exp11_class_walk_D39_f6.json'


def class_number(discriminant):
    count = 0
    for a in range(1, isqrt(-discriminant // 3) + 2):
        for b in range(-a, a + 1):
            numerator = b * b - discriminant
            if numerator % (4 * a):
                continue
            c = numerator // (4 * a)
            if a > c or (b < 0 and (abs(b) == a or a == c)):
                continue
            if gcd(gcd(a, abs(b)), c) == 1:
                count += 1
    return count


def rank(rows, modulus, columns):
    pivots = {}
    for row in rows:
        current = {int(k): int(v) % modulus for k, v in row.items() if int(v) % modulus}
        assert all(0 <= k < columns for k in current)
        while current:
            pivot = min(current)
            if pivot not in pivots:
                inverse = pow(current[pivot], -1, modulus)
                pivots[pivot] = {k: v * inverse % modulus for k, v in current.items()}
                break
            multiplier = current[pivot]
            for k, v in pivots[pivot].items():
                value = (current.get(k, 0) - multiplier * v) % modulus
                if value:
                    current[k] = value
                else:
                    current.pop(k, None)
    return len(pivots)


def main():
    data = json.loads(SOURCE.read_text())
    assert (data['DK'], data['f'], data['p'], data['u'], data['hecke_primes']) == (-39, 6, 367, 8, [2, 3])
    class_numbers = {d: class_number(-39*d*d) for d in (1, 2, 3, 6)}
    assert class_numbers == {1: 4, 2: 4, 3: 12, 6: 12}
    assert data['class_size'] == 2*sum(class_numbers.values()) == 64
    assert len(data['column_points']) == len(set(data['column_points'])) == 64
    rows = data['relation_rows']
    assert len(rows) == data['relations'] == 48
    degree_counts = Counter()
    for row in rows:
        values = [int(v) for v in row.values()]
        assert all(0 <= int(k) < 64 for k in row)
        assert sum(values) == 5
        degree_counts[{4: 2, 5: 3}[len(row)]] += 1
    assert dict(degree_counts) == {2: 32, 3: 16}
    checks = {}
    for q in (11, 1009, 1000000007):
        direct = rank(rows, q, 64)
        atkin = rank(rows + data['atkin_lehner_rows'], q, 64)
        assert (direct, atkin) == (40, 52)
        checks[str(q)] = {'hecke_rank': direct, 'with_atkin_lehner_rank': atkin}
    result = {'status': 'verified', 'source_sha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
              'class_numbers': {str(k): v for k, v in class_numbers.items()},
              'distinct_points': 64, 'row_degree_counts': dict(degree_counts), 'rank_checks': checks}
    (HERE / 'matrix_audit.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
