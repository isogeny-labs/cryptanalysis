"""Independent NumPy Walsh replay and direct set audit of selected cosets."""
import hashlib
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SOURCE = ROOT / 'n131_w20_sevenpair_gate_20261010/support_w20.tsv'
SEED = 898618
PIVOT = SEED.bit_length() - 1
N = 1 << 19


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compress(mask):
    return (mask & ((1 << PIVOT) - 1)) | ((mask >> (PIVOT + 1)) << PIVOT)


def walsh(a):
    a = a.copy()
    width = 1
    while width < len(a):
        groups = a.reshape(-1, 2, width)
        left = groups[:, 0, :].copy()
        right = groups[:, 1, :].copy()
        groups[:, 0, :] = left + right
        groups[:, 1, :] = left - right
        width *= 2
    return a


def main():
    protocol = json.loads((HERE / 'affine_protocol.json').read_text())
    assert sha(SOURCE) == protocol['repo_sha256'][str(SOURCE.relative_to(ROOT))]
    columns = {}
    for line in SOURCE.read_text().splitlines():
        mask, col, _ = map(int, line.split())
        assert mask not in columns
        columns[mask] = col
    codes = {
        compress(m) for m, col in columns.items()
        if m < (m ^ SEED) and (m ^ SEED) in columns and col != columns[m ^ SEED]
    }
    assert len(codes) == 132045
    signal = np.zeros(N, dtype=np.int64)
    signal[list(codes)] = 1
    transform = walsh(signal)
    squared = transform * transform
    correlation_num = walsh(squared)
    assert np.all(correlation_num % N == 0)
    corr = correlation_num // N
    assert int(corr[0]) == len(codes)
    assert int(np.sum(corr)) == len(codes) ** 2
    order = sorted(range(1, N), key=lambda d: (-int(corr[d]), d))
    lines = (HERE / 'affine_stdout.txt').read_text().splitlines()
    top = [tuple(map(int, line.split()[1:])) for line in lines if line.startswith('TOP_LINE ')]
    assert len(top) == 64
    for rank, direction, overlap in top:
        assert direction == order[rank]
        assert overlap == int(corr[direction])
    best_line = [tuple(map(int, line.split()[1:])) for line in lines if line.startswith('BEST_LINE ')]
    best_plane = [tuple(map(int, line.split()[1:])) for line in lines if line.startswith('BEST_PLANE ')]
    assert best_line == [(order[0], int(corr[order[0]]), len(codes) - int(corr[order[0]]) // 2)]
    pairs, a, b, nonempty = best_plane[0]
    assert pairs == 2016
    line_cosets = {min(c, c ^ order[0]) for c in codes}
    plane_cosets = {min(c, c ^ a, c ^ b, c ^ a ^ b) for c in codes}
    assert len(line_cosets) == best_line[0][2]
    assert len(plane_cosets) == nonempty
    assert a in order[:64] and b in order[:64]
    code_array = np.fromiter(codes, dtype=np.int64)
    replay_best = None
    replay_pairs = 0
    for i, first in enumerate(order[:64]):
        for second in order[i + 1:64]:
            bases = np.minimum.reduce((code_array, code_array ^ first,
                                       code_array ^ second, code_array ^ first ^ second))
            size = len(np.unique(bases))
            candidate = (size, first, second)
            if replay_best is None or candidate < replay_best:
                replay_best = candidate
            replay_pairs += 1
    assert replay_pairs == pairs
    assert replay_best == (nonempty, a, b)
    result = {
        'status': 'INDEPENDENT_AFFINE_AUDIT_PASS',
        'source_sha256': sha(SOURCE),
        'affine_stdout_sha256': sha(HERE / 'affine_stdout.txt'),
        'full_direction_count': N - 1,
        'top_directions_replayed': 64,
        'selected_plane_pairs_replayed': replay_pairs,
        'best_line': {'direction': order[0], 'overlap': int(corr[order[0]]),
                      'nonempty_cosets': len(line_cosets)},
        'selected_plane': {'directions': [a, b], 'nonempty_cosets': len(plane_cosets),
                           'ordered_rectangles': len(plane_cosets) ** 2},
        'correlation_sum': int(np.sum(corr)),
    }
    (HERE / 'affine_audit_result.json').write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
