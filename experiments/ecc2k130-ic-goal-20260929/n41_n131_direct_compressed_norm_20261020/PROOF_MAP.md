# Proof map

| Result | Lean declaration or exact check | Status |
| --- | --- | --- |
| Norm across a new binary source direction | `QuadraticBlockNorm.quartic_norm_step` | Checked Lean 4, arbitrary characteristic-two commutative ring and quartic coefficients |
| Quadratic norm identity | `QuadraticBlockNorm.quadratic_norm` | Checked Lean 4 |
| Quartic decomposition into `U(Z)+YV(Z)` | `QuadraticBlockNorm.quartic_decomposition` | Checked Lean 4 |
| Translation symmetry for any binary subset sum | `AffineNorm.normFn_translate_span` in the prior affine-block artifact | Checked Lean 4 there |
| N41/N131 coefficient identity | `build_bench_sage.py` and explicit-block equalities in `run_sage.py` | Exact checked Sage arithmetic on pinned field representations |
| Right-subspace root test | Modular linearized recurrence and exact polynomial GCD in `run_sage.py` | Exact finite-field check; a retained root still needs curve-point validation |

The Lean module pins `leanprover/lean4:v4.34.1`. Its build command and
axiom audit are:

```sh
lean QuadraticBlockNorm.lean > lean_check.log 2>&1
```

All three declarations report only `propext`, `Classical.choice`, and
`Quot.sound` under `#print axioms`. The module contains no `sorry`,
`admit`, custom research axiom, native proof evaluation, or kernel bypass.
`lean4checker --fresh` was unavailable on this host. The generic theorem
proves the recurrence used by the executable. The concrete curve-to-quartic
elimination and source-state validity are imported from the earlier
independently audited artifacts, not re-proved in this module.
