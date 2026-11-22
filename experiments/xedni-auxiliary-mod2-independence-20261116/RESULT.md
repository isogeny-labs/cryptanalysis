# Auxiliary mod-7 gate proves independence of 16 selected lift pairs

Sixteen of the 20 rational point pairs admitted by the frozen p=47 centered-lift law are **Z-linearly independent on their reconstructed curves over Q**. This includes both admitted pairs satisfying the prescribed relation after reduction modulo 47. The auxiliary reduction modulo 7 maps each of these 16 pairs to distinct nonzero elements of E(F_7) ≅ (Z/2)^2, while all three rational curves have no rational 2-torsion. The conclusion follows by an infinite descent on any proposed integer relation. The four other admitted rows reduce to points of order 4 on a cyclic group of order 4; this particular criterion leaves them open.

## Frozen census and exact result

`protocol.json` fixes the SHA-256 of the parent `xedni-varying-curve-selection-20261115` v2 census and the outcome-independent tests. All 1,722 archived statuses are retained. `run.py` uses the checked Sage launcher; `audit.py` independently enumerates E(F_7), applies its group law in integer arithmetic, and checks rational 2-torsion by the rational-root theorem. The audit passed on all 20 admitted rows.

| Reconstructed curve (A, B) | Accepted ordered rows | Mod-7 group | Rows meeting independence criterion | Reduced relation rows |
| --- | ---: | --- | ---: | ---: |
| (-847, 8035) | 8 | (Z/2)^2 | 8 | 0 |
| (-9478/31, 64516/31) | 8 | (Z/2)^2 | 8 | 2 |
| (-1129, -13679) | 4 | Z/4 | 0 | 0 |

For each of the three curves the cubic x³+Ax+B has no rational root. Thus E(Q) has no point of order 2. The parent coefficients reduce to (-1,-2) modulo 47, and that curve has 43 points. The exact point orders, coordinates, distinctness, and parent row indices appear in `rows.json`; `result.json` preserves census status counts and the four exceptions.

## Proof and formalization map

Let P,Q lie on one rational curve in the 16-row subset. Good reduction at 7 gives a group homomorphism from E(Q) to E(F_7). Since the images of P and Q are distinct nonzero elements of (Z/2)^2, reducing aP+bQ=O forces a and b even. Write a=2a' and b=2b'. Then 2(a'P+b'Q)=O. The absence of rational 2-torsion forces a'P+b'Q=O. Repeating halves the integer coefficients indefinitely, so a=b=0. For the two rows with P+2Q=O modulo 47, the prescribed vector has no rational relation under this selected-lift law.

| Mathematical step | Lean declaration in `AuxiliaryMod2Independence.lean` | Exact hypotheses | Status |
| --- | --- | --- | --- |
| Independent mod-2 images force even coefficients | `parity_from_two_independent_reductions` | additive group, homomorphism to (ZMod 2)^2, basis images | checked |
| Even coefficients and no 2-torsion permit infinite descent | `auxiliary_mod2_independence` | additive group, 2-torsion injectivity, parity of every relation | checked |
| Combined structural implication | `independent_of_mod2_reduction` | the preceding reduction images and 2-torsion hypothesis | checked |
| Instantiate on these E(Q) curves | no Lean declaration | formal elliptic-curve reduction maps, exact point-image and rational-root certificates | **partial**; Sage and independent Python arithmetic verify the concrete premises |

The pinned toolchain is Lean 4 `v4.35.0-rc4` with Mathlib revision `021c46bdd042f67b538b9f9871d556a93713a9a9`. `lake build AuxiliaryMod2Independence` completed 9,040 jobs. `#print axioms` for each reported theorem lists only `propext`, `Classical.choice`, and `Quot.sound`; `lean4checker --fresh` was unavailable. The remaining formal bridge is an implementation of these rational elliptic curves and their good-reduction homomorphisms in Lean, together with formal checking of the finite-field and rational-root certificates. No unproved curve statement is substituted as a Lean theorem.

This result is specific to the frozen two-point selection law with one auxiliary prime. The parent auxiliary incidence-rank condition does not itself assert group independence: the four cyclic-order-4 rows pass that gate but fail this mod-2 criterion. A next experiment can add an explicit mod-2 image gate to the selection law, or derive a separate independence certificate for the four exceptions.

## Reproduction

From the repository root:

```sh
./sage --runtime-info
./sage -python experiments/xedni-auxiliary-mod2-independence-20261116/run.py
python3 experiments/xedni-auxiliary-mod2-independence-20261116/audit.py
```

From this experiment directory, run `lake build AuxiliaryMod2Independence`. `sage-runtime.json`, `build-output.txt`, `audit.json`, and `SEAL.sha256` retain the execution and artifact receipts.
