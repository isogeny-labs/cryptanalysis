# Further native optimizations and Pollard rho comparison

The target is the same original full prime-order curve over F_(2^31−1),
`y²=x³+2x+14`, with order 2147505293 and the same public P and Q.
All timings below are complete recoveries of the same test logarithm.

Median full wall time across the same three fixed search seeds:

| Solver | Complete recovery |
|---|---:|
| Preserved v1 IC, fresh control | 35.416334 s |
| Centered fused IC, same search | 15.083680 s |
| Centered fused IC, batched targets | 9.685108 s |
| Pollard rho, shared arithmetic | 0.018318 s |

**Rho is about 529× faster than the fastest IC variant on this instance.**
The fused same-search change is 1.79× faster by the median of paired run
ratios. Batching further improves the query rate and changes the successful
query count, so its full-time comparison also includes sampling variation.

| Seed | v1 IC (s) | Fused IC (s) | Batched IC (s) | Rho (ms) |
|---:|---:|---:|---:|---:|
| 0 | 23.530 | 14.419 | 9.685 | 7.092 |
| 1 | 40.001 | 22.293 | 5.167 | 21.868 |
| 2 | 35.416 | 15.084 | 11.668 | 18.318 |

| Seed | Common v1/fused IC queries | Batched IC queries | Rho walk steps |
|---:|---:|---:|---:|
| 0 | 36,262,094 | 34,771,537 | 26,343 |
| 1 | 60,080,847 | 19,300,166 | 119,375 |
| 2 | 41,844,181 | 45,496,514 | 111,072 |

These are fresh measurements; the earlier 27.6-second v1 median remains in
the previous report. Per-seed timings above expose run-to-run variation.
Native internal medians are recorded alongside full process wall times; rho
takes 15.877 ms internally, versus its 18.318 ms full wall median here.

Raw timings, CPU times, peak memory, and certificates are in
[results/field31_s5_base0/summary.json](results/field31_s5_base0/summary.json).

The preserved v1 and fused v2 use exactly the same search sequence for each
seed, producing identical relation files and dependency weights. Batched v2
uses 64 public-point walks, so its successful query count can differ. The
sampler is independent of target membership. Every index-calculus variant
rejects duplicate and sign-reversed rows, and recovers through a dependency
involving at least three distinct rows. Individual base points are stored;
the solver constructs no point-pair table.

Methods run serially, with order rotated over the three fixed search seeds.
All four variants use the same compiler flags: `-O3 -march=native -std=c++17`.
Full wall times include process launch, public-input loading, setup, search,
and public-key verification. Each IC run is also charged the measured base
construction time. Compilation and independent certificate auditing occur
outside the timed attack. CPU and native internal timings are also recorded.
The public curve parameters and group order are supplied equally to all methods.
Hardware and build details are recorded in [environment.json](environment.json).

## Changes

* The auxiliary quadratic is kept centered at the next isogeny kernel. Replacing
  the image offset A by `A-r_next` eliminates repeated coordinate translations.
  The final step folds in the terminal coordinate directly.
* Three groups of eight coordinates stay in AVX-512 registers through the full
  circuit. This exposes independent instruction streams and avoids writing and
  rereading the three polynomial coefficients at every stage. AVX2 and scalar
  fallbacks implement the same exact formula.
* Fixed addition chains compute inverses in the Mersenne fields. At 31 bits,
  inversion uses 30 squarings and eight other multiplications.
* Sixty-four independent target walks share one field inversion through a
  prefix-product batch. Infinity, doubling, and opposite-point additions take
  explicit exceptional paths. Up to 63 generated targets can be unused when
  recovery ends; both processed and generated counts are recorded.
* Small polynomial dot-product tails accumulate unreduced products before
  reducing. Four 31-bit products fit in 64 bits. The ordinary polynomial
  backend receives this arithmetic optimization as well.

The explicit-polynomial query microbenchmark improves from 1.873 µs to
1.646 µs (1.14× throughput), with method order alternated across three rounds.
See [explicit_profile.json](explicit_profile.json).

On the original 32768-root workload, median direct extraction falls from
**1.250 ms to 0.406 ms**, a further **3.08×** speedup.
All 261,472 scalar resultant values agree exactly between versions across
the 16 unchanged benchmark targets, as do all returned point decompositions.
See [circuit_results.json](circuit_results.json).

The earlier generic GCD remainder-tree and liftability optimizations remain
available. This version accelerates the direct circuit path, which already
avoids constructing the large resultant or computing its GCD.

## Rho baseline and audit

[rho.cpp](rho.cpp) implements a 32-adding Pollard walk with Brent cycle
detection, constant walk storage, and restart handling for degenerate
collisions. It includes the same [native_v2.cpp](native_v2.cpp) field and point
arithmetic as optimized IC, including the faster inverse. It reads only p,
group order, curve coefficients, P, and Q; its public input has no factor base.

For every rho recovery, the independent Python audit checks both collision
points `a₁P+b₁Q=a₂P+b₂Q`, the nonzero coefficient difference, the recovered
scalar equation, and `[k]P=Q`. IC certificates check every signed point relation,
distinct rows, full factor-base cancellation, and `[k]P=Q`. The solver never
reads the fixture answer.

All twelve fresh attacks passed the independent audit. The 26-test regression
suite passed, including 751 exact fused-circuit target checks at 31 and 61 bits.
Native arithmetic tests checked 39630 cases across 19, 31, and 61-bit fields,
including maximum-value dot products, inversion identities, and exceptional
batched additions. The earlier 57 complete attack certificates also reverified.
See [verification.json](verification.json), [unit_tests.log](unit_tests.log),
[native_tests.json](native_tests.json), and [selftest_native.cpp](selftest_native.cpp).

## Reproduce

From the project root, with Python, SymPy, python-flint, and a C++17 compiler:

```sh
python algebraic/optimized/benchmark.py --seeds 0 1 2
python algebraic/optimized/benchmark.py --verify-only
python algebraic/optimized/benchmark_circuit.py
cd algebraic/optimized
python -m unittest test_v2 -v
```

For the complete regression suite, run
`python -m unittest test_solver test_resultants test_optimized optimized.test_v2 -v`
from `algebraic`; its older Groebner tests also require Singular.

[benchmark.py](benchmark.py) builds its executables automatically. Native
executables and shared libraries are omitted from the source archive.
The earlier [full experiment](../end_to_end/README.md) and its source remain
unchanged so its certificates and measurements remain independently verifiable.

These measurements concern this 31-bit instance. The optimized circuit also
has exact 61-bit tests; a full 61-bit recovery is outside these measurements.
