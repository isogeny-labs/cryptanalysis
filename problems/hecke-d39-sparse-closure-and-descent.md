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

## 2026-10-30 four-part study and continuation update

The [four-part result](../experiments/hecke-sparse-target-20261030/RESULT.md)
now verifies sparse fixed-geometry cells, deduplicated/folded information,
actual extension traces and bounded public-target recovery. At subgroup
orders16,319 and206,477, there are32 folded base columns, zero doubling/tripling
rows, and20 Hecke constraints. The frozen bootstrap therefore needs12 rather
than32 generic log queries. All labels replay independently. This addresses
the dense-scalar-collision ambiguity; it does not establish total cost or speed.

The largest original target failed256 shifts. Explicit known-label trace growth
recovered it in3 attempts; a matched201-point generic base recovered it in10,
and cost70 additions to grow versus528 for trace derivation. New trace columns
at r206477 add zero constraints on the original32 columns after elimination.
The attempted cheap higher-arity reuse controls also failed their65/256 caps.
The larger conductor30 selector exhausted200 candidates without an eligible
field; that continuation is missing evidence, with every rejection retained.

Remaining acceptance conditions are now specific: reduce the12 sparse-f6 free
logs without introducing equally many unanchored variables; verify target
connection on fresh public points rather than only exploratory continuations;
record exclusive phase costs and matched strong-rho evidence on the required
benchmark host; and complete the faithful Lean bridge/certificates. Lean4 and
mathlib are absent here, so no kernel-checked theorem is claimed. The source
report links all exact scopes, raw successes, failures and verification receipts.

The original finite experiment requirements are now executed within their
frozen limits. The scalable, fully measured IC improvement remains unresolved.

## 2026-10-30 pair-index reuse and stronger generic control

The [pair-reuse continuation](../experiments/hecke-sparse-target-20261030/PAIR_REUSE_RESULT.md)
now checks all57,475 pairs and all21,118 nonzero collision rows independently.
It reuses the already-required index before base-log preparation. Required
queries decrease9→1,12→1 and45→1 in three cells; the sparse r206477 cell
remains at12. Generic pair-only preprocessing has rank31 on r769 and rank158
on the conductor30 field, so the earlier scalar-only comparison must not be
read as the strongest available generic baseline. Hecke supplies10 and19
marginal constraints on the medium and sparse f6 fields over this stronger
control. All base labels replay; target coverage and statuses are unchanged.

The external same-budget goal is not complete: geometric generation, coefficient
tracking and LA are not fully priced, and stronger generic collectors have not
been ruled out. A no-extra-curve-sums stage improvement does not make this
zero-cost preprocessing or establish a generic lower bound.

The next qualified comparison needs the repository-required CUDA benchmark
host. Device and compute-binding presence checks find no available NVIDIA
device or configured RunPod/Modal/fleet binding in this environment; see the
linked access receipt. This blocks qualified cost/rho measurement here, not
ordinary correctness work or the mathematical possibility of a Hecke advantage.
Acceptance: configure that execution capability, freeze complete costs and a
stronger generic comparator, run fresh public-point controls, independently
replay every result, then reassess the same-total-budget claim.
