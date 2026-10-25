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
The new ell=5 screen broadens the torsion-module predicate; it does not by
itself establish geometric indecomposability or a new affected source family.
The user wants a novel family/criterion with proof and explicit transfer;
beating rho is not an acceptance gate.

## Evidence and uncertainty

- **Observed:** the frozen kernel checks enumerate and verify actual ell=3
  subgroup points, pairings and twist transport. There is no quotient equation.
- **Derived:** the ell=5-and-higher module recognition theorem has a written
  proof in the linked note. Its preregistered exact Rust checks are separate
  from a quotient reconstruction. General Lean formalization remains open.
- **Suspected explanation:** none claimed for the absent reconstruction.
- **Missing capability:** binary quotient reconstruction and an evaluated
  homomorphism. At ell=5, geometric indecomposability also needs its own proof.
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

- **Action:** enumerate all GL2(F5) module cases against the proposed exact
  criterion, and exact F512 source traces passing five but failing three.
- **Inputs and controls:** the frozen [check contract](../experiments/ghs-sweeper/CUBIC_GLUING_CHECKS.md), all 480 matrices, scalar/Jordan controls,
  all 1,008 full-degree binary models, raw/table arithmetic replay.
- **Limits:** exact finite scopes; no random yield or timing extrapolation.
- **Outcomes:** a disagreement invalidates the criterion or implementation
  until corrected with retained failure evidence; agreement identifies module
  candidates for geometric reconstruction, not catalogue attack entries.
- **Recheck trigger:** completed exact checks or a characteristic-two quotient
  reconstruction or newly available primary text.

## Resolution and history

2026-10-25: current cryptanalysis main removes the historical missing-checker
dependency. That procedural block no longer applies to new checks. Frozen
reports are preserved. The construction and novelty gaps remain unresolved.
