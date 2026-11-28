# Half-rank scaled projections already contain modular Subset Sum

The interpolation reduction produces

\[
 \det((I+K)_{S,S}),\qquad K=DP,qquad P^2=P,
\]

with (P) diagonally self-adjoint and of rank about half its dimension.  Those
properties alone cannot yield a fast singular-subset algorithm: even the
smaller class with (P) a symmetric projection contains modular Subset Sum.

Let (w_1,\ldots,w_n,T\in\mathbf F_p^*\), with (p\nmid n), and put

\[
 a_i=-w_i/T,qquad
 P_0=\frac1n\mathbf1\mathbf1^T,qquad
 D_0=\operatorname{diag}(na_i).
\]

Then (P_0=P_0^T=P_0^2) and has rank one.  The matrix
(K_0=D_0P_0) has constant row (i) equal to (a_i).  For every subset
(S\subseteq[n]), the matrix determinant lemma gives

\[
 \det((I+K_0)_{S,S})
 =1+\sum_{i\in S}a_i
 =1-\frac1T\sum_{i\in S}w_i.
\]

It is singular exactly when the selected weights sum to (T) modulo (p).
Moreover (K_0) is diagonally self-adjoint: multiplying row (i) by
(a_i^{-1}) gives the all-ones matrix.

The rank ratio can be made identical to the curve control.  Set

\[
 P=P_0\oplus I_{n-2},\qquad D=D_0\oplus I_{n-2}.
\]

Now (P) has ambient dimension (2n-2) and rank (n-1), exactly half.  A
selected padding coordinate contributes a factor two to the principal
determinant, which is nonzero in odd characteristic.  Hence padding introduces
no spurious singular subset.

This is an exact algebraic reduction from modular Subset Sum, without an
average-case hardness claim.  It is consistent with the broader literature:
general rank-one matrix-polytope singularity and P-matrix recognition have
classical hardness reductions, while interlace-polynomial evaluations that
sum principal-submatrix ranks are generally #P-hard.  Those results concern
larger matrix classes and are context, not proofs about the curve-derived
family.  See [Coxson's rank-one-polytope reduction](https://www.math.ucdavis.edu/~deloera/MISC/LA-BIBLIO/trunk/Morris/Morris1.pdf)
and [Bläser--Hoffmann on interlace-polynomial complexity](https://arxiv.org/abs/0707.4565).

The conclusion is sharply scoped: idempotence, half rank, diagonal
self-adjointness, and the principal-minor formula are insufficient.  Any
positive hyperelliptic algorithm must use the Lagrange/Vandermonde
interpolation entries of (P) beyond these abstract matrix properties.

~~~sh
python3 scaled_projection_subset_sum.py |
  cmp - scaled_projection_subset_sum.json
python3 -m py_compile scaled_projection_subset_sum.py
~~~
