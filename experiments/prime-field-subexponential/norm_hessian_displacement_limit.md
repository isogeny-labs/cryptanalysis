# A surviving handle: norm Hessians have displacement rank at most four

Write the homogeneous hyperelliptic section parameters as the coefficients of
two polynomials \(B\) and \(C\).  The norm is

\[
 U_{B,C}=wB^2-2vBC-uC^2.
\]

For every output coefficient, its quadratic-form Hessian has two polynomial
coefficient blocks.  Each block is Hankel: its entries depend only on the sum
of the two coefficient indices.  If \(Z_B,Z_C\) are the nilpotent coefficient
shifts and \(Z=Z_B\oplus Z_C\), direct boundary cancellation gives

\[
 \operatorname{rank}(ZQ_d-Q_dZ^{\mathsf T})\le4                 \tag{1}
\]

for every coefficient Hessian \(Q_d\).  The bound is independent of the
section dimension, field size, target divisor, and genus; the three fixed
polynomials \(u,v,w\) change the Hankel symbols but not the two-block boundary
count.

The exact genus-two controls verify (1) for every coefficient at section
dimensions \(r=1,\ldots,20\).  The dimensions through seven use the frozen
split norm relations; dimensions eight through twenty use deterministic
extended planted divisors.  Every measured rank is 0, 2, or 4.

This is useful structure, but not yet an inversion algorithm.  The same
Hessians generate the full matrix algebra from \(r=2\) onward, so low
displacement does not produce a common eigenbasis.  More importantly, an
input matrix with a short displacement generator can acquire large generator
rank under Macaulay multiplication and elimination.  The remaining positive
question is therefore precise: does the degree-\(D\) Macaulay operator of the
whole norm sequence admit a multilevel displacement or tensor representation
of size \(\exp(o(r))\) at the certificate degree \(D=\Theta(r)\)?

A positive answer with an equally compact solve, not just a fast
matrix-vector product, could change the exponent.  The present result proves
only the rank-four input representation and records it as a candidate for
that next step.

~~~sh
python3 norm_hessian_displacement.py | cmp - norm_hessian_displacement.json
python3 -m py_compile norm_hessian_displacement.py
~~~
