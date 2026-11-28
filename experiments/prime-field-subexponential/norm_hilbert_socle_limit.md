# Socle structure of the norm-convolution quotient

The universal terminal Hilbert coefficients do not by themselves show whether
the norm-convolution quotient is Gorenstein, level, or has earlier annihilated
components. This control computes the full graded socle

\[
  \operatorname{Soc}(A)=\{a\in A:A_1a=0\}
\]

for the sparse deterministic coefficient triple from the universality control.
It constructs exact quotient coordinates degree by degree and intersects the
kernels of multiplication by every variable.

The measured nonzero socle components are:

| section dimension | nonzero socle components |
| ---: | --- |
| 3 | degree 2: 1 |
| 4 | degree 2: 4 |
| 5 | degree 2: 3; degree 3: 1 |
| 6 | degree 3: 8 |
| 7 | degree 3: 14; degree 4: 1 |
| 8 | degree 4: 16 |
| 9 | degree 4: 46; degree 5: 1 |

Thus the measured even quotients are level, with type $2^{r/2}$. The odd
quotients from dimension five onward are not level or Gorenstein: a large
lower socle accompanies the one-dimensional terminal component. In the odd
rows the lower dimensions are 3, 14, and 46.

## Exact limit

These are exact finite-field calculations for one deterministic coefficient
triple over $\mathbb F_{101}$, supported by the separate coefficient and prime
universality census for the Hilbert functions. They do not prove an asymptotic
socle formula or a minimal free resolution. The observed structure supplies a
sharper algebraic target for such a proof, but it again preserves an
exponential quotient rather than producing a smaller solver state.
