# Level-432 dual coordinate equation: formal addendum

This versioned addendum concerns the rational coordinate formula cited in
`experiments/hecke-432-map-identity-20261025/RESULT.md`. It leaves that
experiment's sealed files unchanged.

| Source expression | Lean declaration | Exact scope |
| --- | --- | --- |
| `(X³−16)(X³+128)² − (X³−64)³ = 432X⁶` | `Hecke432DualCurve.numerator_identity` | Polynomial identity in any commutative ring. |
| `((Y(X³+128))/X³)² = (((X³−64)/X²))³+432` when `Y²=X³−16` | `Hecke432DualCurve.curve_equation` | Field elements with `X ≠ 0`; the target curve equation only. |

The declarations do not prove that the formulas extend through `X=0` and
infinity, form a group homomorphism, have degree three, equal the dual isogeny,
or identify the quarter-shift map with a modular parametrization. The
modular-curve construction and Sturm argument remain open Lean obligations.

Build with the pinned shared workspace:

```sh
cd experiments/hecke-432-formal-ci-20261025
lake env lean -R ../.. ../hecke-432-dual-map-formalization-20261107/formal/DualCurveEquation.lean
```

The `lean-proof-gate.yml` corpus job checks added Hecke modules and their
`#print axioms` output on the pinned Lean and Mathlib revisions.
