"""GF(2) unfolding ranks of the indicator of the frozen 195 coordinates."""
from pathlib import Path


def compressed_rows(points, mask):
    # Unoccupied rows and columns are zero; their deletion preserves rank.
    columns = {}
    rows = {}
    for x in points:
        col = columns.setdefault(x & ~mask, len(columns))
        row = x & mask
        rows[row] = rows.get(row, 0) | (1 << col)
    return rows.values()


def rank(rows):
    pivots = {}
    for row in rows:
        while row:
            pivot = row.bit_length() - 1
            if pivot not in pivots:
                pivots[pivot] = row
                break
            row ^= pivots[pivot]
    return len(pivots)


def unfoldings(points, order):
    assert sorted(order) == list(range(31))
    mask = 0
    result = []
    for bit in order[:-1]:
        mask |= 1 << bit
        r = rank(compressed_rows(points, mask))
        assert r == rank(compressed_rows(points, ((1 << 31) - 1) ^ mask))
        result.append(r)
    return result


if __name__ == "__main__":
    points = list(map(int, Path(__file__).with_name("coordinates.txt").read_text().splitlines()))
    assert len(set(points)) == len(points) == 195
    selected = [j for j in range(31) if 0x1520944e & (1 << j)]
    for name, order in (
        ("low-to-high", list(range(31))),
        ("even-then-odd", list(range(0, 31, 2)) + list(range(1, 31, 2))),
        ("projection-first", selected + [j for j in range(31) if j not in selected]),
    ):
        profile = unfoldings(points, order)
        print(name, "ranks at cuts 1..30:", *profile)
