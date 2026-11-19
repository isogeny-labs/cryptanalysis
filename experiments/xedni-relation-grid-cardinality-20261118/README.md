# Lean proof of primitive relation grid cardinality

**Checked theorem.** Fix positive coprime integers `a,b`, a coefficient radius `H`, and a modulus `q` satisfying `2H(a+b)<q`. Let `L=2H+1`. The centered map

```text
(u,v) ↦ b(u−H)−a(v−H) mod q,   0 ≤ u,v < L
```

has image cardinality exactly `L²−(L−a)(L−b)`, where the subtractions on the right are natural subtractions. This is the positive-coefficient form of the closed formula derived in [the parent result](../xedni-relation-collision-count-20261118/README.md). The bound on `q` prevents modular wraparound between any two integer image values.

## Proof

Call a grid pair a *start* if its first coordinate is below `a` or its second is below `b`. There are `L²−(L−a)(L−b)` starts, since the complement is the rectangle with both coordinates at least the corresponding relation coefficient. Every pair has the same integer image as a start: when it is not a start, subtract `(a,b)`, which preserves `bu−av` and strictly lowers the first coordinate. Strong induction terminates this process. Coprimality implies that two pairs with equal integer images differ by an integer multiple of `(a,b)`. Two distinct starts cannot differ by such a multiple, so the integer image and the start set have the same cardinality. The no-wrap inequality makes reduction modulo `q` injective on the integer image. Shifting the grid coordinates by `−H` translates every output by one fixed residue and preserves cardinality.

## Proof map

| Step | Lean declaration in [GridCardinality.lean](GridCardinality.lean) | Status |
| --- | --- | --- |
| Count starts by complement rectangle | `card_starts` | Checked |
| A primitive fiber has at most one start | `linearImage_injOn_starts` | Checked |
| Every grid pair reduces to a start with the same integer image | `exists_start_same_image` | Checked |
| Start and full-grid integer images coincide | `image_starts_eq_grid` | Checked |
| Exact integer image cardinality | `integer_grid_image_card` | Checked |
| Exact modular image cardinality under no-wrap | `mod_grid_image_card` | Checked |
| Exact centered modular image cardinality | `centered_mod_grid_image_card` | Checked |

The theorem uses positive `a,b`. In the frozen 39-row public panel, this sign convention covers 21 rows from seven hits. The 18 rows with negative `b` were independently enumerated and match the absolute-value formula in the parent result. Their sign-reflection transfer is a separate Lean step; the checked theorem here does not silently include them. Likewise, identifying an arbitrary rational elliptic point's reduction with this public-subgroup coordinate remains the earlier point-level geometric bridge.

The toolchain is Lean `v4.35.0-rc4`, pinned to Mathlib revision `021c46bdd042f67b538b9f9871d556a93713a9a9` in [lakefile.toml](lakefile.toml) and [lake-manifest.json](lake-manifest.json). Run `lake build GridCardinality` in this directory. [build-output.txt](build-output.txt) records the successful build and seven `#print axioms` audits. Each theorem uses only `propext`, `Classical.choice`, and `Quot.sound`. The source contains no `sorry`, `admit`, `sorryAx`, custom research axiom, or native-evaluation shortcut. `lean4checker --fresh` is unavailable on this host.
