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


def qualifying_traces(degree):
    """Exact modular trace list for a positive extension degree."""
    if degree < 1:
        raise ValueError("extension degree must be positive")
    if degree < 661993:
        return [-21645] if degree % 2 else [-21645, 21645]
    return admitted_traces(degree)


if __name__ == "__main__":
    for degree in (1, 2, 3244, 660001, 661992, 661993):
        traces = admitted_traces(degree)
        assert traces == qualifying_traces(degree)
        if degree in (1, 660001):
            assert traces == [-21645]
        elif degree in (2, 3244, 661992):
            assert traces == [-21645, 21645]
        else:
            assert len(traces) == 72 and -74434 in traces
        print(degree, len(traces), traces if len(traces) < 3 else min(traces))

    # Walk consecutive extension degrees for each surviving trace. This uses
    # the second-order recurrence directly, independently of binary doubling.
    for trace in (-21645, 21645):
        previous, current, power = 2, trace, P
        for degree in range(1, 661993):
            passes = (1 + power - current) % R == 0
            assert passes == (trace in qualifying_traces(degree)), (trace, degree)
            previous, current = current, (trace * current - P * previous) % R
            power = power * P % R
    print("Both surviving traces agree through degree 661992.")

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

        from timeit import repeat

        for name, call in (("two recurrences", lambda: admitted_traces(3244, (-21645, 21645))),
                           ("parity rule", lambda: qualifying_traces(3244))):
            times = repeat(call, number=10000, repeat=7)
            print(name, "median ns per lookup", round(median(times) * 1e5, 1))
