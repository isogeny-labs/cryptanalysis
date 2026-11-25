"""Check singleton-column certificates for the archived M31 smooth-coordinate subsets."""
import json
import subprocess
from collections import Counter, defaultdict, deque

ARCHIVE = (
    "4551d77ae4a87fdee717e69b8f90c46420f6cc35:"
    "experiments/prime-field-auxiliary-ic/snapshot/comparison/field31/auxiliary/"
)


def read(name):
    return subprocess.check_output(["git", "show", ARCHIVE + name])


def largest_factor(x):
    divisor, largest = 2, 1
    while divisor * divisor <= x:
        while x % divisor == 0:
            largest = divisor
            x //= divisor
        divisor = 3 if divisor == 2 else divisor + 2
    return max(largest, x)


def peel(rows):
    incident = defaultdict(set)
    for i, row in enumerate(rows):
        for col in row:
            incident[col].add(i)
    queue = deque(c for c in incident if len(incident[c]) == 1)
    certificate = []
    while queue:
        col = queue.popleft()
        if len(incident[col]) != 1:
            continue
        i, = incident[col]
        certificate.append((i, col))
        for c in rows[i]:
            incident[c].remove(i)
            if len(incident[c]) == 1:
                queue.append(c)
    return certificate


def main():
    public = json.loads(read("public.json"))
    labels = [largest_factor(x) for x, _ in public["factor_base_representatives"]]
    for seed in range(3):
        prefix = f"seed{seed}/"
        assert json.loads(read(prefix + "public.json")) == public
        records = [json.loads(line) for line in read(prefix + "relations.jsonl").splitlines()]
        assert len(records) == json.loads(read(prefix + "metrics.json"))["relations"]
        for bound in (256, 1024, 4096):
            rows = []
            for record in records:
                codes = record["codes"]
                assert len(codes) == 3 and all(0 <= c < 2 * len(labels) for c in codes)
                if all(labels[c // 2] > bound for c in codes):
                    continue
                coeff = Counter()
                for code in codes:
                    coeff[code // 2] += 1 if code % 2 == 0 else -1
                rows.append({c for c, v in coeff.items() if v % public["n"]})
            # Replay the proposed pivots directly against all remaining row supports.
            live = set(range(len(rows)))
            for i, c in peel(rows):
                assert [j for j in live if c in rows[j]] == [i]
                live.remove(i)
            assert not live
            print(seed, bound, len(rows))


if __name__ == "__main__":
    main()
