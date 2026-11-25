# CM point-to-ideal scalar bridge

- **Status:** `investigating`
- **Kind:** construction and cost gap
- **Affected work:** [CM joint S4 research](../research/cm_joint_s4_20261123/README.md), [PR #1967](https://github.com/isogeny-labs/cryptanalysis/pull/1967), [lead atlas `LEAD-STR-class-group-ecdlp-bridge`](https://github.com/isogeny-labs/crypto-autoresearcher/tree/main/knowledge/leads/ecdlp)
- **Next action owner:** CM joint S4 research
- **Last updated:** 2026-11-25

## Problem

For an ordinary prime-field curve with large CM discriminant, the available horizontal-isogeny and principal-ideal relations are functions of the curve and known endomorphisms. The ECDLP input `Q=[d]G` adds a point. We lack an efficiently evaluable map or decomposition oracle whose output contains a nontrivial equation in `d` and whose fully charged cost improves the current relation pipeline on the same target. [pcc:unverified]

The concrete P-192 objective is a cold, same-target comparison with rho. A stage-level method can first qualify as an improvement against a frozen same-instance index-calculus baseline, with its full pipeline cost accounted for. Neither objective follows from smoothness of a principal ideal alone. [pcc:unverified]

## Evidence and uncertainty

- **Observed:** The [coordinate-to-ray screen](../research/cm_joint_s4_20261123/COORDINATE_IDEAL_RAY_SCREEN.md) gives a computable point-dependent ray residue `-1/(x(P)-1) mod r`. Exact finite-curve counts fail the additive scalar rule; paired coordinate-model controls do not isolate a horizontal-isogeny effect. Claim `PCC-20261125-d7ec76` is unverified. [pcc:unverified]
- **Derived:** The [x-only ray sign gate](../research/cm_joint_s4_20261123/X_ONLY_RAY_SIGN_GATE.md) proves that any `x`-only map into an odd-order ray subgroup satisfying the additive scalar law is trivial: `P` and `-P` have the same x-coordinate but opposite scalar labels. This is a structural reason for the coordinate candidate's additive failure; it does not exclude even nonadditive predicates. [pcc:unverified]
- **Observed:** The [signed three-sum ceiling](../research/cm_joint_s4_20261123/SIGNED_THREE_SUM_CEILING.md) caps any eight-point signed base at 96 nonidentity sums; the fixed source already attains it. The [frozen equal-yield mixed-base cost panel](../research/cm_joint_s4_20261123/MIXED_EQUAL_YIELD_COST_REPORT.md) then finds mixed/source CPU S4 solve ratios `0.984–0.993` across three model scales, missing its `0.90` component-gain gate. Claims `PCC-20261125-e28f9c` and `PCC-20261125-a64a1e` are unverified. [pcc:unverified]
- **Derived:** The [squared-ray gate](../research/cm_joint_s4_20261123/SQUARED_RAY_POINT_BRIDGE.md) identifies an order-`r` principal-unit subgroup, but its scalar-labelled class for `Q` is defined using `d`. The [three-summand support gate](../research/cm_joint_s4_20261123/README.md) bounds the present full-rank factor-base query route under its stated memory and uniform-query assumptions. [pcc:unverified]
- **Suspected explanation:** Coordinate-derived ray residues can vary with the chosen Weierstrass model without retaining the point-group law. This explains the screened candidate, not every possible coordinate-to-ideal map. [pcc:unverified]
- **Missing capability:** An explicit point relation or extractor that is both target-dependent and cheaper than its generic analogue after setup, query, linear algebra, and descent costs. [pcc:unverified]
- **What this evidence does not establish:** It is not a universal impossibility result for CM-assisted index calculus, a bound for every factor base, or a P-192 performance result. [pcc:unverified]

## What would unblock it

- [ ] Specify an executable map or decomposition oracle for `G,Q` that emits a replayable nonzero relation `a+b d=0 mod r` or a factor-base row with nonzero target coefficient, without using `d` as input. Verify it against independent point arithmetic on a fixed same-target instance.
- [ ] Show a mechanism-specific gain: hold curve order, factor-base size, known-log dimension, representation choice, and target distribution fixed, then compare relation yield and complete extraction cost with an isomorphism/model null and a non-CM control.
- [ ] For a security-relevant claim, freeze a cold same-target protocol and account for setup, failed attempts, relation collection, linear algebra, descent, storage, and matched rho; independently replay the point relation and cost records.

The first condition establishes a point bridge only. The second could establish a component improvement. The third is needed for a whole-attack comparison. [pcc:unverified]

## Next discriminating step

- **Action or proof obligation:** Specify a target-dependent relation mechanism that changes the effective base-log dimension or uses a different point decomposition than the saturated signed eight-point S4 construction. For an additive ray label, it must distinguish `P` from `-P`; for an even scalar predicate, it must give a charged full-log route. Give its isogeny-specific operation, a same-size generic control, and a cost prediction before timing. [pcc:unverified]
- **Inputs and controls:** Use a fixed source curve, target `Q`, same-size factor bases and an isomorphic coordinate-model null; verify each emitted row directly in the elliptic-curve group and compare with a generic transported-base route.
- **Execution limits and stop condition:** Start with exact small-field enumeration and solver operation counts. Stop a candidate when its relation is independent of `d`, its claimed gain disappears under model controls, or its charged query count already exceeds the matched reference.
- **Outcomes and next actions:** A valid point row advances to frozen cost measurement. A bounded negative result stays scoped to its candidate. An inconclusive solver run needs a diagnostic, and an infrastructure failure is recorded separately.
- **Recheck trigger:** A new explicit point-dependent map, a reduced-dimensional factor base, or an independently replayed same-target cost improvement.

## Resolution and history

2026-11-25: Opened after the explicit coordinate-to-ray screen. The fixed signed-base yield ceiling and equal-yield mixed-base cost panel narrow the unchanged-base route; the point-to-ideal scalar bridge remains unresolved. [pcc:unverified]
