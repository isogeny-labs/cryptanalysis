# Singular principal minors are theta-divisor hits

The principal-minor reduction has an exact divisor interpretation.  This
identifies both its useful compression and its remaining asymptotic barrier.

Let the genus-(g) target divisor be represented by (u,v), write
(f=v^2+uw), and use the section

\[
 F=B(y-v)-uC.
\]

It vanishes on the target divisor.  At square saturation choose
(h=r+1) signed points (P_i=(x_i,\epsilon_i y_i)).  The selected evaluation
matrix is singular exactly when a nonzero such section also vanishes at all
(P_i).  Its conjugate norm is

\[
 -\frac{F\,\iota(F)}u
 =wB^2-2vBC-uC^2.
\]

Consequently a singular signing gives

\[
 wB^2-2vBC-uC^2
 =\prod_{i=1}^h(X-x_i)\,R(X),
 \qquad \deg R\le g-1.
\]

The roots of (R), lifted with (F=0), form a residual effective divisor
(E) of degree at most (g-1), including points at infinity when the degree
drops.  The complete zero divisor of (F) gives

\[
 [P_1+\cdots+P_h]+[E]=-[D]
 \quad\text{in }J(\mathbf F_p).
\]

Thus, on the ordinary open set where the divisors have the expected degrees,
the singular-principal-minor search is the preimage problem

\[
 [P_1+\cdots+P_h]\in -[D]-W_{g-1},
\]

where (W_{g-1}\subset J) is the theta divisor of classes having an effective
representative of degree at most (g-1).

## Consequence for random search

For fixed genus,

\[
 \#W_{g-1}(\mathbf F_p)=p^{g-1}+O_g(p^{g-3/2}),\qquad
 \#J(\mathbf F_p)=p^g+O_g(p^{g-1/2}).
\]

If the signed partial sums mix in the Jacobian, the expected singular density
is therefore

\[
 p^{-1}+O_g(p^{-3/2}).
\]

This predicts about (2^h/p) deficient signings.  In the largest exact
genus-two panel, (h=11), the prediction is (2048/101=20.28\ldots) and the
observed count is 22.  The observation is a mixing diagnostic, not a proof of
equidistribution.

The interpretation also prevents a false conclusion.  Finding a singular
square signing only produces a free residual divisor of degree (g-1).  If
the final (g-1) abscissae were fixed in advance, the residual must still
match them; this restores the missing codimension.  In the exact panels only
one or two of the many singular square signings extend through the supplied
remaining slots.

## Algorithmic limit

Uniform probing can now find a theta hit in expected \(\widetilde O(p)\)
group operations, independent of (g), but that does not solve a DLP or
collect a complete linear system in the same cost.  A (p^{o(1)}) algorithm
would need a structured method for finding a theta-preimage among the binary
signed sums; rank, self-adjointness, and random sampling alone do not supply
one.

The companion control reconstructs (B,C,R), lifts the residual divisor, and
checks the Jacobian identity for every deficient signing in all ten panels:

~~~sh
python3 principal_minor_jacobian_equivalence.py |
  cmp - principal_minor_jacobian_equivalence.json
python3 -m py_compile principal_minor_jacobian_equivalence.py
~~~
