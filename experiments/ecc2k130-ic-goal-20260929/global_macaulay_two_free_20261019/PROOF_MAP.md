# Proof map

`DualSound.lean` builds with the pinned `leanprover/lean4:v4.34.1` toolchain. The executable on this ARM64 macOS host has SHA-256 `1b370cfcbf44e80d1b004ab1b1ab9a4c73951f9f7c242140bcff9bc577576554`; the Lean release commit is `5045d0056413266e57c625dcd7c365b10e377c52`. Reproduce the build with:

```sh
/Users/adamburan/.elan/toolchains/leanprover--lean4---v4.34.1/bin/lean DualSound.lean
```

`lean_check.stdout` retains the `#print axioms` audit. Both declarations use only standard `propext`; the source contains no `sorry`, `admit`, `sorryAx`, custom research axiom or unverified native-evaluation proof. `lean4checker --fresh` was unavailable on this host.

| Result | Lean declaration | Exact hypothesis and status |
| --- | --- | --- |
| A Boolean linear functional that vanishes on every generator vanishes on every finite XOR of those generators. | `GlobalMacaulayDual.annihilates_fold` | Any value type `V`, XOR operation, zero element and Boolean functional satisfying the stated additivity and row-value hypotheses; kernel checked. |
| If that functional evaluates the constant row to one, no XOR of generated rows equals the constant row. | `GlobalMacaulayDual.no_constant_certificate` | Same hypotheses plus `phi one=true`; kernel checked. |

For the frozen N41 matrix, the functional is parity of the bitwise intersection with the 27,832-weight dual witness in `dual_v3_result.json`. The independent `verify_dual.py` reconstructs the 41 coordinate equations from the 13-term resultant, generates **all 55,391 rows**, checks functional value zero on each, and checks value one on the constant monomial. That finite construction is a computational certificate; the exact GF(2^41) polynomial basis, Boolean monomial ordering, row generator and 137,980-bit witness are not yet represented and kernel replayed in Lean. The abstract theorem's hypothesis is discharged by the saved independent verifier rather than silently assumed for the concrete curve.

The mathematical scope is the declared Macaulay matrix: source products of the two free W11 codes, the 41 coordinate equations of the frozen two-pair resultant, and squarefree multipliers of degree at most three. Source-validity equations, higher-degree multipliers, and other joint constraints are outside this matrix. The earlier [resultant proof map](../n41_w11_freecode_resultant_20261018/PROOF_MAP.md) covers the curve-to-resultant implication with its exact assumptions.
