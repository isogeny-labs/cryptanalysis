# Transfer audit completeness and geometric proof bridges

- **Status:** investigating
- **Kind:** implementation gap, proof gap, access/tool limit; bounded proved obstructions
- **Affected work:** [Rust audit](../tools/transfer-audit/README.md), [theorems](../tools/transfer-audit/THEOREMS.md)
- **Next action owner:** transfer-audit implementation/research task
- **Last updated:** 2026-10-30

## Problem

The requested general classification of efficient subgroup-preserving transfers
cannot yet be certified: arbitrary isogeny paths, quotient maps, higher-genus
families, and geometric/formal proof bridges remain unimplemented or unproved.
Literal absence of all abstract transfers is false (identity/same-field maps
already exist); the meaningful unresolved question concerns specified descent
targets or useful algorithms. This record retains that full requirement.

## Evidence and uncertainty

- **Observed:** the Rust audit verifies fixed fixtures, exact subfield bounds,
  classical ranks, Frobenius coefficient orbits and the existing same-field
  genus-three map. Small-field class enumeration has a disclosed degree-eight
  ceiling. Transitive Lean checking covers the twelve tool theorems documented
  in the proof map. Failed builds and checkpoint attempts are retained in
  `tools/transfer-audit/evidence/`.
- **Proved scope:** the written size obstruction excludes every target
  Jacobian over F2 of genus<=63 for the certified B-163 subgroup, uniformly
  across source isogenies preserving it. The algebraic gcd obstruction excludes
  all abelian-variety homomorphisms to a supplied actual target class when
  the Frobenius polynomials are coprime. These are applications of known theory.
- **Access limit:** the S3 checkpoint attempt first failed at GNU/BSD stat
  portability (fixed), then at missing AWS credentials/upload token. No new
  research sweep was launched under that failure. Unit/proof/fixture correctness
  checks are not cryptanalytic benchmarks or a new research campaign.
- **Missing capabilities:** full geometric Lean bridges, target curve/Weil
  validation, arbitrary evaluated isogeny paths, general gGHS maps, and a
  classification of efficiently evaluable group homomorphisms.
- **Not established:** complete class traversal at cryptographic degree,
  globally novel weak families, a faster solver, or exclusion of every possible
  descent. A failed bounded search or missing capability is not a security proof.

## What would unblock it

- [ ] Supply a specified transfer universe with a completeness theorem and an
  executable, source-bound verifier covering every branch; broaden each family
  explicitly instead of relabelling the present universe.
- [ ] For full Lean coverage, define and prove the finite-group/cardinality,
  Frobenius/Tate, Weil-bound and Rust-refinement bridges from the proof map;
  do not encode those statements as custom axioms or assumed conclusions.
- [ ] Before research sweeps, restore a valid checkpoint upload transport and
  pass `scripts/checkpoint.sh gate`; this is infrastructure, not a math result.

These conditions would improve explicitly scoped coverage. They would not by
themselves establish cheaper ECDLP solving or global publication novelty.

## Next discriminating step

Add an independently verified isogeny-path provider beyond Frobenius, starting
with the complete small-field classes and requiring evaluated maps, kernel
and prime-subgroup checks. Use the current positive/negative fixed fixtures
as controls. A closed finite graph proves only its declared vertex/edge
universe; larger degrees, exhausted budgets or failed map construction remain
open. Recheck on a new path implementation, formal bridge or restored checkpoint
transport. Follow the existing checkpoint/protocol rules before experiments.

## Resolution and history

2026-10-30: implementation and scoped proofs added; broader completeness and
formalization remain unresolved. Merging the implementation PR is not a proof
of the broader research deliverable.
