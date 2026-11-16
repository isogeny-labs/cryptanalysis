# Complete algebraic index calculus and faster candidate extraction

Newer [native optimizations and a Pollard rho comparison](../optimized/README.md)
are available. The v1 sources and measurements below remain unchanged.

This directory compares complete attacks with auxiliary isogeny maps against
algebraic index calculus using an explicit-polynomial relation solver. The target remains the
original prime-order curve over F_(2^31−1):

```
E: y² = x³ + 2x + 14
n = #E(F_p) = 2147505293, prime
P = (1, 814455902)
Q = (988441464, 1643383878)
```

All complete attacks recover `123456789` and verify `[k]P=Q`. The solver reads
only public input. The known answer is kept in a separate fixture file read
only by the independent verifier. These runs use two-point algebraic relations;
no point-pair table or precomputed factor-base logarithms enter the solver.
Duplicate and sign-reversed factor-base rows are discarded. Each final
dependency uses at least three distinct signed relation rows; recovery cannot
come from collecting the same relation target twice.

## Complete recovery timings

Median full recovery time over three fixed search seeds on the 31-bit curve:

| Relation solver | Full time (s) | Time / auxiliary time |
|---|---:|---:|
| Auxiliary maps | 27.606 | 1.00× |
| Same base, explicit polynomial | 75.854 | 2.75× |
| Independent random base, explicit polynomial | 85.146 | 3.08× |

The controlled same-base comparison gives **2.75× faster complete recovery**.
The independent random-base comparison gives **3.08×** by median elapsed time.
Each same-base pair has identical queries, relations, and dependency weights.

| Search seed | Common same-base queries | Auxiliary (s) | Explicit same base (s) | Random-base queries | Random base (s) |
|---:|---:|---:|---:|---:|---:|
| 0 | 36,262,094 | 25.694 | 65.942 | 46,838,477 | 85.146 |
| 1 | 60,080,847 | 39.928 | 109.025 | 34,384,115 | 62.583 |
| 2 | 41,844,181 | 27.606 | 75.854 | 57,816,394 | 105.424 |

An additional 16-seed experiment over F_(2^19−1), with full prime order
523801 and 19 point representatives, completed 48 audited attacks. Its median
same-base speedup was 1.97× and independent random-base speedup
was 1.93×. These short runs have greater process-launch timing noise.

Raw runs and certificates: [31-bit results](field31_s5_base0/summary.json),
[19-bit results](field19_s5_base0/summary.json).

Timing includes factor-base construction, native setup, every unsuccessful
relation query, successful relation verification, incremental modular Gaussian
elimination, and public-key verification. Compilation and the later independent
certificate audit are excluded. The curve parameters and group order are common
public input. Each method is charged for constructing its base in each run.
Methods run serially and execution order rotates across search seeds. Machine
and compiler details are in [environment.json](environment.json).

The depth-five auxiliary chain has 32 membership roots, of which 17 lift to
signed point pairs on the target. Its auxiliary curve is `C: y²=x³+x`, with
known order `p+1=2³¹`, and all maps have degree two. A small base makes the complete experiment
practical; the target group still has its full original prime order. The depth
was selected from target-query microbenchmarks, rather than from a favorable
recovered logarithm. Other measured depths are in
[native_profiles_simd.json](native_profiles_simd.json).

There are two controls:

* `same_base` receives the identical 17 point representatives with the maps
  removed. It computes an explicit quadratic product and evaluates it at the
  base coordinates. For each search seed, it finds exactly the same relations
  after exactly the same number of queries as `chain`, isolating the effect of
  the algebraic representation.
* `random` receives 17 independently sampled representatives on the same target
  curve, fixed before any relation search. It uses the same explicit-polynomial
  solver. Its query count varies because its relation opportunities differ.

Both controls use only liftable coordinates, a preallocated balanced polynomial
product tree, cached evaluation powers, Mersenne reduction, and SIMD dot
products. The auxiliary solver and both controls share vectorized initial
Semaev coefficients, target generation, point arithmetic, relation extraction,
and modular linear algebra. Their input files contain no pair-sum table.

The scalar implementation pilot is preserved in [scalar_pilot](scalar_pilot).
Its same-base comparison was effectively tied. The measured improvement in the
final implementation includes vectorization of the auxiliary circuit; the
ordinary polynomial solver was also optimized before the final runs.
An initial SIMD pilot is retained in [simd_pilot](simd_pilot); its recovery
allowed repeated rows. Those runs are excluded from the final timing table.

## GCD and algebraic solver optimization

Median candidate-extraction times over 16 fixed targets at 32768 membership
roots (16342 liftable coordinates):

