"""Checked-Sage comparison of distinct-root and repeated-root Hecke kernels."""
import argparse
import hashlib
import importlib.util
import json
import re
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent / 'ecdlp-hecke-d39-holdout-20261026'
SOURCE = BASE / 'data' / 'exp11_class_walk_D39_f6.json'
OLD = BASE / 'tools' / 'hecke11.py'
NEW = HERE / 'hecke11_repeated.py'
EXPECTED = {
    SOURCE: '4bcc8eb1905a9ed79a47cc31820e722dc7a6ff87f18bb37aeebafa35e6cc6df9',
    OLD: '7e66144e76bf62f7e645d87cc58be2bb0f7cc5e52601665650ef0706a6f715fb',
    NEW: '2924c486d920cfcfffc5a8864d4134efd883716d77d90bf2957346bb88d04d7b',
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


def rank(rows, modulus, columns):
    pivots = {}
    for row in rows:
        current = {int(k): int(v) % modulus for k, v in row.items() if int(v) % modulus}
        while current:
            pivot = min(current)
            if pivot not in pivots:
                inverse = pow(current[pivot], -1, modulus)
                pivots[pivot] = {k: v * inverse % modulus for k, v in current.items()}
                break
            multiplier = current[pivot]
            for k, v in pivots[pivot].items():
                value = (current.get(k, 0) - multiplier*v) % modulus
                if value:
                    current[k] = value
                else:
                    current.pop(k, None)
    return len(pivots)


def main(output_path):
    for path, expected in EXPECTED.items():
        assert digest(path) == expected, path
    data = json.loads(SOURCE.read_text())
    assert (data['DK'], data['f'], data['p'], data['hecke_primes']) == (-39, 6, 367, [2, 3])
    old = module(OLD, 'original_hecke11')
    new = module(NEW, 'repeated_hecke11')
    funcs, jfun = old.build([2, 3])
    a, b = old.Reduced(367, funcs, jfun, [2, 3]), new.Reduced(367, funcs, jfun, [2, 3])
    points = []
    for encoded in data['column_points']:
        match = re.fullmatch(r'\((\d+) : (\d+) : 1\)', encoded)
        assert match, encoded
        points.append(a.E([int(match.group(1)), int(match.group(2)), 1]))
    assert len(points) == len(set(points)) == 64
    index = {point: i for i, point in enumerate(points)}
    patterns = {2: Counter(), 3: Counter()}
    added = []
    for i, point in enumerate(points):
        for degree in (2, 3):
            roots = a.neighbour_x(degree, point).roots()
            patterns[degree][','.join(str(multiplicity) for _, multiplicity in sorted(roots, key=lambda item: item[1]))] += 1
        before = a.neighbours_all(2, point)
        after = b.neighbours_all(2, point)
        canonical = lambda neighbors: None if neighbors is None else sorted(str(Q) for Q in neighbors)
        if canonical(before) == canonical(after):
            continue
        assert before is None and after is not None, i
        assert all(Q in index for Q in after), i
        assert sum(after, a.E(0)) == a.a_l[2] * point, i
        moments = [a.funcs[(2, 'xy', k)](point[0], point[1]) for k in range(3)]
        assert all(sum(Q[1] * Q[0] ** k for Q in after) == moments[k] for k in range(3)), i
        row = Counter(index[Q] for Q in after)
        row[i] -= a.a_l[2]
        added.append({'source_column': i, 'neighbours': [index[Q] for Q in after],
                      'row': {str(k): int(v) for k, v in row.items() if v}})
    ranks = {}
    augmented = data['relation_rows'] + [item['row'] for item in added]
    for modulus in (23, 1009, 1000000007):
        ranks[str(modulus)] = {'original': rank(data['relation_rows'], modulus, 64),
                               'augmented': rank(augmented, modulus, 64)}
        assert ranks[str(modulus)]['original'] == 40
    output = {'status': 'verified', 'source_sha256': digest(SOURCE),
              'old_kernel_sha256': digest(OLD), 'new_kernel_sha256': digest(NEW),
              'points_scanned': len(points), 'root_patterns': {str(k): dict(v) for k, v in patterns.items()},
              'added': added, 'ranks': ranks}
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, indent=2, sort_keys=True) + '\n')
    print(json.dumps({k: v for k, v in output.items() if k != 'added'}, sort_keys=True))
    print(json.dumps({'added_count': len(added), 'sources': [item['source_column'] for item in added]}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True,
                        help='write the receipt to a unique attempt directory')
    main(parser.parse_args().output)
