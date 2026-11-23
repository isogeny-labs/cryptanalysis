# Native reciprocal completion and sibling-fiber checks

The reference uses the previous native affine layer and the exact bounded-divisor filter. Each call generates and checks the entire ordered public depth-15 M31 fiber and returns the canonical 195 points. The reciprocal routine uses one inversion for the half-list. The validator folds a scratch copy to its terminal, checking every sibling product against the map coefficient and rejecting zero coefficients. Python-to-native packing, allocations and output conversion are timed.

|Native additions to the reference|Median wall ms|Median CPU ms|Paired wall ratio|Paired CPU ratio|
|---|---:|---:|---:|---:|
|Neither|39.66|25.46|1.000|1.000|
|Reciprocals|33.28|21.77|1.187|1.147|
|Fiber validation|27.94|17.66|1.575|1.432|
|Both|20.60|14.68|2.110|1.789|

Local arm64, 24 balanced four-arm blocks. Both kernels together won 20/24 wall comparisons and 24/24 CPU comparisons. Ratios use within-block times. The spread between CPU and wall measures warrants keeping the raw timings with the result.

Full chain output matched at depths 3, 8, 10, 12 and 15. The replay mutates three root positions, the root count, the terminal and a sibling coefficient at each depth; both implementations reject all 30 damaged fibers. Both also reject a zero input to reciprocal completion without modifying the caller's list. All 96 timed calls returned the independent scalar reference.

Build fiber.c with `cc -O3 -shared -fPIC fiber.c -o /tmp/m31-fiber.so`. Build the lift and layer libraries as in ../m31-native-layer/README.md, then run `uv run --isolated --with sympy --python 3.13 python replay.py /absolute/path/to/lift.so /absolute/path/to/layer.so /tmp/m31-fiber.so`.
