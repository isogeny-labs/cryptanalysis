# Xedni two-torsion rank-one gap

- **Status:** `investigating`
- **Kind:** formal construction boundary; open proof and implementation gap [pcc:unverified]
- **Affected work:** [Xedni two-torsion boundary audit](../research/xedni_rank_decay_20261118/TWO_TORSION_BOUNDARY_REPORT_20261120.md), [decay-disproof attempt](../research/xedni_rank_decay_20261118/DISPROOF_ATTEMPT_20261119.md)
- **Next action owner:** Xedni rank-decay task
- **Last updated:** 2026-11-20

## Problem

The public Cheon--Lee--Hahn--Chee two-torsion lift does not yet force a useful
dependence between its two selected finite-field points: under the cited
descent theorem, the published three-prime construction certifies only
`rank E(Q) <= 2`, while two selected non-torsion points require rank at most
one to force a dependence.

The audited source instance is `p=353`, `a=-1`, `b=16`, with selected points
`(9,63)` and `(17,183)`. The acceptance criterion remains a public,
non-circular lift whose complete search cost is charged and whose rational
dependence reduces to an invertible target-bearing source relation. A rank
bound without exact relation and source replay is not sufficient.
[pcc:unverified]

## Evidence and uncertainty

- **Observed:** The exact implementation in
  [`two_torsion_lift.py`](../research/xedni_rank_decay_20261118/two_torsion_lift.py)
  replays both published parameters `n=-1793` and `n=181`. Pinned PARI/GP
  2.17.2 reports `|B_n|`, `F_plus(n)`, and `F_minus(n)` prime in each fixed
  row, and exact arithmetic gives `gcd(F_plus,F_minus)=1`.
- **Derived or proved:** The cited rank expression evaluates to `1+2-1=2` in
  both rows. The Lean module
  [`CheonTwoTorsion.lean`](../research/xedni_rank_decay_20261118/formal/XedniRankClassification/CheonTwoTorsion.lean)
  proves the factor-difference identity and that a nonzero first lifted
  ordinate makes the two factors distinct. The complete expanded
  discriminant factorization is replayed by exact Python arithmetic, not yet
  formalized in Lean. [pcc:unverified]
- **Suspected explanation:** A useful member of this family would need a unit
  exception, one shared prime support across the two nonunit discriminant
  factors, or a stronger descent. A three-point extension is a separate route
  because rank at most two could then force a selected dependence.
- **Missing capability:** No public selector has certified either a
  rank-at-most-one two-point lift or a rank-at-most-two three-point lift with
  an exact target-bearing relation. No Mordell--Weil rank was computed for the
  fixed rows.
- **What this evidence does not establish:** It does not prove that the fixed
  curves have rank two, exclude actual rank one, measure a natural success
  frequency, or disprove the Xedni decay heuristic.

## What would unblock it

- [ ] Certify a two-point member with rank at most one, or a three-point member
  with rank at most two, using a public selector that does not use the unknown
  target scalar or a discovered relation.
- [ ] Recover an invertible target-bearing dependence and replay it exactly on
  the source curve while charging every rejected parameter, factorization,
  duplicate, rank attempt, timeout, and verification cost.
- [ ] Replicate the result prospectively on fresh frozen sources before making
  any decay-rate claim.

The first condition establishes only forced dependence capacity. The second
is necessary for a useful relation, and the third is necessary for an attack
or decay claim.

## Next discriminating step

- **Action or proof obligation:** Freeze and compare a shared-prime-support
  selector and an independent three-point extension against the published
  three-prime arm and direct finite-field relation search.
- **Inputs and controls:** Cross source prime, square-lift representative,
  parameter-search rule, selected-point count, and Silverman/JKSST small-prime
  local conditions independently. Preserve the exact source and reduction
  maps.
- **Execution limits and stop condition:** Use the existing Xedni protocol's
  prospective limits and mandatory checkpoint/tool gates. A bounded null
  result closes only the frozen selector and budget.
- **Outcomes and next actions:** A certified useful relation advances to fresh
  replication and full-cost slope testing. A null result records a bounded
  negative. A rank bound without a source relation remains inconclusive.
- **Recheck trigger:** A public selector, stronger descent certificate,
  three-point construction, or restored rank/checkpoint toolchain.

A planned step is not a completed experiment. Apply the existing execution,
review, budget, and archival rules before acting on it.

## Resolution and history

2026-11-20: Exact fixed-example replay and the factor-difference Lean boundary
were added. The published prime-value arm was classified as a rank-at-most-two
construction, not the required forced two-point dependence. Unresolved.
