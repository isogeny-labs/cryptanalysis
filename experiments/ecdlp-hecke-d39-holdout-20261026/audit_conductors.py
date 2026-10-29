"""Checked-Sage audit of exact endomorphism conductors for saved points."""
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

from sage.all import EllipticCurve_from_j

HERE = Path(__file__).resolve().parent
SOURCE = HERE / 'data' / 'exp11_class_walk_D39_f6.json'
sys.path.insert(0, str(HERE / 'tools'))
import hecke11 as H  # noqa: E402


def main():
    data = json.loads(SOURCE.read_text())
    assert (data['DK'], data['f'], data['p'], data['u']) == (-39, 6, 367, 8)
    funcs, jfun = H.build([2, 3])
    reduced = H.Reduced(367, funcs, jfun, [2, 3])
    conductors = []
    j_values = []
    cache = {}
    pairs = defaultdict(list)
    for index, encoded in enumerate(data['column_points']):
        match = re.fullmatch(r'\((\d+) : (\d+) : 1\)', encoded)
        assert match, encoded
        point = reduced.E([int(match.group(1)), int(match.group(2)), 1])
        j = reduced.j(point)
        assert j is not None
        key = int(j)
        if key not in cache:
            cache[key] = int(EllipticCurve_from_j(j).endomorphism_order().conductor())
        j_values.append(key)
        conductors.append(cache[key])
        pairs[key].append(index)
    counts = Counter(conductors)
    assert dict(counts) == {1: 8, 2: 8, 3: 24, 6: 24}
    assert len(pairs) == 32 and all(len(indices) == 2 for indices in pairs.values())
    result = {'status': 'verified', 'source_sha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
              'point_counts_by_endomorphism_conductor': dict(sorted(counts.items())),
              'distinct_j': len(pairs), 'points_checked': 64,
              'column_conductors': conductors, 'column_j': j_values}
    (HERE / 'conductor_audit.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps({k: v for k, v in result.items() if not k.startswith('column_')}, sort_keys=True))


if __name__ == '__main__':
    main()
