# Bounded direct-lift formula screen has full rank through weighted degree 14

The normalized level-432 B coordinate cannot satisfy a rational-coefficient relation
\(A(x_C,y_C,x_E)x_B+B(x_C,y_C,x_E)=0\) within the frozen monomial spaces of
weighted degree \(D\leq14\) for \(A\) and \(D+2\) for \(B\). Here
\((x_C,y_C)\) are the normalized \(27a1\) modular-parametrization coordinates,
\(x_B\) is the normalized \(432a1:y^2=x^3-16\) coordinate, and
\(x_E=(x_B^3-64)/x_B^2\) is the degree-three projection. The largest
screened matrix has 130 columns. Each of the 12 frozen matrices has a
nonzero square minor over its auxiliary field, independently replayed from
saved q-series coefficients.

## Frozen screen and result

The [protocol](protocol.json) was fixed before generating q-series. Its
monomials are \(x_C^a y_C^b x_E^c\), where \(b\in\{0,1\}\) and
\(2a+3b+2c\) bounds weighted degree. The weights match the poles of the
three coordinates at the q cusp. Each matrix takes the coefficient vectors
of \(x_B\) times every A monomial and every B monomial at exponents
\(-(D+2),\ldots,240\). Exponents 241–280 were reserved as a holdout.

| Degree D | Columns | Rank mod 997 | Pivot determinant mod 997 | Rank mod 1009 | Pivot determinant mod 1009 |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 4 | 20 | 20 | 370 | 20 | 215 |
| 6 | 34 | 34 | 179 | 34 | 52 |
| 8 | 52 | 52 | 492 | 52 | 938 |
| 10 | 74 | 74 | 888 | 74 | 329 |
| 12 | 100 | 100 | 536 | 100 | 34 |
| 14 | 130 | 130 | 602 | 130 | 120 |

The training kernel is zero in every cell; including the holdout leaves it
zero. `screen_result.json` records each exact monomial ordering, row range,
rank, selected pivot rows, determinant, and status. `qseries_modp.json`
retains the input coefficients through q^320. `verification.json` records
the independent determinant replay. The verifier also checks the 27a1
equation and the B-to-E x-coordinate identity through q^280.

## Proof and scope

For each degree, the q-series coefficient map is linear in the coefficients
of A and B. A nonzero pivot determinant modulo 997 or 1009 means that the
corresponding rational minor is nonzero: every matrix entry is the reduction
of a rational q-series coefficient with denominator prime to the selected
prime. Hence the rational matrix has full column rank. Any rational
identity in the specified monomial space would have a zero coefficient
vector on the training rows, forcing all its A and B coefficients to vanish.
This is a bounded exclusion for the declared linear-in-\(x_B\) ansatz;
higher degrees and formulas using additional level invariants remain open.

| Result | Proof and verification |
| --- | --- |
| Nonzero minor excludes a nonzero coefficient relation | `DirectLiftRank.no_relation_of_nonzero_minor`, checked in the pinned Lean 4/mathlib environment. |
| Twelve concrete minors are nonzero | Sage producer and separate Python/NumPy Laurent multiplication and Gaussian elimination agree on every determinant in `verification.json`. |
| Exact q-series coefficients represent the named modular maps | Checked Sage `modular_parametrization().power_series(360)` and saved runtime identity; the independent replay checks the 27a1 and B-to-E equations. |

The Lean theorem formalizes the central linear-algebra implication with its
nonzero-determinant hypothesis. Encoding the exact modular q-series and all
130-column numerical certificates inside Lean remains an open formalization
bridge; those certificates are instead replayed by `verify.py`. The
mathematical argument above identifies precisely where they enter.

From the repository root, replay with the checked Sage launcher:

```sh
./sage --runtime-info
./sage -python experiments/hecke-432-direct-lift-20261025/screen_sage.py
python3 experiments/hecke-432-direct-lift-20261025/verify.py
```

The next experiment should add source-dependent level information. At p=997,
the complete 16/27 route distinguishes source records that the original
\(j\)-value and E output do not, so a terminal invariant or an anchored
Hecke relation is a concrete route to choosing among the three rational B
lifts.
