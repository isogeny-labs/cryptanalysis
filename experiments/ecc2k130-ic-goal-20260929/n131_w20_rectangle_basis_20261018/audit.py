"""Independent source-set replay of the coordinate-partition census."""
import hashlib
import json
from collections import Counter
from itertools import combinations
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SOURCE = ROOT / 'n131_w20_sevenpair_gate_20261010/support_w20.tsv'
SEED = 898618
PIVOT = SEED.bit_length() - 1


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compress(mask):
    low = mask & ((1 << PIVOT) - 1)
    high = mask >> (PIVOT + 1)
    return low | (high << PIVOT)


def histogram(codes, free_mask):
    count = Counter(code & ~free_mask for code in codes)
    return {str(k): sum(n == k for n in count.values()) for k in range(1, 1 + (1 << free_mask.bit_count()))}, len(count)


def main():
    protocol = json.loads((HERE / 'protocol.json').read_text())
    assert sha(SOURCE) == protocol['repo_sha256'][str(SOURCE.relative_to(ROOT))]
    columns = {}
    for line in SOURCE.read_text().splitlines():
        mask, column, _shift = map(int, line.split())
        assert mask not in columns
        columns[mask] = column
    codes = {
        compress(mask)
        for mask, col in columns.items()
        if mask < (mask ^ SEED)
        and (mask ^ SEED) in columns
        and col != columns[mask ^ SEED]
    }
    assert len(codes) == 132045
    rows = {}
    for line in (HERE / 'stdout.txt').read_text().splitlines():
        parts = line.split()
        if parts[0] == 'ROW':
            f, free_mask, nonempty, full = map(int, parts[1:5])
            hist = list(map(int, parts[5:]))
            assert len(hist) == (1 << f) + 1
            assert sum(hist) == 1 << (19 - f)
            assert sum(k * n for k, n in enumerate(hist)) == len(codes)
            assert nonempty == sum(hist[1:])
            assert full == hist[-1]
            rows[(f, free_mask)] = (nonempty, full, hist)
    assert len(rows) == 5016
    selected = {}
    # Exhaustively replay every two-bit partition with a distinct set-based
    # implementation, and replay both chosen wider partitions.
    masks = [(2, sum(1 << bit for bit in bits)) for bits in combinations(range(19), 2)]
    masks += [(3, 3080), (4, 67842)]
    for f, free_mask in masks:
        positive, nonempty = histogram(codes, free_mask)
        hist = [0] * ((1 << f) + 1)
        for k, n in positive.items():
            hist[int(k)] = n
        hist[0] = (1 << (19 - f)) - nonempty
        assert rows[(f, free_mask)] == (nonempty, hist[-1], hist)
        if free_mask in (3, 4098, 3080, 67842):
            selected[str(free_mask)] = {
                'free_bits': f, 'nonempty': nonempty, 'histogram': hist,
                'ordered_rectangles': nonempty * nonempty,
            }
    best = {}
    for f in (2, 3, 4):
        subset = [(mask, row) for (width, mask), row in rows.items() if width == f]
        mask, row = min(subset, key=lambda item: (item[1][0], -item[1][1], item[0]))
        best[str(f)] = {'mask': mask, 'nonempty': row[0], 'full': row[1],
                        'ordered_rectangles': row[0] ** 2}
    assert [best[str(f)]['mask'] for f in (2, 3, 4)] == [4098, 3080, 67842]
    result = {
        'status': 'INDEPENDENT_AUDIT_PASS', 'source_sha256': sha(SOURCE),
        'census_stdout_sha256': sha(HERE / 'stdout.txt'),
        'source_rows': len(columns), 'valid_codes': len(codes),
        'all_two_bit_partitions_replayed': len(list(combinations(range(19), 2))),
        'selected': selected, 'best': best,
        'pair_assignments': len(codes) ** 2,
    }
    (HERE / 'audit_result.json').write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
