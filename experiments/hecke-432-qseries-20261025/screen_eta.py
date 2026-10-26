"""Enumerate bounded eta quotients against the level-432 newform q-series."""
from hashlib import sha256
import itertools
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha(path):
    return sha256(path.read_bytes()).hexdigest()


def candidates(level, support_cap, exponent_cap):
    divisors = [d for d in range(1, level+1) if level % d == 0]
    found = set()
    for d in divisors:
        if d == 6 and exponent_cap >= 4:
            found.add(((d, 4),))
    for d1, d2 in itertools.combinations(divisors, 2):
        numerator = 24-4*d2
        denominator = d1-d2
        if numerator % denominator:
            continue
        r1 = numerator//denominator
        r2 = 4-r1
        if r1 and r2 and max(abs(r1), abs(r2)) <= exponent_cap:
            found.add(((d1, r1), (d2, r2)))
    if support_cap >= 3:
        for d1, d2, d3 in itertools.combinations(divisors, 3):
            for r1 in range(-exponent_cap, exponent_cap+1):
                if r1 == 0:
                    continue
                numerator = 24-4*d3-(d1-d3)*r1
                denominator = d2-d3
                if numerator % denominator:
                    continue
                r2 = numerator//denominator
                r3 = 4-r1-r2
                if r2 and r3 and max(abs(r2), abs(r3)) <= exponent_cap:
                    found.add(((d1, r1), (d2, r2), (d3, r3)))
    return sorted(found)


def eta_coefficients(factors, precision):
    # q^1 times the product of (1-q^(d*n))^r, truncated before q^precision.
    series = [1]+[0]*(precision-2)
    for divisor, exponent in factors:
        for multiple in range(divisor, precision-1, divisor):
            for _ in range(abs(exponent)):
                if exponent > 0:
                    for k in range(precision-2, multiple-1, -1):
                        series[k] -= series[k-multiple]
                else:
                    for k in range(multiple, precision-1):
                        series[k] += series[k-multiple]
    return [0]+series


def main():
    protocol = json.loads((HERE/'protocol.json').read_text())
    qseries_path = HERE/'qseries_result.json'
    qseries = json.loads(qseries_path.read_text())
    assert qseries['protocol_sha256'] == sha(HERE/'protocol.json')
    rule = protocol['eta_screen']
    precision = rule['coefficient_match_precision']
    expected = qseries['newform_coefficients'][:precision]
    options = candidates(protocol['level'], rule['support_cap'], rule['absolute_exponent_cap'])
    rows = []
    for factors in options:
        assert sum(exponent for _, exponent in factors) == 4
        assert sum(divisor*exponent for divisor, exponent in factors) == 24
        coefficients = eta_coefficients(factors, precision)
        prefix = next((n for n in range(precision) if coefficients[n] != expected[n]), precision)
        rows.append({'factors': [list(item) for item in factors],
                     'matching_coefficients_before_first_difference': prefix,
                     'first_different_degree': None if prefix == precision else prefix,
                     'first_different_coefficient': None if prefix == precision else coefficients[prefix],
                     'second_modularity_congruence_mod_24':
                         sum((protocol['level']//d)*r for d,r in factors) % 24})
    rows.sort(key=lambda row: (-row['matching_coefficients_before_first_difference'],
                               row['factors']))
    result = {'status': 'PASS_BOUNDED_ETA_QSERIES_SCREEN',
              'protocol_sha256': sha(HERE/'protocol.json'),
              'qseries_sha256': sha(qseries_path),
              'source_sha256': sha(HERE/'screen_eta.py'),
              'candidate_count': len(rows),
              'full_precision_matches': [row for row in rows if row['first_different_degree'] is None],
              'best_prefix': rows[0]['matching_coefficients_before_first_difference'],
              'candidates': rows,
              'candidate_id': None, 'timing_claim': None}
    (HERE/'eta_result.json').write_text(json.dumps(result, sort_keys=True, indent=2)+'\n')
    print(json.dumps({'status': result['status'], 'candidate_count': len(rows),
                      'full_precision_matches': len(result['full_precision_matches']),
                      'best_prefix': result['best_prefix']}, sort_keys=True))


if __name__ == '__main__':
    main()