| Candidate extraction | Time (ms) | Baseline time / time |
|---|---:|---:|
| FLINT GCD and roots | 284.387 | 1.00× |
| Cached remainder blocks | 195.712 | 1.45× |
| Liftable coordinates + cached blocks | 101.916 | 2.79× |
| Direct native isogeny circuit | 1.235 | 230.23× |

The optimized polynomial GCD path is **2.79× faster**.
The circuit replaces polynomial construction and GCD extraction with scalar
evaluation of the exact resultant circuit; its complete verified relation query
takes 1.433 ms median. This phase comparison is distinct from
the end-to-end native comparison above.


The reference backend already calls FLINT's fast polynomial GCD. The new
[known_root_gcd.py](../known_root_gcd.py) amortizes a tree of fixed membership
polynomials across queries. It reduces the resultant down that tree, then
computes small GCDs at 256-root leaves. This works with auxiliary and ordinary
bases. Before building the tree, the model-aware backend removes coordinates
that do not lift to the target curve, since they cannot occur in a rational
point relation. This preparation depends only on the base and curve. Its
correctness tests include every finite target on a curve with two-torsion.
The ordinary resultant CLI enables both optimizations with `--gcd-blocks 256`.

For the auxiliary encoding, [native_candidates.py](../native_candidates.py)
uses a stronger optimization. At each liftable base coordinate x, start with
the three scalar coefficients of S₃(x,y,X). Push the weighted quadratic through
each degree-two isogeny using the exact formulas in
[resultant_solver.py](../resultant_solver.py). Evaluate the last quadratic at
the terminal coordinate. The resulting scalar is exactly
`Res_y(S₃(x,y,X), P(y))`. Its zeros identify candidate x coordinates directly:
there is no large resultant polynomial to construct or GCD to compute.

The native 31-bit implementation evaluates four coordinates per AVX2 operation.
The 61-bit library uses exact 128-bit intermediate arithmetic. Both have exact
coefficient-backed value tests and signed point-relation checks. Each candidate
is verified by point subtraction and a factor-base coordinate lookup. Only
individual factor-base points are stored.

The GCD benchmark uses all 16 original, unmodified targets from the 32768-root
experiment. It checks exact equality between blocked and ordinary GCD roots,
equality of native circuit values with polynomial evaluations, and equality of
all returned point decompositions with the reference solver. Setup times are
recorded separately in [gcd_benchmark.json](gcd_benchmark.json). The circuit
timing is a different extraction algorithm; it is not a faster implementation
of the generic GCD routine itself. The full native comparison above gives both
methods native arithmetic and excludes this Python-versus-native confounder.

## Reproduce and verify

Requires Python 3, SymPy, python-flint, and a C++17 compiler. Native executables
and libraries build automatically and are omitted from the downloadable source
archive. `-march=native` enables SIMD when supported; the scalar fallback is
available on other machines. The algebraic backend requirements are listed in
[requirements.txt](../requirements.txt). The complete regression suite also
requires Singular for its older Groebner tests; installation is described in
[the algebraic README](../README.md).

From the project root:

```sh
python algebraic/end_to_end/benchmark.py algebraic/end_to_end/field31_s5_base0 --seeds 0 1 2
python algebraic/end_to_end/benchmark.py algebraic/end_to_end/field19_s5_base0 --seeds 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15
python algebraic/end_to_end/verify.py
cd algebraic
python benchmark_optimized.py
python -m unittest test_solver test_resultants test_optimized -v
```

Each full run stores its public input, query count, timing, signed relations,
and a weighted dependency certificate. The independent Python verifier checks
every relation `aP+bQ=±F_i±F_j`, cancellation of every factor-base column,
the remaining equation `AP+BQ=O`, and the recovered scalar. Primality, `[n]P=O`,
and the Hasse interval certify the full target group order.

The final audit checked **57 complete attacks and 790 point relations**, with
19 identical search-sequence comparisons. Native validation checked 40707
signed-pair targets and 5000 further public targets against the explicit
polynomial candidate masks. All 24 unit tests passed. Recorded checks are in
[verification.json](verification.json),
[native_validation.json](native_validation.json), and
[unit_tests.log](unit_tests.log).

For a single optimized two-point query, use `relation_solver.py --engine native
--m 2 --encoding chain` with `--public`, `--auxiliary`, `--roots`, `--x`, `--y`,
and `--output`. The ordinary polynomial backend remains available with
`--engine resultant` and optional `--gcd-blocks 256`.

These are measured results for these prime fields and implementations. They do
not establish a general speedup for every auxiliary curve or a practical
attack on cryptographic-size prime-field curves. Full 61-bit recovery has not
been demonstrated here; its native circuit is covered by exact solver tests.
