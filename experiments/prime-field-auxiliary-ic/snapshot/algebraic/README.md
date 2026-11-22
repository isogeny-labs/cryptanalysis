# Implemented algebraic index-calculus solver

**Latest:** [native v2 and Pollard rho](optimized/README.md) complete the original
31-bit recovery at median times of 9.69 seconds for batched IC and 18.3 ms for
rho, using shared arithmetic. The matched-search IC optimization gives a
1.79× median paired speedup; large-base circuit extraction improves by 3.08×.

The earlier [complete native algebraic comparison](end_to_end/README.md)
recovers the original 31-bit logarithm with a 2.75× median speedup over the same
base without auxiliary maps, across three matched search seeds. Independent
certificate audits reject duplicate and opposite relation rows. The optimized
GCD backend also improves the original large-base extraction stage by 2.79×.

An earlier solver uses the isogeny composition directly through quadratic
resultants. It demonstrates a measured relation-stage advantage
over an independent random base: about 1.79 times elimination throughput and
1.14 times total relation throughput in the 32768-root F_(2^31-1) test.
See [structure_results/README.md](structure_results/README.md) for the
algorithm, matched reruns, limits, and reproducible commands. The older
Groebner-only results below remain historical measurements of that engine.

**Audit correction:** the optional split solver missed the infinity chart,
and the earlier ordinary-base comparison used target-dependent roots. Both
are corrected. The old ordinary timing comparison is withdrawn as a general
performance comparison. See [audit/README.md](audit/README.md) for the
reproduction, fixes, source-paper context, and replacement experiments.

The missing solver is implemented: auxiliary isogeny equations plus Semaev
polynomials, an actual Groebner basis, FGLM order conversion, finite-field root
extraction, and exact elliptic-curve point/sign verification.

`index_calculus.py` connects it to relation collection and modular linear
algebra. There is no pair-table search or DLP-oracle fallback in this pipeline.

Validation completed:

* Twelve tests, including exhaustive small-base point-sum comparisons over both
  requested fields, unsatisfiable systems, invalid inputs, denominators,
  direct S4, an infinite intermediate point sum, and machine-integer overflow
  regressions for target coordinates and large curve coefficients.
* Thirty-six matched small algebraic relation benchmarks, all solved and
  independently verified.
* Complete Groebner-based index calculus over F_127, recovering k=37 with
  auxiliary-chain, expanded-root, and ordinary factor bases.
* Bounded attempts at the original 1024/2048-root sizes. These did not finish;
  no full-size algebraic DLP or speedup is claimed.

## Polynomial systems

For every factor-base x-coordinate, introduce z_(i,1)=x_i and a variable per
further isogeny stage. With u=z_(i,j)-r_j, impose

```text
u * (z_(i,j+1) - u - A_j) - B_j = 0,
```

and at the terminal stage impose `u*(c-u-A_last)-B_last=0`. These are the
denominator-cleared equations for `f_j(z)=z-r_j+A_j+B_j/(z-r_j)`. The code
requires B_j != 0, so a denominator zero leaves -B_j != 0 and cannot solve
the cleared equation. Extracted solutions are checked in the rational maps.

For two-point relations, add

```text
S3(x1,x2,x(target)) = 0,
S3(x,y,z) = (x-y)^2*z^2
            - 2*((x+y)*(x*y+a)+2*b)*z
            + (x*y-a)^2 - 4*b*(x+y).
```

For three-point relations, the production default adds exact S4: the
resultant in w of S3(x1,x2,w) and S3(x3,x(target),w). For quadratics
A*w^2+B*w+C and D*w^2+E*w+F, this is

```text
(A*F-C*D)^2 - (A*E-B*D)*(B*F-C*E).
```

This includes infinite intermediate sums. A chain of length s gives m*s
variables and m*s+1 equations, matching the slides.

Optional `--summation split` introduces a finite intermediate coordinate w
and two quartic S3 equations. The solver now also completes the infinity
chart, x1=x2 and x3=x(target), whenever that chart can contain a relation.
Both chart results are verified and merged. Direct S4 remains a convenient
single-system formulation. The older small benchmarks used regular targets
and passed exhaustive checks, but did not exercise the previously missing
chart.

The solver considers both signs of each liftable y-coordinate, retaining
only exact sums equal to the full target point. Extension-field solutions
and coordinates not lifting to E(F_p) are rejected.

## Backend and resource bounds

For p=2^31-1, Singular 4.4.1 computes a grevlex standard basis and FGLM
conversion to lexicographic order. For p=2^61-1, Singular uses its exact Z/pZ
coefficient ring for the basis computation; SymPy 1.14.0 performs FGLM over
the actual prime field, since Singular disables FGLM on that ring type.
No floating-point arithmetic is used. Univariate factors over F_p supply
the finite-field roots for lexicographic back substitution.

