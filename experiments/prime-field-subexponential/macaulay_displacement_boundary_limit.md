# The affine Macaulay truncation has an exponential displacement boundary

The homogeneous norm Hessians have block-Hankel displacement rank at most
four.  A standard affine Macaulay solve dehomogenizes one section coefficient
and truncates multiplier monomials at certificate degree \(D\).  This
operation creates a large boundary that the rank-four input description does
not control.

Let \(F\) be one dehomogenized quadratic norm equation with nonzero constant
coefficient \(c\), and let \(M_D\) contain the rows \(x^\alpha F\) for
\(|\alpha|\le D-2\).  Compare multiplication of row multipliers by \(x_j\)
with multiplication of output monomials by \(x_j\).  They commute for
\(|\alpha|<D-2\).  On the top layer \(|\alpha|=D-2\), quadratic terms leave
the truncation while the constant term contributes

\[
 c x^{\alpha+e_j}.
\]

These monomials are distinct as \(\alpha\) varies.  Hence a single variable
displacement has rank at least

\[
 B(r,D)=\binom{r+D-3}{r-1}.                         \tag{1}
\]

All seven exact split panels contain a norm equation with nonzero constant.
At their measured certificate degrees, the boundary ranks are exactly

\[
 1,2,3,10,15,56,84
\]

for \(r=1,\ldots,7\), matching (1).  If \(D=\delta r+O(1)\) with
\(\delta>0\), Stirling's formula gives

\[
 \log B(r,D)
 =r\big((1+\delta)\log(1+\delta)-\delta\log\delta\big)+o(r),
\]

so the ordinary truncated displacement generator is exponential at the
semi-regular certificate degree.

This does not negate the rank-four homogeneous Hessian theorem.  It shows
that a direct affine Toeplitz/Hankel Macaulay solve loses that compression at
the top monomial simplex boundary.  A surviving algorithm must keep a
homogeneous graded recurrence, quotient the boundary implicitly, or prove a
different multilevel compression after syzygies are imposed.  The result is
a limit on the standard truncated displacement construction, not a lower
bound on every structured polynomial-system solver.

~~~sh
python3 macaulay_displacement_boundary.py |
  cmp - macaulay_displacement_boundary.json
python3 -m py_compile macaulay_displacement_boundary.py
~~~
