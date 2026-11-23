# Proof map

| Mathematical statement | Lean declaration or certificate | Status |
| --- | --- | --- |
| Norm recursion doubles an affine binary block | `AffineNorm.normFn_cons` | Checked Lean 4 |
| Translation by the new binary direction permutes the norm factors | `AffineNorm.normFn_translate_head` | Checked Lean 4 |
| Translation by any binary subset sum preserves the norm | `AffineNorm.normFn_translate_span` | Checked Lean 4 |
| Linearized vanishing polynomial is additive and zero on binary span | `SubspaceVanishing.vanishingFn_add` and `vanishingFn_zero_on_binarySpan` in prior N41 artifact | Checked Lean 4 in source artifact |
| Invariant polynomial lies in `F(q)[L_B(p)]` | Written root-count proof in `RESULT.md` | Lean bridge open: formal polynomial division over rational-function coefficients, invariant remainder and degree/root count |
| Concrete N41/N131 258-term compression | Exact `residual == 0` and independent 16-factor product equality in Sage producers | Executable finite-field certificate; Lean field representation bridge open |
| Nonzero right-subspace GCD detects a source-product root | Modular linearized recurrence plus exact Sage GCD; N131 constructed root independently checked | Concrete algebraic check; pair validity and group relation require separate witness replay |

`AffineNorm.lean` uses pinned `leanprover/lean4:v4.34.1`. Build command:

```sh
lean AffineNorm.lean > lean_check.log 2>&1
```

The saved output contains `#print axioms` for all three declarations.
The translation declarations use only `propext`, `Classical.choice` and
`Quot.sound`; there are no custom axioms, `sorry`, `admit`, native-evaluation
proofs or kernel bypasses. `lean4checker --fresh` was unavailable on this
host. The module proves the structural symmetry, while the explicit
invariant-ring and curve-resultant bridges remain open as stated above.
