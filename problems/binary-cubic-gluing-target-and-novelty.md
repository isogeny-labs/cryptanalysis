# Binary cubic gluing: target construction and publication novelty

- **Status:** investigating
- **Kind:** explicit-map implementation gap, partial formalization, publication-priority gap
- **Affected work:** [recognition theorem](../experiments/ghs-sweeper/CUBIC_GLUING.md), [quartic census and CM criterion](../experiments/ghs-sweeper/QUARTIC_CUBIC_RESULTS.md)
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

The subsequent published O3 plane-quartic census finds 30 targets at trace
-35 and three at +35, two classes missing from that local journal. The new
source pair has b=59, a=0/1, traces -35/+35 and orders 548/478, with primes
137/239. Matching Weil polynomials establish an isogeny-class relation,
not an evaluated or efficient log transfer. The CM discriminant criterion
gives a written indecomposability proof for transverse 53-gluings, but those
quotients have not been identified with the explicit quartics.

## Evidence and uncertainty

- **Observed:** the frozen kernel checks enumerate and verify actual ell=3
  subgroup points, pairings and twist transport. There is no quotient equation.
- **Derived:** the ell=5-and-higher module recognition theorem has a written
  proof and agrees with all 480 GL2(F5) cases. All 126 five-only F512 twist
  pairs pass the small-isogeny screen; the [geometric proof](../experiments/ghs-sweeper/FIVE_GLUING_GEOMETRY.md)
  then gives existence for one unknown twist per pair. Five fixed finite
  module facts are checked in Lean; the general formalization remains open.
- **Observed:** all 33 new quartic targets have independently replayed first
  three point counts. Six negative-trace targets have the published V4
  elliptic-quotient geometry; the other 27 have trivial geometric automorphism
  group, including all three positive-trace targets.
- **Derived:** the CM discriminant/degree-partition test excludes every
  decomposable transverse 53-quotient for the +/-35 source pair. The full
  written argument includes the ordinary CM degree bridge. Four named Lean
  theorems certify its finite arithmetic core; geometry remains unformalized.
- **Suspected explanation:** none claimed for the absent reconstruction.
- **Missing capability:** binary quotient reconstruction and an evaluated
  homomorphism. The ell=5 geometric proof now has an explicit sufficient
  condition, verified on the 126 candidate pairs.
  Tian's 2023 full journal article is unread; the 2020 preprint is inspected.
- **Not established:** new published priority, a novel affected family,
  identification of an explicit quartic as the constructed quotient,
  a log transfer or an efficient attack. The O3 and V4 families are published.

## What would unblock it

- [ ] Compare the exact criterion and construction against the full relevant
  primary literature, including the 2023 article or an accepted manuscript.
- [x] Record sufficient written geometric indecomposability criteria for
  five-gluing and the fixed +/-35 transverse 53-gluings.
- [ ] Choose the correct source twist and identify a smooth genus-three
  equation over F8 with the constructed principally polarized quotient.
- [ ] Evaluate the quotient homomorphism on a declared prime subgroup r
  coprime to the gluing prime; verify membership, exact image order, addition
  and a planted log by a separately checked recovery.

These conditions establish an explicit descent and allow a source-family
novelty assessment; they do not establish a faster solver or asymptotic attack.

## Next discriminating step

- **Action:** identify a trace +35 O3 target as a polarized quotient of the
  b=59 source, or construct the actual 53-quotient and select its arithmetic
  twist. Actual E[53] points and quotient reconstruction are missing; the
  current kernel is an abstract torsion-module certificate. The b=48 five-
  gluing construction remains an alternative, not a completed route.
- **Inputs and controls:** modulus 515, b=59, a=1, r=239; the three positive-
  trace equations and their raw replay certificates; both source twists,
  the six known V4-route negative-trace controls, and raw/table arithmetic.
- **Limits:** one source pair for construction; no curve-yield or cost inference.
- **Outcomes:** a reconstructed equation needs smoothness, correct field,
  polarization/twist and explicit prime-subgroup map checks; a failed
  construction does not refute the existence theorem. Neither outcome settles
  publication novelty without the primary-text comparison.
- **Recheck trigger:** actual E[53] or E[5] coordinate certificate, quotient
  reconstruction or newly available primary text.

## Resolution and history

2026-10-25: current cryptanalysis main removes the historical missing-checker
dependency. That procedural block no longer applies to new checks. Frozen
reports are preserved. The construction and novelty gaps remain unresolved.

2026-10-25: completed 480-matrix and 1,008-source censuses, 126-pair geometric
screen, 39 Rust tests, fixed Lean certificate and 95-source corpus replay.
The sufficient five-gluing geometric proof is recorded. No target, selected
source twist, evaluated isogeny or recovered log is claimed.

2026-10-25, subsequent phase: 33 explicit spectral targets, two new local
trace classes, complete target automorphism enumeration and a derived CM
indecomposability criterion. All 48 Rust tests, strict Clippy and the
96-source Lean corpus gate pass. Target equations exist independently of
the quotient proof; quotient identification and log transfer remain open.
The earlier frozen problem version remains bound by its original manifest
at commit 9ddbe2c6; the new manifest records this version transition.
