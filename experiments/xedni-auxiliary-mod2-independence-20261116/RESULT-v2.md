# Two fixed auxiliary primes certify all 20 selected lift pairs

Every rational point pair admitted by the frozen p=47 centered-lift census is Z-linearly independent on its reconstructed curve over Q. Sixteen pairs have independent images in E(F_7)/2E(F_7); the remaining four have independent images in E(F_11)/2E(F_11). Each reconstructed cubic x³+Ax+B has no rational root, so its rational elliptic curve has no point of order 2. A checked Lean theorem establishes the abstract quotient-and-descent implication. The concrete finite-field and rational-root premises were independently replayed with exact Python arithmetic.

This is a versioned amendment to [the one-prime result](RESULT.md). `protocol.json` and its outputs remain intact. `protocol-v2.json` freezes the ordered auxiliary-prime list [7,11] and the same test on every one of the 20 admitted rows; `result-v2.json` and `rows-v2.json` report every outcome. The prime-11 lead was found in an exploratory search and is identified as such in the amendment. All 1,722 parent statuses and both rows with the prescribed reduced relation remain in the population.

| Rational curve (A, B) | Admitted ordered pairs | First certificate prime | Prescribed reduced-relation pairs | Rational cubic roots |
| --- | ---: | ---: | ---: | --- |
| (-847, 8035) | 8 | 7 | 0 | none |
| (-9478/31, 64516/31) | 8 | 7 | 2 | none |
| (-1129, -13679) | 4 | 11 | 0 | none |

For a certificate prime ℓ, the exact test enumerates E(F_ℓ), forms its doubled-point set 2E(F_ℓ), and checks that the images of P, Q, and P+Q are all outside that set. Their cosets in E(F_ℓ)/2E(F_ℓ) are therefore nonzero and independent. The quotient is killed by 2. A rational relation aP+bQ=O maps to this quotient, forcing a,b even. Since E(Q) has no point of order 2, halving the relation yields another relation; infinite descent gives a=b=0. This argument applies to every integral coefficient vector, including the prescribed vector (1,2) on both reduced-relation rows.

## Verification and proof map

`run_v2.py` used the checked local Sage build recorded in `sage-runtime.json`. `audit_v2.py` enumerates finite-field points and the doubling set independently in pure Python and invokes the v1 rational-root audit. It passed for all 20 rows, with 16 first certificates at 7 and four at 11. The raw records retain both primes' complete checks for each row, including nonselected prime results.

| Result | Lean declaration in `AuxiliaryMod2Independence.lean` | Status |
| --- | --- | --- |
| Parity from two basis images in (ZMod 2)^2 | `parity_from_two_independent_reductions` | checked |
| Parity from three nonzero images in an exponent-2 quotient | `parity_from_exponent_two_quotient` | checked |
| Infinite descent from even coefficients and no 2-torsion | `auxiliary_mod2_independence` | checked |
| Combined quotient criterion | `independent_of_exponent_two_quotient` | checked |
| Curve-specific E(Q) and reduction homomorphisms | no Lean declaration | partial formalization; exact arithmetic certificates and written proof retained |

The Lean toolchain and Mathlib revision are pinned in `lean-toolchain` and `lake-manifest.json`. `lake build AuxiliaryMod2Independence` completed 9,040 jobs; `#print axioms` for each reported theorem lists only `propext`, `Classical.choice`, and `Quot.sound`. `lean4checker --fresh` was unavailable. The exact missing Lean bridge is a model of these E(Q) curves, construction of good-reduction homomorphisms into the finite quotients, and formal checking of the point and rational-root certificates. The abstract theorem neither assumes the desired rational independence nor replaces it with an arithmetic certificate.

The result certifies independence for this complete finite selected-lift population. The next proof question is how the auxiliary-gate distribution behaves under larger, multi-prime CRT and curve-optimization selection laws; these are not represented by this p=47 law.

## Reproduction

From the repository root:

```sh
./sage --runtime-info
./sage -python experiments/xedni-auxiliary-mod2-independence-20261116/run_v2.py
python3 experiments/xedni-auxiliary-mod2-independence-20261116/audit_v2.py
```

From the experiment directory, run `lake build AuxiliaryMod2Independence`. The artifact hashes are in `SEAL.sha256`.
