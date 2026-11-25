"""Read archived public inputs and timings. No solver execution."""
import hashlib
import json
from pathlib import Path
import subprocess

ARCHIVE = "experiments/prime-field-auxiliary-ic/snapshot/algebraic/optimized"
FIXTURE = f"{ARCHIVE}/results/field31_s5_base0"
ARCHIVE_REV = "efb9330c1"
ROOT = Path(__file__).resolve().parent
P = 2**31 - 1
BOUND = 89
digests = {}


def read(path):
    raw = subprocess.check_output(["git", "show", f"{ARCHIVE_REV}:{path}"], cwd=ROOT)
    digests[path] = hashlib.sha256(raw).hexdigest()
    return raw


def smooth(x):
    assert 0 < x < P
    for divisor in range(2, BOUND + 1):
        while x % divisor == 0:
            x //= divisor
    return x == 1


def overlap(xs):
    return dict(size=len(xs), ordinary=[x for x in xs if smooth(x)],
                any_rotation=[x for x in xs if any(smooth((x << i) % P) for i in range(31))])


def main():
    read(f"{ARCHIVE}/benchmark.py")
    fixture = json.loads(read(f"{FIXTURE}/public.json"))
    roots = fixture["structured_roots"]
    assert len(set(roots)) == len(roots)
    assert (fixture["public"]["p"], fixture["public"]["a"], fixture["public"]["b"]) == (P, 2, 14)
    points = []
    for x in roots:
        rhs = (x**3 + 2*x + 14) % P
        y = pow(rhs, (P+1)//4, P)
        if y*y % P == rhs:
            points.append([x, min(y, P-y)])
    assert sorted(points) == fixture["factor_base"]
    rows = []
    for seed in range(3):
        row = json.loads(read(f"{FIXTURE}/v2_batch_seed{seed}.audited.json"))
        assert row["seed"] == seed and row["label"] == "v2_batch"
        basis, remaining = row["basis_seconds"], row["process_wall_seconds"]
        total = row["end_to_end_seconds"]
        assert basis == fixture["auxiliary_basis_seconds"] and basis+remaining == total
        rows.append(dict(seed=seed,total_s=total,basis_s=basis,
                         basis_percent=100*basis/total,
                         zero_basis_speedup_ceiling=total/remaining))
    print(json.dumps(dict(archive_revision=ARCHIVE_REV, roots=overlap(roots),
                          columns=overlap([x for x,y in points]), rows=rows,
                          sha256=digests),indent=2))


if __name__ == "__main__":
    main()
