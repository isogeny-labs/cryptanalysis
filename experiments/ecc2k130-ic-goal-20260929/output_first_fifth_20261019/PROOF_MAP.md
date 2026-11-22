# Proof map

The checked Lean file is `OutputFirst.lean`. It was built with Lean 4.34.1, commit `5045d0056413266e57c625dcd7c365b10e377c52`, ARM64 macOS binary SHA-256 `1b370cfcbf44e80d1b004ab1b1ab9a4c73951f9f7c242140bcff9bc577576554`. The local `lean-toolchain` pins the release; the file imports `Std` and Lean's `Init.Grind.Ring.Field` from that toolchain. Reproduce with the exact executable:

```sh
/Users/adamburan/.elan/toolchains/leanprover--lean4---v4.34.1/bin/lean OutputFirst.lean
```

`lean_check.stdout` retains every `#print axioms` result and `lean_check.stderr` is empty. `lean4checker --fresh` was unavailable on this host. The declarations contain no `sorry`, `admit`, `sorryAx`, custom research axioms, or native-evaluation proof.

| Mathematical statement | Lean declaration | Hypotheses and status |
| --- | --- | --- |
| The fixed-seed product map `a ↦ a(a+s)` is additive in characteristic two. | `OutputFirst.source_product_additive` | Any `Field F` satisfying `∀z, z+z=0`; checked; standard axioms `propext`, `Classical.choice`, `Quot.sound`. |
| The binary pair-output law `Hx²+px+C=0` implies `px=Hx²+C`. | `OutputFirst.pair_law_product` | Same characteristic-two hypothesis; checked; standard axioms as above. |
| For nonzero `x`, `px=Hx²+C` gives `p=Hx+C/x`. | `OutputFirst.product_from_output` | Any field, `x≠0`; checked without axioms. |
| The pair-output law recovers its source product from `x`. | `OutputFirst.recover_product` | Characteristic two, `x≠0`, exact pair-output law; checked; standard axioms as above. |
| If the declared source-product code map is injective, two codes recovered from the same output are equal. | `OutputFirst.unique_source_code` | Injectivity of `encode : Code → F`, with both codes mapping to `Hx+C/x`; checked without axioms. |

The precise N41 and N131 source-product maps have 10 and 32 independent product-basis columns. The producer checks these ranks by GF(2) elimination; the independent Sage worker reconstructs the bases and checks the same ranks. Their concrete injectivity is a **finite computational certificate**, not yet a kernel-checked Lean theorem. Likewise, the connection from the actual elliptic-curve pair sum to the abstract quadratic law is checked by Sage across the frozen residual panel, while the Lean theorem assumes that law. A full formalization needs the exact binary curve group law, the reciprocal pair-output derivation, the chosen finite fields and code bases, and a kernel-replayed rank certificate. The abstract theorems do not silently discharge those concrete obligations.
