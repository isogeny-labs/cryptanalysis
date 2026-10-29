# Known labels in a thin usable coordinate domain

- **Status:** open
- **Kind:** implementation gap and untested algorithmic hypothesis; a scoped
  proved sampling restriction; incomplete formalization and measurement provenance
- **Affected work:** [Frobenius lifts and progression blocks](../experiments/prime-field-frobenius-blocks-20261027/README.md)
- **Next action owner:** unassigned; publication does not schedule execution
- **Last updated:** 2026-10-27

## Problem

An efficient construction that deliberately places known-labeled points in a
small coordinate domain while lowering complete verified-relation cost remains
missing. Cheap auxiliary fixed-invariant lifts have not supplied that combination.

The imported toy experiments use prime-order E(F_p), labeled `T=uP+vQ`,
quadratic fixed-norm or cubic fixed-coefficient Frobenius orbits, and binomial
coordinate domains. The exact four performance fixtures and workload seeds are
retained in the linked archive. The original acceptance criterion counts point
construction, failed systems, root extraction, index recovery and verification;
a stage operation count is insufficient.

## Evidence and uncertainty

- **Observed:** the archived 64 bases include 18 failures and 78 verified
  divisors. Eight complete domain constructions per block method consume 515
  blocks, 58 without hits. The chain uses 45,973 group operations and
  2.351736994 CPU seconds; reused-table BSGS uses 77,662 and 0.262263897.
  These are unisolated historical partial component observations. Sorting hits,
  maintaining the collected domain, and antipodal scalar recovery/verification
  are unmeasured and uncounted, including 353 recovery opportunities per method.
  Complete construction costs and their ratios are unknown; see the
  [accounting correction](../experiments/prime-field-frobenius-blocks-20261027/ERRATA.md).
- **Derived:** for fixed invariants and irreducible quadratic/cubic orbit
  polynomials, B prescribed orbit parameters yield at most 2B nonzero traces.
  A uniform independent labeled sampler has success probability at most 2B/r.
  The written proof in [the archive](../experiments/prime-field-frobenius-blocks-20261027/archive/WRITEUP.md)
  uses the two ordinate choices and Frobenius orbit. It does not exclude
  nonuniform constructions, adaptive domains or different solvers.
- **Suspected explanation:** the finite covers shift rather than remove the
  chosen-base membership work. This is an interpretation of these implementations,
  not a universal lower bound.
- **Missing capabilities:** a faster direct solver on the reciprocal coefficient
  surface; a block certificate with sublinear field work and charged recovery;
  a faithful checked Lean bridge for the orbit-fiber argument. No Lean executable
  was available on the publication host. Historical host-isolation receipts,
  same-target rho controls and full-target phase accounting are also absent.
- **Limits:** exhaustive toy checks, a handwritten proof and an integrity check
  cannot certify an asymptotic attack gain, cryptographic-scale performance,
  the full geometric theorem in Lean, or security against untested methods.

## What would unblock it

- [ ] Supply a nonuniform thin-domain construction or a direct chosen-base solver
  whose explicit cost model improves the relevant verified baseline, including
  construction, every rejected system, extraction, recovery and verification.
- [ ] Independently replay its complete witnesses on frozen inputs at growing
  sizes; retain failed cases and resource receipts. Any claimed IC speedup also
  needs the current same-target rho reference and single-target online accounting.
- [ ] For a formal theorem claim, formalize the actual Frobenius-orbit-to-trace
  fiber statement and derive the cardinality bound without assuming its conclusion.
  Build the pinned Lean modules and retain axiom audits.

The first two conditions would establish a measured construction/solver
improvement in their stated regime. They would not alone establish a generic
sub-square-root ECDLP attack. A formalized sampling bound would certify only its
restricted mathematical statement, not rule out new constructions.

## Next discriminating step

- **Action:** freeze a direct reciprocal-divisor solver experiment retaining the
  degree-B sampled-base membership and `Tr_E(sum R_i)=O` throughout solving.
- **Inputs and controls:** begin with the archive's four exact nonanomalous
  fixtures and saved bases; compare all relation sets with batched pairs and
  trace fibers. Preserve both successful and empty systems. Use current lab
  identities, placement and timing controls before any performance claim.
- **Execution limits:** publication launches no search. A future protocol must
  name its explicit limits and stop rule before timing or held-out selection.
- **Outcomes:** a lower complete matched cost advances the stage baseline;
  identical membership work without a cost decrease closes only that solver
  variant; incomplete witnesses invalidate the implementation; missing receipts
  leave timing conclusions exploratory.
- **Recheck trigger:** a new solver, nonuniform construction, formalization
  dependency or qualified measurement protocol becomes available.

## Resolution and history

2026-10-27: imported the preserved code/data package and recorded the precise
construction, solver, formalization and provenance gaps. **Unresolved.**
Publishing the package or merging its PR does not resolve the original requirement.

2026-10-27: review identified collection/recovery work omitted from historical
cost sums. Corrected the publication labels and PDF, preserving all archive
bytes. Full collection/recovery accounting remains a future measurement gap.
