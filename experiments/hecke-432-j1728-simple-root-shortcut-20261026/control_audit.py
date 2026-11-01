"""Audit the one-simple-root rule against frozen nine-prime local records."""
import json
from collections import Counter
from hashlib import sha256
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def has_simple_linear(pattern):
    return any(int(degree) == 1 and int(exponent) == 1 for degree, exponent in pattern)


def main():
    protocol_path = HERE / 'protocol.json'
    protocol = json.loads(protocol_path.read_text())
    paths = {name: ROOT / rel for name, rel in protocol['input_paths'].items()}
    for name, path in paths.items():
        assert digest(path) == protocol['input_sha256'][name]
    galois = json.loads(paths['galois_result'].read_text())
    support = json.loads(paths['relative_discriminant_support'].read_text())
    assert galois['status'] == 'PASS_CUBIC_RESOLVENT_GALOIS_CLASSIFICATION'
    assert {r['side']: r['galois_group_over_L'] for r in galois['rows']} == \
        {'left': 'V4', 'right': 'V4'}
    assert support['fixed_integer_in_left_discriminant_ideal'] == 96
    screen = json.loads(paths['prior_local_screen'].read_text())
    resolution = json.loads(paths['prior_local_resolution'].read_text())
    assert {r['prime'] for r in screen['rows']} == {7, 11, 23, 31}
    prior = {r['prime']: r for r in resolution['rows']}
    rows = []
    for prime_row in screen['rows']:
        p = prime_row['prime']
        for i, place in enumerate(prime_row['places']):
            for side in ('left', 'right'):
                pattern = place[side]['reduced_factor_degrees_exponents']
                degrees = prior[p]['sides'][side]['places'][i]['relative_residue_degrees']
                simple = has_simple_linear(pattern)
                repeated = any(int(e) > 1 for _, e in pattern)
                rows.append({'prime': p, 'place_index': i, 'side': side,
                             'simple_linear': simple, 'repeated_reduction': repeated,
                             'observed_relative_degrees': degrees,
                             'status': 'MATCH' if not simple or degrees == [1, 1, 1, 1]
                             else 'MISMATCH'})
    right_obs = json.loads(paths['prior_right_observations'].read_text())
    right_resolution = json.loads(paths['prior_right_direct_comparison'].read_text())
    assert right_resolution['status'] == 'PASS_ALL_DIRECT_RIGHT_POLYNOMIAL_CHECKS'
    resolved = {(r['prime'], r['right_place_index']): r['observed_relative_degrees']
                for r in right_resolution['rows']}
    for row in right_obs['rows']:
        pattern = [(f['degree'], f['multiplicity']) for f in row['right_factors']]
        simple = has_simple_linear(pattern)
        repeated = any(int(e) > 1 for _, e in pattern)
        p, j = row['prime'], row['right_place_index']
        degrees = resolved[p, j]
        rows.append({'prime': p, 'place_index': j, 'side': 'right',
                     'simple_linear': simple, 'repeated_reduction': repeated,
                     'observed_relative_degrees': degrees,
                     'status': 'MATCH' if not simple or degrees == [1, 1, 1, 1]
                     else 'MISMATCH'})
    assert {r['prime'] for r in rows} == set(protocol['control_primes'])
    positive = [r for r in rows if r['simple_linear']]
    repeated_positive = [r for r in positive if r['repeated_reduction']]
    counts = Counter(r['status'] for r in positive)
    out = {'status': 'PASS_SIMPLE_ROOT_CONTROLS' if counts == {'MATCH': len(positive)}
           else 'FAIL_SIMPLE_ROOT_CONTROLS',
           'protocol_sha256': digest(protocol_path),
           'source_sha256': digest(Path(__file__)),
           'all_sites': len(rows), 'simple_root_sites': len(positive),
           'repeated_simple_root_sites': len(repeated_positive),
           'simple_root_status_counts': dict(counts),
           'repeated_simple_root_by_prime': dict(sorted(Counter(
               r['prime'] for r in repeated_positive).items())),
           'rows': rows}
    (HERE / 'control_result.json').write_text(json.dumps(out, sort_keys=True, indent=2) + '\n')
    print(json.dumps({k: out[k] for k in ('status', 'all_sites', 'simple_root_sites',
                                         'repeated_simple_root_sites',
                                         'repeated_simple_root_by_prime')}, sort_keys=True))


if __name__ == '__main__':
    main()
