# Frobenius-orbit lifts and arithmetic-progression certificates

## Summary

Two constant-degree extension constructions attach fixed-norm or fixed-coefficient
orbit coordinates to a point with a known label `T=uP+vQ`. An exact block
certificate finds labeled multiplicative-coset hits without scanning every point
with group additions. Both mechanisms are implemented and checked. These
experiments establish no reduction in complete attack cost.

## Claim label

**OBSERVATION**, together with the elementary finite-domain bound proved in
`WRITEUP.md`. The construction and divisor identities are exact; their
cryptanalytic usefulness is an experimental question.

## Algorithm family and mechanism

Representation-dependent factor-base construction and relation search:

* Quadratic extension points have fixed abscissa norm and known elliptic trace.
  Their six-point relation divisors have reciprocal norm sextics.
* Cubic Frobenius orbits have two fixed symmetric abscissa coefficients.
  A quartic finds the lifts; formal quotient representations avoid unnecessary
  embeddings into a common extension field for trace-only computations.
* Symmetric baby/giant blocks reduce coset membership to homogeneous quadratic
  resultants. Powering takes place modulo the giant-point polynomial, retaining
  the raw binomial coordinate constraint and including index recovery.

The known labels belong to **prime-field traces**, not to individual extension
points. The relation condition is `Tr_E(sum R_i)=O`, including every element of
the trace-zero kernel. Actual sampled-base membership is retained.

## Expected cost law

No predictive sub-square-root attack law is claimed. Field operations, group
operations, construction, rejected lifts, root extraction, failed blocks and
verification are separately recorded. Complete attack exponents are **unknown**.

The implemented block chain uses approximately
`O~(b*g*log B)` field work, with `M=2*b*g`, plus `b+g` group work and output
recovery. At balanced `b,g`, this is approximately linear in `M` in field work.
The proposed `O~(B+sqrt(M))` total bound was **not** obtained.

## Baseline and falsifier

Relations are compared with batched direct pairs on the identical accepted
trace bases. Block searches are compared with sequential scanning, coordinate
product certificates, and interval multi-target BSGS with a baby table tuned
for reuse across the entire batch. Complete labeled-domain construction uses
identical random starts and stopping rules for all four methods.

The proposed advantage fails these tests if base membership restores the usual
cost or if total construction time loses to the controls. That happened here.
This does not prove that all direct solvers on the reciprocal coefficient
surface, all composed maps, or all nonuniform constructions must fail.

## Result classification

`failed_or_overfit`

This is the repository's class for an unsupported attack improvement. The
positive construction identities and the restricted finite-domain theorem
remain valid; no fitted attack exponent or held-out success is asserted.

## Reproduction

See `WRITEUP.md`, `requirements.txt`, `run.sh`, and the raw JSON files under
`experiments/ideas/`. The standalone audit uses independent pure-Python extension
arithmetic and sequential block replay.
