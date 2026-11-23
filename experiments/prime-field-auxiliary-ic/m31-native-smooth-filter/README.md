# Native smoothness filtering for the checked public M31 basis

For each canonical x the filter tests the signed representative min(x,p−x). It strips powers of every prime through 211 using compile-time divisors, accepting as soon as the remaining cofactor is at most 211. A positive cofactor in that range has only allowed prime factors. Zero is excluded. One FFI call compacts the input array in order. Input packing, allocation, output conversion, all auxiliary root generation and validation, and native ordinate lifts are included in each timed basis call.

Two local arm64 panels were timed independently. Ratios are medians of within-block ratios. The anchor uses the Python affine layer, reciprocal pass and sibling checks, followed by native lifting before trial division. The previous best path uses native layer, reciprocal and fiber routines with the Python exact divisor filter before lifting. The candidate changes only that filter in the incremental comparison.

|Comparison|Pairs|Median wall ms, reference / candidate|Paired wall gain|Median CPU ms, reference / candidate|Paired CPU gain|
|---|---:|---:|---:|---:|---:|
|Previous best vs native filter|32|14.10 / 5.54|2.348|12.77 / 5.46|2.316|
|Original anchor vs full native path|24|83.14 / 9.12|9.086|66.17 / 7.50|9.534|

The second panel directly compares complete pipelines. It does not compound ratios from different runs. All 112 timed results matched the independent ordered 195-point reference. The filter was also compared coordinate-by-coordinate with trial division on all archived roots, small integers, signed reflections, pseudorandom coordinates and values around powers of allowed and excluded primes.

Build filter.cpp with `c++ -std=c++17 -O3 -shared -fPIC filter.cpp -o /tmp/m31-filter.so`. Follow the adjacent m31-native-fiber README for the three other libraries. Run replay.py and combined.py with Python 3.13 and SymPy, supplying the four shared-library paths in the order lift, layer, fiber, filter. Both programs emit CSV. These benchmarks charge public basis preparation only.
