"""Pair base primes under s -> -s and replay conjugate quartic splitting."""
import json
from hashlib import sha256
from pathlib import Path

from sage.all import NumberField, PolynomialRing, QQ

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def main():
    protocol_path = HERE / 'protocol.json'
    protocol = json.loads(protocol_path.read_text())
    paths = {name: ROOT / rel for name, rel in protocol['input_paths'].items()}
    for name, path in paths.items():
        assert sha256(path.read_bytes()).hexdigest() == protocol['input_sha256'][name]
    cert = json.loads(paths['factor_certificate'].read_text())
    obs = json.loads(paths['holdout_observations'].read_text())
    assert obs['status'] == 'PASS_QUARTIC_OBSERVATION'
    K = NumberField(PolynomialRing(QQ, 'x')(
        [QQ(v) for v in cert['field_polynomial_coefficients_low_to_high']]), 'alpha')
    L = K.extension(PolynomialRing(K, 't').gen() ** 2 - 2, 's')
    sigma = L.hom([-L.gen()], L)
    assert sigma(L.gen()) == -L.gen()
    assert sigma(L(K.gen())) == L(K.gen())
    by_key = {(row['prime'], row['base_place_index'], row['side']): row
              for row in obs['rows']}
    assert len(by_key) == len(obs['rows'])
    rows = []
    for p in protocol['primes']:
        places = L.primes_above(p)
        permutation = []
        for i, P in enumerate(places):
            image = L.ideal([sigma(v) for v in P.gens()])
            hits = [j for j, Q in enumerate(places) if image == Q]
            assert len(hits) == 1
            j = hits[0]
            assert int(P.residue_class_degree()) == int(places[j].residue_class_degree())
            assert L.ideal([sigma(v) for v in image.gens()]) == P
            left = by_key[p, i, 'left']
            right = by_key[p, j, 'right']
            assert left['status'] == right['status'] == 'SQUAREFREE'
            assert left['observed_relative_degrees'] == right['observed_relative_degrees']
            permutation.append(j)
            rows.append({'prime': p, 'left_base_place_index': i,
                         'right_base_place_index': j,
                         'base_residue_degree': int(P.residue_class_degree()),
                         'left_relative_degrees': left['observed_relative_degrees'],
                         'right_relative_degrees': right['observed_relative_degrees'],
                         'status': 'MATCH_CONJUGATE_PLACES'})
        assert sorted(permutation) == list(range(len(places)))
        assert all(permutation[permutation[i]] == i for i in range(len(places)))
        print(json.dumps({'prime': p, 'base_places': len(places),
                          'fixed_places': sum(i == j for i, j in enumerate(permutation))},
                         sort_keys=True), flush=True)
    out = {'status': 'PASS_CONJUGATE_PRIME_PAIRING',
           'protocol_sha256': sha256(protocol_path.read_bytes()).hexdigest(),
           'source_sha256': sha256(Path(__file__).read_bytes()).hexdigest(),
           'paired_base_places': len(rows), 'rows': rows}
    (HERE / 'prime_pairing_result.json').write_text(json.dumps(out, sort_keys=True, indent=2) + '\n')
    print(json.dumps({'status': out['status'], 'paired_base_places': len(rows)},
                     sort_keys=True), flush=True)


if __name__ == '__main__':
    main()
