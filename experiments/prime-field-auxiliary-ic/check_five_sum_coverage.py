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


def coverage(base):
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
    return counts, reached


def main():
    data = json.loads(FIXTURE.read_bytes())
    assert tuple(data["public"][key] for key in ("p", "a", "b")) == (P, 2, 14)
    balls = []
    for key in ("factor_base", "random_factor_base"):
        counts, ball = coverage(data[key])
        balls.append(ball)
        if counts != EXPECTED_SHELLS:
            raise ValueError(f"{key} shell counts differ: {counts}")
        print(key, counts, sum(counts))
        shifts = [tuple(data[key][0]), tuple(data["public"]["P"]), tuple(data["public"]["Q"])]
        overlaps = [sum(add(point, shift) in ball for point in ball) for shift in shifts]
        expected = [113290, 96 if key == "factor_base" else 264, 0]
        if overlaps != expected:
            raise ValueError(f"{key} shift overlaps differ: {overlaps}")
        print(key, "overlap after first basis point, P, Q", overlaps)
    common = len(balls[0] & balls[1])
    if common != 83:
        raise ValueError(f"cross-base intersection differs: {common}")
    print("cross-base intersection", common, "union", len(balls[0] | balls[1]))


if __name__ == "__main__":
    main()
