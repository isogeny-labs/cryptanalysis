# Binary cubic gluing: target construction and publication novelty

- **Status:** investigating
- **Kind:** implementation gap, geometric proof gap, literature access gap
- **Affected work:** [3-kernel certificates](../experiments/ghs-sweeper/KERNEL_CERTIFICATE.md), [prime-to-three recognition theorem](../experiments/ghs-sweeper/CUBIC_GLUING.md)
- **Next action owner:** current research session
- **Last updated:** 2026-10-25

## Problem

We cannot identify a novel affected binary cubic curve family from a stable
torsion kernel alone: no characteristic-two quotient curve or evaluated
subgroup isogeny has been constructed, and publication priority is unresolved.

The fixed ell=3 source is over F512/F8 with modulus 515, b=24, a=0 and
its a=1 twist. Its two traces already occur in the historical sweeper journal.
The new ell=5 screen broadens the torsion-module predicate. The subsequent
degree-1-through-6 exclusions and written proof give geometric
indecomposability and genus-three existence for one source twist per passing
pair. They do not establish a novel affected source family or explicit target.
The user wants a novel family/criterion with proof and explicit transfer;
beating rho is not an acceptance gate.

## Evidence and uncertainty

- **Observed:** the frozen kernel checks enumerate and verify actual ell=3
  subgroup points, pairings and twist transport. There is no quotient equation.
- **Derived:** the ell=5-and-higher module recognition theorem has a written
  proof and agrees with all 480 GL2(F5) cases. All 126 five-only F512 twist
  pairs pass the small-isogeny screen; the [geometric proof](../experiments/ghs-sweeper/FIVE_GLUING_GEOMETRY.md)
  then gives existence for one unknown twist per pair. Five fixed finite
  module facts are checked in Lean; the general formalization remains open.
- **Suspected explanation:** none claimed for the absent reconstruction.
- **Missing capability:** binary quotient reconstruction and an evaluated
  homomorphism. The ell=5 geometric proof now has an explicit sufficient
  condition, verified on the 126 candidate pairs.
  Tian's 2023 full journal article is unread; the 2020 preprint is inspected.
- **Not established:** new published priority, a novel affected family, an
  explicit target or log transfer, or an efficient attack.

## What would unblock it

- [ ] Compare the exact criterion and construction against the full relevant
  primary literature, including the 2023 article or an accepted manuscript.
- [ ] Prove the selected quotient is geometrically indecomposable, choose
  the correct source twist and construct a smooth genus-three equation over F8.
- [ ] Evaluate the quotient homomorphism on a declared prime subgroup r
  coprime to the gluing prime; verify membership, exact image order, addition
  and a planted log by a separately checked recovery.

These conditions establish an explicit descent and allow a source-family
novelty assessment; they do not establish a faster solver or asymptotic attack.

## Next discriminating step

- **Action:** construct the ell=5 quotient on the b=48 F512 twist pair and
  select its arithmetic Jacobian twist. Actual E[5] coordinates are the next
  missing input; the current basis is an abstract torsion-module certificate.
- **Inputs and controls:** modulus 515, b=48, a=0/1, source orders 520/506;
  retain the [completed exact checks](../experiments/ghs-sweeper/CUBIC_GLUING_RESULTS.md),
  scalar/Jordan negatives and raw/table arithmetic replays.
- **Limits:** one fixed pair for construction; no curve-yield or cost inference.
- **Outcomes:** a reconstructed equation needs smoothness, correct field,
  polarization/twist and explicit prime-subgroup map checks; a failed
  construction does not refute the existence theorem. Neither outcome settles
  publication novelty without the primary-text comparison.
- **Recheck trigger:** actual E[5] coordinate certificate, quotient
  reconstruction or newly available primary text.

## Resolution and history

2026-10-25: current cryptanalysis main removes the historical missing-checker
dependency. That procedural block no longer applies to new checks. Frozen
reports are preserved. The construction and novelty gaps remain unresolved.

2026-10-25: completed 480-matrix and 1,008-source censuses, 126-pair geometric
screen, 39 Rust tests, fixed Lean certificate and 95-source corpus replay.
The sufficient five-gluing geometric proof is recorded. No target, selected
source twist, evaluated isogeny or recovered log is claimed.
