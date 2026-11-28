# The principal-minor pullback is low degree but exponentially dense

The interpolation projection gives a Boolean polynomial for the square
branch determinant.  If (z_i\in\{0,1\}) records a flip, then

\[
 \Delta(z)=\det(I+\operatorname{diag}(z)K)
 =\sum_{T\subseteq[h]}\det(K_{T,T})\prod_{i\in T}z_i.
\]

Since (K=\operatorname{diag}(c)P) and
(\operatorname{rank}P=q=\lfloor h/2\rfloor), this polynomial has degree at
most (q).  The exact coefficient formula makes it possible to test whether
that degree bound comes with either of the two compressions that would be
algorithmically useful: sparse support or low balanced-cut tensor rank.

It does not in the current panels.  For square sizes six through eleven, the
numbers of nonzero coefficients versus all monomials allowed by the rank bound
are

\[
 41/42,\ 63/64,\ 163/163,\ 256/256,\ 635/638,\ 1013/1024.
\]

The Walsh transform remains exponentially supported as well; at (h=11),
792 of 2,048 coefficients are nonzero over \(\mathbf F_{101}\).

More decisively, view the complete value table of \(\Delta\) as a matrix across
a balanced partition of the branch variables.  At (h=10), 248 of 252 cuts
have the maximum rank 32 and the other four have rank 24.  At (h=11), 461 of
462 cuts have the maximum rank 32 and the remaining cut has rank 28.  Local
changes between value, monomial, and Walsh coordinates are invertible on each
side of a cut, so they do not remove this width.

At binary coverage (h=g\log_2p+O_g(1)), the generic rank-bounded support

\[
 \sum_{j\le h/2}\binom hj
\]

is (2^{h-1+o(h)}=p^{g+o(1)}).  Thus the principal-minor identity is a real
geometric normalization, but ordinary sparse-polynomial interpolation,
Walsh-sparse recovery, or bounded-width tensor contraction does not turn it
into a (p^{o(1)}) search.

These finite panels are diagnostics, not an asymptotic lower bound.  A positive
algorithm can still exploit a recurrence not visible to coefficient support or
balanced flattening rank.

~~~sh
python3 principal_minor_spectrum_control.py |
  cmp - principal_minor_spectrum_control.json
python3 -m py_compile principal_minor_spectrum_control.py
~~~
