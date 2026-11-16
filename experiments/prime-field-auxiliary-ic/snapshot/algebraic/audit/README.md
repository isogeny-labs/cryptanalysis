# Audit and corrections

**Follow-up:** the subsequent
[chain-aware resultant solver](../structure_results/README.md) demonstrates
a measured relation-stage advantage using a different algorithm. The audit
below concerns the earlier generic Groebner implementation and its fixtures.

The audit found a real completeness defect in the optional split-S4 solver,
and a selection bias in the earlier ordinary-factor-base benchmark. Both
are corrected. They should be distinguished from the question of whether
the auxiliary construction produces a computational speedup.

## Reproduced missing relation

On E:y^2=x^3+x over F_127, T=(0,0) has order two, so T+T+T=T.
With membership roots {0}, the original split solver returned

```text
status: solved
relations: []
```

The direct-S4 solver correctly returned [(0,0),(0,0),(0,0)]. Before-fix
artifacts are retained in `before_infinity_fix/`.

The split system used two S3 quartics and a finite coordinate w for the
intermediate sum. Here that sum is the identity. The missing projective
chart is x1=x2, x3=x(target), together with the original membership equations.

`solve()` now solves both charts when needed. If target.x is outside the
factor base, the infinity chart is provably empty. Otherwise it computes a
second Groebner basis and merges the verified point relations. The corrected
result is retained in `after_infinity_fix/` and the regression test is
`test_split_S4_completes_missing_infinity_chart`.

This defect affected split-mode completeness. It did not affect the default
direct-S4 solver. The previous small regular benchmark cases also happened
to pass exhaustive checks, so this bug is not an explanation of their timing
difference.

## Benchmark selection correction

The old benchmark built an ordinary root set by inserting the coordinates
of a known target decomposition, then filling its remaining entries. That
was a useful conditioned-positive correctness fixture, but it was not an
independently chosen ordinary factor base for a general performance claim.
The old ordinary-versus-auxiliary timing table is withdrawn as evidence for
that general claim. Its numerical records remain in `../benchmarks/`.

The replacement benchmark:

* Builds both bases before choosing any target.
* Matches membership-root count and liftable-coordinate count.
* Samples a common uniformly distributed finite curve point independently.
* Records relations, no relation, and unknown/resource-limited outcomes.
* Checks every completed small problem against an exhaustive oracle.
* Compares chain and expanded encodings on the identical structured base.

Membership polynomials are now cached per factor base. They are no longer
rebuilt for every x-variable and every relation target.

The 61-bit raw algebraic relation problem must also be kept separate from
the earlier 38-bit cofactor-projected point-table problem. Those timings
cannot be combined to claim a like-for-like 61-bit DLP comparison.

## Corrected runs

The complete test suite has 12 passing tests. The corrected toy benchmark
uses the fixed prime-order target y^2=x^3+2x+51 over F_127 and 16 independently
sampled targets per encoding. All 48 computations completed and matched
the exhaustive oracle. The chain and expanded versions found a relation
on the same one of 16 targets; the independent ordinary base found relations
on three targets. This small sample does not establish a performance ranking.

A fresh unseeded 1024-root, three-point relation trial over F_(2^31-1)
timed out at ten seconds in all three encodings. All three outcomes remain
unknown, not unsatisfiable. See `benchmarks_corrected/large/`.

Six additional small-case runs checked standard versus slim Groebner
algorithms and three variable orderings. All returned the same verified
relation. Their basis times ranged from about 1.98 to 2.84 seconds; these
checks identified no large ordering or algorithm-selection speedup. Raw
artifacts are retained in `order_profiles/`.

## What the source paper says

Petit, Kosters, and Messeng, Section 5, explicitly compare against the
ordinary Semaev root-polynomial formulation and report that

> these systems are easier to solve than ours using Groebner basis algorithms
> on similar parameters.

Source: https://people.maths.ox.ac.uk/petit/files/16PKC_primeECDLP.pdf#page=14

The paper therefore does not supply a guarantee that the auxiliary-chain
system outperforms ordinary index calculus. The audit confirms bugs and
experimental limitations, not such a guarantee or a practical speedup.

## Reproduce

```sh
cd /workspace/index_calculus_demo/algebraic
python test_solver.py
python benchmark_relations.py --toy --repeats 16 --timeout 5
python benchmark_relations.py --large --bits 31 --repeats 1 --timeout 10
python verify_artifacts.py
```

New experiments write under `audit/benchmarks_corrected/`, preserving the
earlier conditioned fixtures and their original measurements.
