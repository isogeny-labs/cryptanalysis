# Quotienting the fixed-rank conjugate center

The hyperelliptic branch relation supplies more structure than an arbitrary
two-list instance.  At a selected split abscissa, write

\[
 t_i^\pm=\frac{\pm y_i-v(x_i)}{u(x_i)}
        =a_i\pm s_i,
\qquad
 a_i=-\frac{v(x_i)}{u(x_i)},\quad
 s_i=\frac{y_i}{u(x_i)}.
\]

Both branches satisfy

\[
 u(x_i)t^2+2v(x_i)t-w(x_i)=0,
\qquad f-v^2=uw.
\]

For \(U=\prod_i(X-x_i)\), set
\(\lambda_i=1/U'(x_i)\).  The signed-Hankel formulation uses the moments

\[
 M_e(t)=\sum_i\lambda_i t_i x_i^e.
\]

The sign-independent center \(M_e(a)\) obeys the order-\(g\) recurrence

\[
 \sum_{j=0}^{g}u_jM_{e+j}(a)
 =-\sum_i\lambda_i v(x_i)x_i^e=0
\]

through the whole required moment window.  The final equality is the
Lagrange leading-coefficient identity, since the polynomial on the right has
degree below \(m-1\).  Therefore the center Hankel matrix \(A\) has rank at
most \(g\), independently of the growing section dimension.

## Fixed-genus quotient

Write the full matrix as

\[
 H(\epsilon)=A+S(\epsilon),
\]

where \(S(\epsilon)\) contains the signed \(y_i/u(x_i)\) moments.  Its size
is

\[
 (q+g-1)\times q,\qquad q=b+1.
\]

When \(\operatorname{rank}A=g<q\), take a left-nullspace matrix \(P\) for
\(A\).  It has exactly \(q-1\) rows.  Every desired kernel vector must obey

\[
 P S(\epsilon)z=0.
\]

If this projected matrix has rank \(q-1\), it supplies a unique projective
candidate \(z(\epsilon)\) for every signing.  The remaining condition
\((A+S(\epsilon))z(\epsilon)=0\) has only \(g\) independent residual
coordinates because \(S(\epsilon)z(\epsilon)\) already lies in the
column space of \(A\).

The exact genus-two controls verify:

- all local quadratic branch identities;
- every required center recurrence;
- center rank exactly two once \(q\ge2\);
- projected rank \(q-1\) for all 128, 256, and 512 signings at
  \(r=5,6,7\);
- exactly one residual-zero signing in each panel.

This replaces a growing rectangular MinRank test by a canonical cofactor
kernel plus \(g\) residual equations.  It does not yet change the asymptotic
exponent.  The cofactors of \(PS(\epsilon)\) have degree \(q-1\) in the
signs, and the resulting residuals have degree \(q\).  Their measured
multilinear supports are essentially maximal:

| slots | \(q\) | maximum nonconstant support through degree \(q\) | residual supports |
| ---: | ---: | ---: | ---: |
| 7 | 3 | 63 | 63, 62 |
| 8 | 3 | 92 | 91, 92 |
| 9 | 4 | 255 | 253, 252 |

Thus explicit Boolean expansion recreates almost every available monomial,
and enumeration still costs \(2^m=p^{g+o(1)}\).

The truth-table tensor flattenings also reach the ordinary central-cut
width.  The two residuals have identical cut-rank profiles in each panel:

| slots | prefix/suffix cut ranks |
| ---: | --- |
| 7 | \(2,4,8,8,4,2\) |
| 8 | \(2,4,8,10,8,4,2\) |
| 9 | \(2,4,8,16,16,8,4,2\) |

In particular the odd panels attain full rank at the central cuts.  A direct
tensor-train or ordered branching-program contraction therefore has width
\(2^{m/2}\) on these controls, matching meet-in-the-middle rather than
\(p^{o(1)}\).  A positive continuation must solve the \(g\) residual
determinant circuits using structure beyond monomial sparsity or the natural
slot ordering.

[Exact control](conjugate_hankel_quotient.py)

~~~sh
python3 conjugate_hankel_quotient.py |
  cmp - conjugate_hankel_quotient.json
~~~
