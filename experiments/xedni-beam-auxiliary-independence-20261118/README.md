# Auxiliary independence certificates for the depth-eight beam

## Result

All eight final rational point pairs retained by the frozen width-eight
Hensel beam are **Z-linearly independent on their reconstructed curves over
Q**. For each pair, one good auxiliary reduction has odd group order and
excludes rational 2-torsion. A second good reduction maps both points to
independent classes in `E(F_ell)/2E(F_ell)`. Every integer relation would
therefore have both coefficients even, and the absence of rational
2-torsion permits infinite descent to zero coefficients.

| Beam state | Model bits | Odd-order prime: group order | Quotient prime: group order / doubled set |
| --- | ---: | --- | --- |
| D8:0 | 158 | 7: 11 | 29: 20 / 5 |
| D8:1 | 162 | 5: 9 | 113: 120 / 30 |
| D8:2 | 167 | 101: 95 | 19: 24 / 6 |
| D8:3 | 176 | 13: 21 | 59: 64 / 16 |
| D8:4 | 177 | 3: 7 | 23: 24 / 6 |
| D8:5 | 177 | 23: 27 | 13: 12 / 3 |
| D8:6 | 179 | 3: 7 | 11: 16 / 4 |
| D8:7 | 179 | 3: 7 | 7: 12 / 3 |

The public relation is fixed at `p=313`, subgroup order `q=331`, target
scalar `w=300`, offsets `(0,13)`, public points `(15,174)` and `(236,132)`,
and vector `(5,4)`. The beam is selected before this auxiliary search.
Each final rational residual has 313-adic depth at least eight, while the
independence certificates address **every** nonzero integer coefficient
pair for those exact rational curves and points.

## Frozen census and independent replay

`protocol.json` pins the beam-result digest, all eight final states, and
every odd prime from 3 through 199 in ascending order. The run retains
all 360 state-prime rows: 23 bad-model reductions and 337 good point
reductions. It records the full group order and doubled-point-set size
where applicable, and chooses the first witness of each type. There are
no missing witnesses within the frozen cap.

The checked Sage run reconstructs each rational curve and point pair,
verifies the parent residual, and enumerates the finite groups. The
independent `audit.py` uses only Python `Fraction` and integer finite-field
group arithmetic. It checks all 360 statuses, rational point membership,
reduction back to the fixed public points, group orders, doubled sets,
coset independence, and first-witness choices. `audit-result.json` records
the pass and the SHA-256 of `rows.json`.

## Proof map

| Mathematical step | Lean declaration or evidence | Status |
| --- | --- | --- |
| Independent nonzero images in an exponent-two quotient force even relation coefficients | `parity_from_exponent_two_quotient` in the existing [AuxiliaryMod2Independence.lean](../xedni-auxiliary-mod2-independence-20261116/AuxiliaryMod2Independence.lean) | Checked with pinned Lean and Mathlib |
| Even-coefficient descent when the rational group has no 2-torsion | `auxiliary_mod2_independence` in the same module | Checked |
| Combined quotient criterion | `independent_of_exponent_two_quotient` in the same module | Checked; its `#print axioms` lists `propext`, `Classical.choice`, and `Quot.sound` |
| Eight concrete rational curves, good reductions, finite quotients, and point images | `run-result.json`, `rows.json`, `audit-result.json` | Exact Sage and independent Python checked; elliptic reduction maps and these concrete certificates are not encoded as Lean terms |

The odd-order witness uses the standard injectivity of good reduction on
prime-to-`ell` torsion for odd `ell`. The quotient witness checks that
`P1`, `P2`, and `P1-P2` lie outside the doubled-point set. The quotient
has exponent two, so their classes are linearly independent. The existing
Lean theorem proves the structural descent from those hypotheses; the
concrete elliptic-reduction bridge remains a formalization task.

## Reproduction

From the repository root, with the beam result present:

```sh
/Volumes/SSD990/cryptanalysis/sage --runtime-info > experiments/xedni-beam-auxiliary-independence-20261118/runtime-info.json
/Volumes/SSD990/cryptanalysis/sage -python experiments/xedni-beam-auxiliary-independence-20261118/run.py
python3 experiments/xedni-beam-auxiliary-independence-20261118/audit.py
```

`runtime-info.json` identifies the accepted Sage build. This is a
certificate for the eight fixed rational lifts, with no inference from
the prime cap to other lift-selection laws.
