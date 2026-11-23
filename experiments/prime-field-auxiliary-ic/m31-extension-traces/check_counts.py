"""Independent modular point-count check using Lucas trace doubling."""
from math import isqrt

P = 2**31 - 1
R = 2147505293


def admitted_traces(degree, candidates=None):
    # S_n = x^n + y^n, xy = P. Track S_n and S_(n+1).
    q = 1
    steps = []
    for bit in bin(degree)[2:]:
        steps.append((bit == "1", q))
        q = q * q * (P if bit == "1" else 1) % R
    limit = isqrt(4 * P)
    result = []
    if candidates is None:
        candidates = range(-limit, limit + 1)
    for t in candidates:
        a, b = 2, t
        for odd, power in steps:
            middle = (a * b - t * power) % R
            if odd:
                a, b = middle, (b * b - 2 * P * power) % R
            else:
                a, b = (a * a - 2 * power) % R, middle
        if (1 + q - a) % R == 0:
            result.append(t)
    return result


if __name__ == "__main__":
    for degree in (1, 2, 3244, 661993):
        traces = admitted_traces(degree)
        if degree == 1:
            assert traces == [-21645]
        elif degree in (2, 3244):
            assert traces == [-21645, 21645]
        else:
            assert len(traces) == 72 and -74434 in traces
        print(degree, len(traces), traces if len(traces) < 3 else min(traces))

    import sys
    if "--bench" in sys.argv:
        from statistics import median
        from time import perf_counter_ns

        for candidates, repetitions in ((None, 3), ((-21645, 21645), 1001)):
            samples = []
            for _ in range(repetitions):
                start = perf_counter_ns()
                traces = admitted_traces(3244, candidates)
                samples.append(perf_counter_ns() - start)
                assert traces == [-21645, 21645]
            print(repetitions, "samples, median ns", median(samples))
