# Sparse Hecke relation closure and arbitrary-target descent

- **Status:** open
- **Kind:** untested scaling hypothesis; missing target-descent implementation
- **Affected work:** [D39 result](../experiments/hecke-d39-scalar-closure-20261030/RESULT.md)
- **Next action owner:** research agent, future larger-class study
- **Last updated:** 2026-10-30

## Problem

The finite D39 rank closure does not establish an IC advantage because the
same rank is obtained from generic doubling alone, and arbitrary-target
descent is not implemented. The current curve is X_0(11)/F367, group order385,
subgroup11, cofactor35; 64 saved columns cover every projected subgroup element.

## Evidence and uncertainty

Observed: six original arms pass, and projected equalities or doubling raise
rank52 to63. The independent three-arm control gives ranks54,63,63 without
any Hecke rows. Four anchored solutions (256 labels) pass separate short-model
replay. Receipts and exact hashes are linked in the result.
Derived: the finite gain cannot distinguish Hecke structure from generic
scalar closure on this fixture. Suspected explanation: dense subgroup coverage;
this is not a measured scaling law. Missing capability: a frozen larger sparse
class study and a verified target-descent pipeline. No impossibility or
cryptographic-size security statement follows.

## What would unblock it

- [ ] Freeze larger class fixtures with complete curve/subgroup identities,
  verified maps where applicable and predominantly distinct projected columns.
- [ ] Compare Hecke+scalar closure with the same-budget generic scalar closure
  and matched random-base controls; retain group checks, ranks and every cost.
- [ ] Implement target descent with scalar replay on fresh public points and
  measure complete matched costs before claiming an IC improvement.

These conditions are needed to support the intended claim; a finite rank
advantage alone is insufficient to establish a solver speedup.

## Next discriminating step

Select and publish larger sparse fixtures and controls before execution,
using the checked Sage launcher if new CM classes are generated. Retain actual
projected base size and collision counts rather than only original columns.
Apply checkpoint, resource and benchmark rules. Freeze resource limits in
that protocol; none of those runs is launched here. An advantage beyond generic
closure leads to target-descent work; equality with it calls for a different
source of independent relations. Failure to generate a fixture is missing
evidence, not a negative mathematical result.

## Resolution and history

Unresolved. 2026-10-30: opened after the dense toy audit and Hecke-free control.