Both computation and extraction run in subprocesses with wall-time and
address-space bounds. Timeouts and memory failures are separate from an
unsatisfiable ideal. `--algorithm slimgb` is available for the 31-bit field;
recorded timings use `std`, not every possible algebraic algorithm.

## Historical conditioned algebraic fixtures

The ordinary-root column below is withdrawn as evidence for a general
with/without-auxiliary performance claim. These were conditioned correctness
fixtures. The target-independent replacement is documented in the audit.

The small comparison uses eight membership roots and known-decomposable
targets. Within each case, all encodings receive the same curve and target:

1. `chain`: auxiliary low-degree map constraints.
2. `expanded`: the identical set V, encoded by product_(v in V)(x-v), with
   no auxiliary-map equations. This isolates the encoding's effect.
3. `plain`: an unstructured set of the same size, filled with consecutive
   ordinary x-values. The common planted decomposition's coordinates are
   included so this solver also receives a satisfiable task. It constructs
   no auxiliary curve or maps in its polynomial system.

The planted decomposition generates a test target and is never supplied to
the solver. These conditioned positive tasks do not measure the probability
that a random target decomposes.

Median total time per three-point relation, including root extraction,
over three seeded/repeated cases:

| Field | Auxiliary chain | Same roots, expanded | Ordinary roots |
|---|---:|---:|---:|
| F_(2^31-1) | 2.497 s | 0.620 s | 0.644 s |
| F_(2^61-1) | 4.470 s | 1.192 s | 1.238 s |

The chain formulation was slower at this small size. Lower degree did not
compensate for the extra variables in this backend. Two-point totals are
around 0.4 seconds and substantially include Python-worker startup; the
saved summary also records backend-only times.

The larger attempts use direct S4, a 20-second solver wall-time cap, and
1536 MiB of address space. Each task is known to have a valid decomposition.

| Field / roots | Auxiliary chain | Expanded roots | Ordinary roots |
|---|---|---|---|
| F_(2^31-1), 1024 | Timeout | Timeout | Timeout |
| F_(2^61-1), 2048 | Memory limit, 16.6 s | Timeout | Timeout |

These are single bounded attempts, not completed DLP benchmarks. They do not
establish an asymptotic conclusion. Inputs, Singular programs, logs, bases,
solutions, timings, and failure records are retained under `benchmarks/`.

## Complete index-calculus correctness run

```text
p=127, E: y^2=x^3+2x+51, #E=109 (prime)
P=(3,46), Q=(6,122), recovered k=37.
```

The chain and expanded runs use the same eight roots and random targets;
both recover k after 22 algebraic relation-search trials. A separate
ordinary-root run uses {10,...,17}, constructs no auxiliary curve, and also
recovers k. These demonstrate integration, not statistical speed comparisons.

For cofactor projection, the driver forms polynomial relations on raw points
using public preimages `P_full/Q_full` or `relation_P/relation_Q`, then projects
the resulting sum. It asserts [h]relation_P=P and [h]relation_Q=Q and never
substitutes projected x-coordinates into raw isogeny constraints. This examines
one preimage of a subgroup target; it does not enumerate all kernel translates,
so its relation rate need not match projected pair-table search.

## Reproduce

Requires Singular and SymPy. A system `Singular` is detected automatically,
or set `SINGULAR_BIN`. On Debian 13, `python install_singular.py` downloads and
extracts a local installation without root. Vendor binaries and caches are
omitted from the downloadable archive.

```sh
cd /workspace/index_calculus_demo/algebraic
python test_solver.py
python verify_artifacts.py
```

One actual relation solve over F_(2^31-1), and the identical task without maps:

```sh
python relation_solver.py --public fixtures/curve31.json \
  --auxiliary fixtures/aux31_s3.json --encoding chain --m 2 \
  --x 2051971722 --y 1473238040 --output example_chain
python relation_solver.py --public fixtures/curve31.json \
  --roots fixtures/roots31_s3.json --encoding expanded --m 2 \
  --x 2051971722 --y 1473238040 --output example_expanded
```

Run the corrected target-independent comparisons:

```sh
python benchmark_relations.py --toy --repeats 16 --timeout 5
python benchmark_relations.py --large --bits 31 --repeats 1 --timeout 10
```

Complete index calculus with algebraic relation search:

```sh
python index_calculus.py --public fixtures/toy_public.json \
  --roots fixtures/toy_roots.json --auxiliary fixtures/toy_auxiliary.json \
  --encoding chain --output full_toy/chain
python index_calculus.py --public fixtures/toy_public.json \
  --roots fixtures/toy_roots.json --encoding expanded --output full_toy/expanded
python index_calculus.py --public fixtures/toy_public.json \
  --roots fixtures/toy_plain_roots.json --encoding plain --output full_toy/plain
python verify_artifacts.py
```

`solver.py` implements relation solving; `relation_solver.py` is its CLI;
`index_calculus.py` is the full pipeline. `small_summary.json` and
`large_runs.json` record measurements. The earlier pair-sum timings remain
separate historical experiments in `../comparison/`.
