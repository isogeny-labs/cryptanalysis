"""Independent brute-force eta exponent census and binomial-series replay."""
from hashlib import sha256
from itertools import combinations, product
import json
from math import comb
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha(path):
    return sha256(path.read_bytes()).hexdigest()


def brute_candidates(level, support_cap, cap):
    divisors = [d for d in range(1, level+1) if level % d == 0]
    found = set()
    for support in range(1, support_cap+1):
        for ds in combinations(divisors, support):
            for prefix in product(range(-cap, cap+1), repeat=support-1):
                exponents = (*prefix, 4-sum(prefix))
                if any(r == 0 or abs(r) > cap for r in exponents):
                    continue
                if sum(d*r for d,r in zip(ds, exponents)) == 24:
                    found.add(tuple(zip(ds, exponents)))
    return found


def binomial_eta_series(factors, precision):
    max_degree = precision-2
    coefficients = [1]+[0]*max_degree
    for divisor, exponent in factors:
        for multiple in range(divisor, max_degree+1, divisor):
            limit = max_degree//multiple
            if exponent > 0:
                local = [(-1)**j*comb(exponent, j) for j in range(min(exponent,limit)+1)]
            else:
                local = [comb(-exponent+j-1, j) for j in range(limit+1)]
            updated = [0]*(max_degree+1)
            for old_degree, old_coefficient in enumerate(coefficients):
                if old_coefficient:
                    for j, factor in enumerate(local):
                        new_degree = old_degree+j*multiple
                        if new_degree <= max_degree:
                            updated[new_degree] += old_coefficient*factor
            coefficients = updated
    return [0]+coefficients


def main():
    protocol_path = HERE/'protocol.json'
    qseries_path = HERE/'qseries_result.json'
    result_path = HERE/'eta_result.json'
    protocol = json.loads(protocol_path.read_text())
    qseries = json.loads(qseries_path.read_text())
    result = json.loads(result_path.read_text())
    assert result['protocol_sha256'] == sha(protocol_path)
    assert result['qseries_sha256'] == sha(qseries_path)
    rule = protocol['eta_screen']
    precision = rule['coefficient_match_precision']
    expected = brute_candidates(protocol['level'], rule['support_cap'],
                                rule['absolute_exponent_cap'])
    saved = {tuple(tuple(item) for item in row['factors']) for row in result['candidates']}
    assert saved == expected
    target = qseries['newform_coefficients'][:precision]
    for row in result['candidates']:
        factors = tuple(tuple(item) for item in row['factors'])
        series = binomial_eta_series(factors, precision)
        first_difference = next((n for n in range(precision) if series[n] != target[n]), precision)
        assert row['matching_coefficients_before_first_difference'] == first_difference
        assert row['first_different_degree'] == (None if first_difference == precision else first_difference)
        assert row['first_different_coefficient'] == (None if first_difference == precision else series[first_difference])
    assert len(expected) == result['candidate_count'] == 665
    assert not result['full_precision_matches']
    output = {'status': 'PASS_INDEPENDENT_ETA_SCREEN_REPLAY',
              'protocol_sha256': sha(protocol_path),
              'qseries_sha256': sha(qseries_path),
              'eta_result_sha256': sha(result_path),
              'candidate_count': len(expected),
              'full_precision_matches': 0,
              'best_prefix': result['best_prefix']}
    (HERE/'eta_validation.json').write_text(json.dumps(output, sort_keys=True, indent=2)+'\n')
    print(json.dumps(output, sort_keys=True))


if __name__ == '__main__':
    main()
