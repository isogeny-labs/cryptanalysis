"""Replay the archived public certificate audit with per-certificate fixed-base tables."""
import argparse
from pathlib import Path
from statistics import median
import sys
from time import perf_counter
from unittest.mock import patch


def window_curve(base_curve):
    class WindowCurve(base_curve):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.tables = {}

        def mul(self, k, point):
            assert k >= 0
            tables = self.tables.setdefault(point, [])
            result = None
            position = 0
            while k:
                if position == len(tables):
                    unit = point if not tables else self.add(tables[-1][16], tables[-1][16])
                    digits = [None, unit]
                    for _ in range(2, 32):
                        digits.append(self.add(digits[-1], unit))
                    tables.append(digits)
                digit = k & 31
                if digit:
                    result = self.add(result, tables[position][digit])
                k >>= 5
                position += 1
            return result

    return WindowCurve


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, default=Path(__file__).resolve().parents[1]/"snapshot")
    parser.add_argument("--repetitions", type=int, default=1)
    parser.add_argument("--compare", action="store_true")
    args = parser.parse_args()
    if not __debug__:
        parser.error("the archived verifier requires assertions enabled")
    if args.repetitions < 1:
        parser.error("repetitions must be positive")
    root = args.snapshot.resolve() / "comparison"
    sys.path.insert(0, str(root))
    import benchmark

    candidate = window_curve(benchmark.Curve)
    for method in ("auxiliary", "plain"):
        for seed in range(3):
            folder = root / "field31" / method / f"seed{seed}"
            samples = {"window": [], "original": []}
            for rep in range(args.repetitions):
                order = ["window", "original"] if args.compare else ["window"]
                for name in (order if rep % 2 else reversed(order)):
                    curve = candidate if name == "window" else benchmark.Curve
                    with patch.object(benchmark, "Curve", curve):
                        start = perf_counter()
                        benchmark.audit(folder, method)
                        samples[name].append(perf_counter() - start)
            print(method, seed, {name: round(median(times)*1000, 3)
                                  for name, times in samples.items() if times}, flush=True)


if __name__ == "__main__":
    main()
