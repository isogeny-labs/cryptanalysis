# Cold public preparation of the signed 211-smooth M31 basis

A signed representative u=min(x,p−x) lies between 1 and 2³⁰−1 on this basis. For each prime q≤211 take the largest power of q up to that limit. The product M of these powers has 1,285 bits. Unique factorization gives u | M precisely for the 211-smooth representatives. The Python path tests M % u == 0 and constructs M anew for each basis. Divisor.lean proves the divisibility equivalence under the exponent bounds.

The archive has 32,768 roots, 392 signed-smooth representatives and 195 smooth target-liftable coordinates. All four arms produced the same ordered 195 points as independent scalar square-root verification. The divisor test also agreed with trial division on every root. Each timed call reconstructs and validates all auxiliary roots. It includes native ordinate calls, packing, filtering and output construction. It excludes interpreter and library startup, benchmark validation and the shared small prime list. Cold refers to rebuilding basis state on each call.

Local arm64, 24 paired blocks, balanced order. Ratios are medians of the within-block reference time divided by the candidate time.

|Order and predicate|Median wall ms|Median CPU ms|Paired wall ratio|Paired CPU ratio|
|---|---:|---:|---:|---:|
|Lift first, trial divide|90.56|72.92|1.000|1.000|
|Filter first, trial divide|124.77|99.64|0.747|0.745|
|Lift first, divisor test|53.64|44.87|1.746|1.714|
|Filter first, divisor test|48.12|41.52|1.886|1.834|

The filter-first divisor path beat the reference in 24 of 24 blocks on both clocks. Moving trial division before the lift approximately doubles its input count. Using the cheaper divisor test makes early filtering practical and reduces native lift batches from 1,024 to 13. These rates concern only this local public setup.

Build the native library from ../m31-native-product/archived-lifts as in its README, and run `uv run --isolated --with sympy --python 3.13 python bench.py /absolute/path/to/neon.so`. The runner loads the frozen chain source from Git. Replay Divisor.lean with mathlib on Lean 4.34.1.
