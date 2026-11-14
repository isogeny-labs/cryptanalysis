# No prime-field elliptic isogeny model for the actual q223 source

- **Status:** resolved for this fixed shortcut; the research objective remains open
- **Kind:** written mathematical obstruction, integer formal proof complete;
  actual geometric/group formalization partial
- **Affected work:** [actual V2 maps](../experiments/chained-transfer-public-target/V2_MAPS_01.md)
  and [integer proof map](../experiments/chained-transfer-public-target/prime-field/README.md)
- **Next action owner:** current Chained ECDLP Transfers research task
- **Last updated:** 2026-11-13

## Problem

The actual E/F223³ with order11092292 cannot become isogenous over F223³ to
an elliptic curve defined over F223. This eliminates that specific elliptic
shortcut, while retaining the constructed prime-field Jacobian descent.
All scientific standing remains unsigned. [pcc:unverified]

## Evidence and uncertainty

The original source order certificate uses independent native field/curve/
prime checks and a unique Hasse multiple. If B/F223 becomes isogenous to E
over K, then #B(K)=11092292. Its subgroup B(F223) has order m dividing that
number, and Hasse forces195≤m≤253. The original Lean kernel excludes all59
integers. This gives the written contradiction; both original toolchains
and all three exact local PCC bindings pass (d8f845/180a3c/7c5dfe), unsigned.
Actual elliptic groups and the standard counting bridges are not implemented
in the Lean module. No computational advantage or generic security statement
follows. [pcc:unverified]

## What would unblock it

For the same actual group order and field, the fixed shortcut contradicts
the counting conditions. Changing the task to another field/source or a
higher-dimensional target changes the mathematical problem and needs its
own exact map and subgroup identities; it does not refute this obstruction.
The positive Jac(C)(F223) target already has the required dimension.

- [x] Original actual extension-field source/order certificate retained.
- [x] Written subgroup/Hasse/isogeny-count implication stated explicitly.
- [x] All59 integer cases and the quantified Nat implication checked by both
  original Lean gates, zero trusted, exact local bindings retained.
- [ ] Formalize actual elliptic/group/counting bridges if claiming full
  formal geometry; signed main standing remains separate.

## Next discriminating step

Continue the higher-genus completed-transfer descent candidate under the
published prospective protocol, and require exact public-target answers.
Benchmarking still needs the actual S3 checkpoint and live resource/budget
admission. Reopen this fixed shortcut only on evidence that the stated source
identity or one of the standard counting hypotheses differs.

## Resolution and history

2026-11-13: fixed elliptic shortcut excluded by the written counting proof
and exact integer module. The first PCC binding was not_covered due to
caller PATH;953579 preserves it and the unchanged claim later passes.
Whole original proof captures and the formalization gap remain explicit.
The broader ECDLP research problem is unresolved. [pcc:unverified]
