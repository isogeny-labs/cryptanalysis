"""Describe column incidence in archived three-point M31 comparison records."""
from collections import Counter, defaultdict
import json
from pathlib import Path
import subprocess

BASE = "experiments/prime-field-auxiliary-ic/snapshot/comparison/field31"
ROOT = Path(__file__).resolve().parents[3]


def read_supports(arm, seed):
    path = f"{BASE}/{arm}/seed{seed}/relations.jsonl"
    data = subprocess.check_output(["git", "show", f"HEAD:{path}"], cwd=ROOT)
    rows = []
    for line in data.splitlines():
        codes = json.loads(line)["codes"]
        assert len(codes) == 3 and all(0 <= code < 1000 for code in codes)
        counts = Counter()
        for code in codes:
            counts[code // 2] += 1 if code % 2 == 0 else -1
        rows.append({column for column, value in counts.items() if value})
    return rows


def components(rows):
    incident = defaultdict(list)
    for index, row in enumerate(rows):
        for column in row:
            incident[column].append(index)
    remaining = set(range(len(rows)))
    sizes = []
    while remaining:
        pending = [remaining.pop()]
        columns = set()
        count = 0
        while pending:
            index = pending.pop()
            count += 1
            for column in rows[index] - columns:
                columns.add(column)
                for neighbor in incident[column]:
                    if neighbor in remaining:
                        remaining.remove(neighbor)
                        pending.append(neighbor)
        sizes.append((count, len(columns)))
    return sorted(sizes, reverse=True)


def core(rows):
    while True:
        degree = Counter(column for row in rows for column in row)
        kept = [row for row in rows if all(degree[column] > 1 for column in row)]
        if len(kept) == len(rows):
            return rows
        rows = kept


if __name__ == "__main__":
    for arm in ("auxiliary", "plain"):
        for seed in range(3):
            rows = read_supports(arm, seed)
            print(arm, seed, components(rows), components(core(rows)))
