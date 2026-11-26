# Norm inversion is a paired hyperplane-transversal problem

After quotienting the scalar orbit, the binary split-fiber inverse has an
exact linear-algebra formulation.  Let \(d=r+1\), let
\(m=r+g=d+g-1\), and write the two evaluation rows at slot \(i\) as
\(a_{i,+},a_{i,-}\in\mathbb F_p^d\).  Recovering the section is equivalent
to finding a projective point \([z]\in\mathbb P^{d-1}(\mathbb F_p)\) such
that

\[
 (a_{i,+}z)(a_{i,-}z)=0\qquad(1\le i\le m).
\]

Equivalently, choose one row from every pair so that the resulting
\(m\times d\) matrix is non-spanning.  In coding language, the evaluation
word of \(z\) has at least one zero in every coordinate pair.  Thus the
missing decoder can be stated as any of three identical tasks:

1. projective list recovery from unions of two hyperplanes;
2. a non-spanning transversal of \(m\) vector pairs;
3. a paired-zero codeword in the structured evaluation code.

## Fixed excess is real but does not by itself remove the branch space

The row excess is exactly

\[
 m-d=g-1,
\]

which is fixed as \(p\to\infty\).  Consequently non-spanning can be tested
by only

\[
 \binom{m}{d}=\binom{d+g-1}{g-1}=O_g(d^{g-1})
\]

maximal minors once a signing is supplied.  This is a useful compression of
the rank certificate, but it is not an inversion algorithm: each determinant
is a degree-\(d\) multilinear polynomial in the sign choices.  In the Hankel
coordinates, a central maximal minor has
\(\binom{m}{m/2+O_g(1)}=2^{m-o(m)}\) nonzero sign monomials.  Expanding the
polynomial therefore recreates the full phase space.

The exact genus-two panels make the distinction concrete.  For
\(r=1,\ldots,7\), exhaustive enumeration finds exactly one non-spanning
signing and exactly one projective kernel.  Projectivization removes the
\(p-1\) scalar copies, but it does not merge multiple signings in these
instances.  The row excess is one in every panel, while the number of
signings grows from 8 to 512.

This formulation isolates a narrower positive target: an algorithm
polynomial or subexponential in \(d=\Theta(\log p)\), with fixed-parameter
dependence on \(g-1\), for the **Vandermonde/Reed--Solomon row pairs arising
from the curve**.  Generic hyperplane-transversal hardness results over the
reals do not directly settle this finite-field, homogeneous, structured
case.  Conversely, fixed excess alone is not evidence for tractability; the
algorithm must use the shared evaluation structure without expanding the
sign minors.

## Generic fixed excess already contains Subset Sum

There is also a direct prime-field reduction explaining why the row excess
cannot be the only parameter.  Given positive integers
\(a_1,\ldots,a_n,b\) with total less than \(p\), work in dimension \(n+1\)
and give item \(i\) the row pair

\[
 v_i=(a_i,e_i),\qquad w_i=(0,e_i).
\]

Add the row \(u=(-b,-1,\ldots,-1)\).  For a selection encoded by
\(s_i\in\{0,1\}\), adding the selected item rows to \(u\) transforms the
square determinant into

\[
 \det(v_i\mathbin{\mathrm{or}}w_i;\,u)
   =\pm\left(\sum_i s_i a_i-b\right).
\]

The selected rows are therefore non-spanning over \(\mathbb F_p\) exactly
when the integer subset sum equals \(b\).  Represent \(u\) by a pair of
distinct nonzero scalar multiples and add a second redundant scalar pair.
The resulting instance has \(m=d+1\), hence row excess one, without changing
the decision problem.  The exact controls verify the determinant equivalence
on yes- and no-instances over \(\mathbb F_{101}\).

This is a hardness scope statement, not a lower bound for the curve rows.
The two redundant pairs are projectively repeated, whereas the two local
curve branches give distinct hyperplanes, and arbitrary Subset-Sum rows do
not have Reed--Solomon evaluation structure.  Moreover, ordinary NP-hardness
does not by itself exclude \(p^{o(1)}\) time.  Composed with the standard
linear-size 3-SAT-to-Subset-Sum reduction and a prime of
\(O(\text{instance size})\) bits, it gives a conditional
\(2^{o(n)}\)-time obstruction under randomized ETH for a generic paired
solver.  It leaves the structured curve family completely open.

The reduction is the homogeneous finite-field analogue of the two-point
hyperplane-transversal construction of
[Bergold et al.](https://doi.org/10.4230/LIPIcs.SWAT.2022.16).

[Exact curve control](paired_hyperplane_control.py) ·
[Subset-Sum control](paired_subset_sum_control.py)

```sh
python3 paired_hyperplane_control.py |
  cmp - paired_hyperplane_control.json
python3 paired_subset_sum_control.py |
  cmp - paired_subset_sum_control.json
```
