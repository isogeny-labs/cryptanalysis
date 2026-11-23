"""Check structural and numerical rank of six fixed public row archives."""
from collections import Counter, defaultdict
from fractions import Fraction
import csv
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
REV = "efb9330c1ee7e30743b7674f686cccb49f1cb25e"
BASE = "experiments/prime-field-auxiliary-ic/snapshot/comparison/field31"
ORDER = 2147505293


def archive(path):
    return subprocess.check_output(["git", "show", f"{REV}:{BASE}/{path}"], cwd=HERE, text=True)


def coefficients(row):
    entries = Counter()
    for code in row["codes"]:
        assert 0 <= code < 1000
        entries[code // 2] += 1 if code % 2 == 0 else -1
    return {c: v for c, v in entries.items() if v}


def pivot_counts(rows, rational=False):
    reduce_entry = Fraction if rational else lambda x: x % ORDER
    inverse = (lambda x: 1 / x) if rational else lambda x: pow(x, -1, ORDER)
    pivots = {}
    for row in rows:
        vector = row.copy()
        while vector:
            c = min(vector)
            scale = reduce_entry(vector[c])
            if c not in pivots:
                inv = inverse(scale)
                pivots[c] = {j: reduce_entry(v * inv) for j, v in vector.items()}
                break
            for j, v in pivots[c].items():
                entry = reduce_entry(vector.get(j, 0) - scale * v)
                if entry:
                    vector[j] = entry
                else:
                    vector.pop(j, None)
        yield len(pivots)


def structural_rank(rows):
    owner = {}
    witness = set()

    def augment(r, reached):
        for c in rows[r]:
            if c in reached:
                continue
            reached.add(c)
            if c not in owner or augment(owner[c], reached):
                owner[c] = r
                return True
        return False

    for r in range(len(rows)):
        reached = set()
        if not augment(r, reached):
            assert r == len(rows) - 1
            witness = {r} | {owner[c] for c in reached}
            neighbors = {c for i in witness for c in rows[i]}
            assert neighbors == reached and len(witness) == len(neighbors) + 1

    assert len(set(owner.values())) == len(owner)
    assert all(c in rows[r] for c, r in owner.items())
    assert len(owner) == len(rows) - bool(witness)
    return len(owner), len(witness)


def audit(method, seed):
    folder = f"{method}/seed{seed}"
    public = json.loads(archive(f"{folder}/public.json"))
    assert public["n"] == ORDER and len(public["factor_base_representatives"]) == 500
    rows = [coefficients(json.loads(s)) for s in archive(f"{folder}/relations.jsonl").splitlines()]
    certificate = json.loads(archive(f"{folder}/certificate.json"))
    n = len(rows)
    assert n == certificate["relations"] and len(certificate["weights"]) == n
    ranks = list(pivot_counts(rows))
    assert ranks[:-1] == list(range(1, n)) and ranks[-1] == certificate["rank"] == n - 1
    rational_ranks = list(pivot_counts(rows, rational=True))
    assert rational_ranks == ranks
    support = [i for i, w in enumerate(certificate["weights"]) if w % ORDER]
    assert n - 1 in support
    totals = defaultdict(int)
    for i in support:
        for c, v in rows[i].items():
            totals[c] += v * certificate["weights"][i]
    assert all(x % ORDER == 0 for x in totals.values())
    matching, witness_size = structural_rank(rows)
    return (seed, method, n, ranks[-1], rational_ranks[-1], matching, witness_size or "",
            witness_size - 1 if witness_size else "", len(support), len(totals))


if __name__ == "__main__":
    writer = csv.writer(sys.stdout, lineterminator="\n")
    writer.writerow(["seed", "method", "rows", "field_rank", "rational_rank", "matching", "witness_rows",
                     "witness_columns", "dependency_rows", "dependency_columns"])
    for seed in range(3):
        for method in ("auxiliary", "plain"):
            writer.writerow(audit(method, seed))
