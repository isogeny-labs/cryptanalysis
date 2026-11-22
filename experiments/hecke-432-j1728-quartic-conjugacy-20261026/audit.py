"""Cross-check exact conjugacy, prime involution, and frozen observations."""
import json
from collections import Counter
from hashlib import sha256
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def main():
    protocol_path = HERE / 'protocol.json'
    protocol = json.loads(protocol_path.read_text())
    for name, relative in protocol['input_paths'].items():
        assert digest(ROOT / relative) == protocol['input_sha256'][name]
    exact = json.loads((HERE / 'conjugacy_result.json').read_text())
    pairing = json.loads((HERE / 'prime_pairing_result.json').read_text())
    obs = json.loads((ROOT / protocol['input_paths']['holdout_observations']).read_text())
    assert exact['status'] == 'PASS_EXACT_SQRT2_CONJUGACY'
    assert pairing['status'] == 'PASS_CONJUGATE_PRIME_PAIRING'
    assert exact['protocol_sha256'] == pairing['protocol_sha256'] == digest(protocol_path)
    assert all(exact['quartic_conjugate_equalities'])
    assert all(exact['radicand_conjugate_equalities'])
    indexed = {(r['prime'], r['base_place_index'], r['side']): r for r in obs['rows']}
    assert len(indexed) == len(obs['rows'])
    rows = pairing['rows']
    assert len(rows) == pairing['paired_base_places'] == len(obs['rows']) // 2
    permutations = {}
    for r in rows:
        p, i, j = r['prime'], r['left_base_place_index'], r['right_base_place_index']
        permutations.setdefault(p, {})[i] = j
        left, right = indexed[p, i, 'left'], indexed[p, j, 'right']
        assert left['status'] == right['status'] == 'SQUAREFREE'
        assert left['observed_relative_degrees'] == right['observed_relative_degrees']
        assert r['left_relative_degrees'] == left['observed_relative_degrees']
        assert r['right_relative_degrees'] == right['observed_relative_degrees']
    for p in protocol['primes']:
        permutation = permutations[p]
        assert sorted(permutation) == list(range(len(permutation)))
        assert all(permutation[permutation[i]] == i for i in permutation)
    counts = Counter((r['prime'], tuple(r['left_relative_degrees'])) for r in rows)
    out = {'status': 'PASS_CONJUGACY_AND_PRIME_PAIR_AUDIT',
           'protocol_sha256': digest(protocol_path),
           'exact_result_sha256': digest(HERE / 'conjugacy_result.json'),
           'pairing_result_sha256': digest(HERE / 'prime_pairing_result.json'),
           'source_sha256': digest(Path(__file__)),
           'paired_base_places': len(rows),
           'fixed_base_places': sum(i == j for perm in permutations.values()
                                    for i, j in perm.items()),
           'pattern_counts': [{'prime': p, 'relative_degrees': list(pattern), 'places': n}
                              for (p, pattern), n in sorted(counts.items())]}
    (HERE / 'audit_result.json').write_text(json.dumps(out, sort_keys=True, indent=2) + '\n')
    print(json.dumps(out, sort_keys=True))


if __name__ == '__main__':
    main()
