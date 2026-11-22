# Proof map: quadratic triple-sum feature capacity

The exact feature map is `feature n x = x + 2^n * quadraticTail n x`, where the
tail packs the squarefree products of bit coordinates in lexicographic pair
order. This matches the bit layout of `rank_extended.py`. The result is a
structural lemma about the screen and a finite computation about one frozen
source law; the latter is recorded separately.

| Result | Lean declaration or check | Hypotheses and status |
| --- | --- | --- |
| The lower `n` bits of the lifted feature are `x`. | `QuadraticFeature.feature_mod` in `QuadraticFeature.lean` | Every `n`, `x < 2^n`; checked by Lean 4.34.1. |
| The lift is injective on `n`-bit coordinates. | `QuadraticFeature.feature_injective_on` | Every `n`, `x,y < 2^n`; checked by Lean 4.34.1. |
| For the frozen N131 W23 source sets, the affine GF(2) rank first equals 8,646 at family 271. | Open finite-rank formalization | `extended_rank_rows.jsonl` was independently recomputed by `audit_rank.py` with a different feature order and opposite pivot order. No Lean declaration for the finite rank certificate is asserted. |

The Lean definitions do not model the Koblitz group law, selected masks, or
the finite GF(2) elimination. A faithful Lean proof of the concrete 271-family
rank threshold would need imported checked point coordinates and a compact
kernel-checkable row-reduction certificate for the 8,646-column matrix. The
Python audit is the current verification for that finite computation.

Pinned toolchain: `leanprover/lean4:v4.34.1` in `lean-toolchain`, with `Std`
from that distribution. The logged command is:

```sh
elan run leanprover/lean4:v4.34.1 lean experiments/ecc2k130-ic-goal-20260929/n41_n131_triple_x_quadratic_capacity_20261023/QuadraticFeature.lean
```

`lean_check.log` contains the build output and `#print axioms` audit. Both
declarations use only Lean's standard `propext` foundation; neither depends on
an axiom encoding the result. `lean4checker --fresh` was unavailable on this
host.
