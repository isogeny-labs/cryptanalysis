# Free-residual theta hits do not improve the end-to-end exponent

A singular square signing produces a residual effective divisor of degree
(g-1).  That is weaker than the fixed-tail binary inverse: its support is not
chosen from the factor base in advance.  Charging this distinction removes the
apparent (\widetilde O(p)) advantage.

Let the rational-point factor base have size (B=p^\beta), and suppose one
theta hit costs (p^\sigma).  Under the standard uniform-support model, all
(g-1) residual points lie in the factor base with probability

\[
 (B/p)^{g-1}=p^{-(g-1)(1-\beta)}.
\]

Collecting (B) sparse relations therefore has exponent

\[
 C(\beta)=\sigma+(g-1)(1-\beta)+\beta
 =\sigma+g-1-(g-2)\beta.
\]

Sparse black-box linear algebra on (B) columns has exponent (L(\beta)=2\beta).
For (0\le\sigma\le1), balancing the two gives

\[
 \beta=\frac{\sigma+g-1}{g},\qquad
 E_{\theta}(\sigma)=\frac{2(\sigma+g-1)}g.
\]

Two consequences are immediate.

1. The available random theta probe has \(\sigma=1\), hence
   \(\beta=1\) and total exponent (2) in every genus.
2. Even a hypothetical (p^{o(1)}) theta-hit oracle has \(\sigma=0\) and
   total exponent (2-2/g).  This is exactly the existing genus-three-through-
   seven baseline, and equals the genus-two rho exponent.

The equality is not a new algorithm: it is a ledger for the conventional
uniform-residual and sparse-matrix route.  Correlated residuals, a new
large-prime recombination theorem, or a logarithm-recovery method that bypasses
the factor-base matrix lie outside it.

For the binary program, the conclusion is sharper.  Improving the search for
**some** singular square signing cannot establish the requested end-to-end
subexponential algorithm.  One must either force the residual divisor onto the
remaining prescribed slots in (p^{o(1)}) work, or recover logarithms without
a polynomial-size factor base and its linear algebra.

~~~sh
python3 theta_relation_exponent_ledger.py |
  cmp - theta_relation_exponent_ledger.json
~~~
