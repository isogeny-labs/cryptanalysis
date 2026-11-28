# The interpolation projection is Cauchy-like, but so is the Subset Sum gadget

Let (X=\operatorname{diag}(x_1,\ldots,x_h)).  The curve-derived flip matrix
(K=\operatorname{diag}(c)P) satisfies

\[
 \operatorname{rank}(XK-KX)\le2.
\]

One way to see the identity is to write the range of (P) as the weighted
Vandermonde evaluations of polynomials of degree below (q).  The
self-adjoint projection kernel is a reproducing kernel for a Hankel moment
functional.  Its Christoffel--Darboux numerator is a difference of two outer
products, so multiplication by (x) has displacement rank two.  Diagonal row
scaling commutes with (X) and preserves the bound.

Every principal submatrix inherits the same generators, so its displacement
rank is also at most two.  All ten exact curve panels, of square sizes two
through eleven, attain full displacement rank two.  At (h=11), 2,035 of
2,048 principal submatrices have rank-two displacement; the remaining 13
have rank zero.

This gives fast structured linear algebra for a **specified** signing, but it
does not solve the signing search.  The half-rank Subset Sum construction has
the same invariant.  Give its hard rank-one block distinct diagonal nodes.
The commutator of the all-ones projection with that diagonal is the difference
of two outer products, while the identity padding commutes with the nodes.
All three exhaustive gadgets therefore have displacement rank two, and every
one of their principal submatrices has displacement rank at most two.

Thus idempotence, self-adjointness, half rank, and Cauchy-like displacement
rank two still contain modular Subset Sum.  A positive algorithm must exploit
stronger relations tying the displacement generators to the hyperelliptic
polynomials (u,v,f) and the Lagrange residue weights.  Faster evaluation of
one determinant does not change the (2^h) search frontier.

~~~sh
python3 interpolation_projection_displacement.py |
  cmp - interpolation_projection_displacement.json
python3 scaled_projection_subset_sum.py |
  cmp - scaled_projection_subset_sum.json
python3 -m py_compile interpolation_projection_displacement.py
~~~
