"""Count distinct points within five signed summands for each archived M31 base."""
import json
from pathlib import Path

P = 2147483647
FIXTURE = Path(__file__).resolve().parent / (
    "snapshot/algebraic/optimized/results/field31_s5_base0/public.json"
)
# Consecutive differences of SignedBall.bound 17 k.
EXPECTED_SHELLS = [1, 34, 578, 6562, 56066, 385186]


def add(left, right):
    """Affine addition on y² = x³ + 2x + 14. None represents infinity."""
    if left is None:
        return right
    if right is None:
        return left
    x, y = left
    z, w = right
    if x == z and (y + w) % P == 0:
        return None
    numerator, denominator = (3*x*x + 2, 2*y) if x == z else (w-y, z-x)
    slope = numerator * pow(denominator, -1, P) % P
    t = (slope*slope - x - z) % P
    return t, (slope*(x-t) - y) % P


def count_shells(base):
    generators = [tuple(point) for point in base]
    assert len(set(generators)) == 17
    assert all((y*y - x**3 - 2*x - 14) % P == 0 for x, y in generators)
    signed = generators + [(x, -y % P) for x, y in generators]
    reached = {None}
    frontier = {None}
    counts = [1]
    for _ in range(5):
        frontier = {add(q, step) for q in frontier for step in signed} - reached
        reached.update(frontier)
        counts.append(len(frontier))
    return counts


def main():
    data = json.loads(FIXTURE.read_bytes())
    assert tuple(data["public"][key] for key in ("p", "a", "b")) == (P, 2, 14)
    for key in ("factor_base", "random_factor_base"):
        counts = count_shells(data[key])
        if counts != EXPECTED_SHELLS:
            raise ValueError(f"{key} shell counts differ: {counts}")
        print(key, counts, sum(counts))


if __name__ == "__main__":
    main()
