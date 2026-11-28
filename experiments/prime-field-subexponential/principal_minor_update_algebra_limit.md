# Rank-one branch updates generate the full matrix algebra

The rank-(q) determinant lemma writes the principal-minor pullback as

\[
 \Delta(S)=\det\left(I_q+\sum_{i\in S}R_i\right),
 \qquad R_i=a_i b_i^{T},
 \qquad q=\lfloor h/2\rfloor.
\]

This form would be algorithmically useful if the updates commuted, were
simultaneously triangularizable into bounded blocks, or generated an algebra
of dimension (o(q^2)).  The exact curve updates do none of these in the ten
panels.

There is a simple certificate for full closure.  For (q) selected updates,
if the (a_i) are a basis, the (b_i) are a dual-space basis, and every
pairing (b_i^Ta_j) is nonzero, then

\[
 R_iR_j=(b_i^Ta_j)a_i b_j^T.
\]

The (q^2) products therefore span (M_q(\mathbf F_p)).  This direct
certificate holds for 196 of 252 five-update subsets at (h=10), and 378 of
462 at (h=11).  The remaining subsets are not low-algebra exceptions: exact
closure shows that every balanced subset in both panels still generates the
full 25-dimensional algebra.

Across all square sizes two through eleven:

- the natural first (q) updates generate all of (M_q);
- every balanced update subset generates all of (M_q);
- the generator span has dimension only (2q-1), but its associative closure
  has dimension (q^2); and
- all update pairs fail to commute except one pair at (h=8), one at (h=10),
  and one at (h=11).

Thus the low-rank determinant formula cannot be scalarized by a common
eigenbasis or a curve-independent bounded block decomposition in these
controls.  Meet-in-the-middle on arbitrary (q\times q) partial sums still
has the exponential branch frontier.  This is a finite structural diagnostic,
not an asymptotic lower bound or a claim against a different nonlinear
normal form.

~~~sh
python3 principal_minor_update_algebra.py |
  cmp - principal_minor_update_algebra.json
python3 -m py_compile principal_minor_update_algebra.py
~~~
