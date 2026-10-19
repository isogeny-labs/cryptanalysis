# Proof map

`BatchInverse.lean` pins Lean 4.34.1 (`leanprover/lean4:v4.34.1`, commit `5045d0056413266e57c625dcd7c365b10e377c52`) and imports `Std` plus `Init.Grind.Ring.Field` from that toolchain. On this ARM64 macOS host the Lean executable has SHA-256 `1b370cfcbf44e80d1b004ab1b1ab9a4c73951f9f7c242140bcff9bc577576554`. Build with:

```sh
/Users/adamburan/.elan/toolchains/leanprover--lean4---v4.34.1/bin/lean BatchInverse.lean
```

`lean_check.stdout` contains the `#print axioms` audit. The declarations use only standard `propext`, `Classical.choice`, and `Quot.sound`, except `reverseBatch`, which uses none. The checked source has no `sorry`, `admit`, `sorryAx`, custom research axiom, or native-evaluation proof. `lean4checker --fresh` was unavailable on this host. The earlier failed proof attempt is described in `scratch/lean_first_errors.txt`.

| Result | Declaration | Exact status |
| --- | --- | --- |
| `(a·tail)⁻¹·tail=a⁻¹` when `tail≠0` | `BatchOutput.inverse_first_from_product` | Checked over any `Lean.Grind.Field F`. |
| `(head·b)⁻¹·head=b⁻¹` when `head≠0` | `BatchOutput.inverse_last_from_product` | Checked over any field. |
| A product of a list of nonzero field elements is nonzero | `BatchOutput.nonzero_prod` | Checked for any list and field. |
| The reverse batch recurrence computes each individual inverse from the inverse of the full product | `BatchOutput.reverseBatch_correct` | Checked for any list of nonzero field elements; its executable recurrence is `BatchOutput.reverseBatch`. |

The batch inversion proof follows the implementation: if `P_i` is the product before denominator `d_i` and `q=(P_i d_i)⁻¹`, emit `q P_i=d_i⁻¹` and update `q←q d_i=P_i⁻¹`. Induction over the list proves every emitted inverse. The concrete GF(2^41) and GF(2^131) code relies on the previous [output-first proof map](../output_first_fifth_20261019/PROOF_MAP.md) for source-product recovery. The checked theorem is about field inversion; the binary-curve x-only addition and the exact finite-field instances are checked computationally on the frozen panel, not reduced to Lean's kernel here.
