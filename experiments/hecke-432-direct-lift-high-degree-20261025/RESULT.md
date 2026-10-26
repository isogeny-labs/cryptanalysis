# Full-rank direct-lift screen now reaches weighted degree 26

The rational-coefficient ansatz
\(A(x_C,y_C,x_E)x_B+B(x_C,y_C,x_E)=0\) has no nonzero solution in the
frozen weighted-degree 16, 18, 20, 22, 24, or 26 spaces. Here
\((x_C,y_C)\) are the normalized \(X_0(27)=27a1\) coordinates,
\(x_E=(x_B^3-64)/x_B^2\), and the monomials of A and B have weights
\(2a+3b+2c\leq D\) and \(D+2\), respectively, with \(b\in\{0,1\}\).
Every frozen matrix has full column rank over both GF(997) and GF(1009),
including the 394-column degree-26 case. This extends the preceding
degree-4 through degree-14 screen; together the checked bounds cover all
even D from 4 through 26 in this specified linear-in-\(x_B\) family.

## Frozen rank screen

The [protocol](protocol.json) fixed q-series precision 720, training
exponents \(-(D+2),\ldots,500\), holdout 501–550, and both auxiliary
fields before the producer ran. The smallest resulting q-series precision
was 717. All exact coefficients used in the screen reduced successfully
modulo both primes.

| Degree D | Columns | Rank mod 997 | Pivot determinant mod 997 | Rank mod 1009 | Pivot determinant mod 1009 |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 16 | 164 | 164 | 337 | 164 | 108 |
| 18 | 202 | 202 | 14 | 202 | 895 |
| 20 | 244 | 244 | 635 | 244 | 158 |
| 22 | 290 | 290 | 204 | 290 | 385 |
| 24 | 340 | 340 | 265 | 340 | 19 |
| 26 | 394 | 394 | 303 | 394 | 991 |

The training and extended nullities are zero in all 12 cells.
`screen_result.json` contains every monomial, row range, pivot row, rank,
and determinant. `qseries_modp.json` retains all input coefficient arrays
through q^650. The independent Python/NumPy verifier reconstructs each
Laurent monomial, checks the 27a1 curve equation and B-to-E identity
through q^550, and reproduces all 12 determinants from the selected
pivot rows. Its [receipt](verification.json) is
`PASS_INDEPENDENT_PIVOT_REPLAY`.

## Proof boundary

A nonzero modular pivot determinant lifts to a nonzero rational minor,
because all entries are p-integral rational q-series coefficients. Thus
the rational training matrix has trivial kernel. Any identity in the
declared ansatz would give a nonzero coefficient vector in that kernel.
The pinned Lean theorem
[`DirectLiftRank.no_relation_of_nonzero_minor`](../hecke-432-direct-lift-20261025/formal/DirectLiftRank.lean)
formalizes this implication for arbitrary square minors; the
[formal receipt](formal/build-output.txt) rechecks its axioms. The
concrete modular q-series and determinants are independently replayed
outside Lean; a full Lean encoding of those coefficients remains open.

The result resolves the declared bounded formula space. The paired
\((C,E)\) map is injective on the p997 rational source census, motivating
a generic function-field degree calculation and, if that degree is one,
a higher-pole-bound formula search for the B coordinate.

Replay from the repository root:

```sh
./sage --runtime-info
./sage -python experiments/hecke-432-direct-lift-high-degree-20261025/screen_sage.py
python3 experiments/hecke-432-direct-lift-high-degree-20261025/verify.py
```

The next mathematical step is to determine the generic degree of
\(X_0(432)\to X_0(27)\times E\). A degree-one proof would establish that
a rational expression for the B coordinate exists; a larger degree
would explain why this class of expressions keeps having full rank.
