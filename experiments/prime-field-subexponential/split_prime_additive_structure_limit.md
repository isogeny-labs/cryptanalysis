# Additive-structure control for split-prime orientations

The fixed-residual reduction leaves a subset-sum instance whose increments are
the doubled Abel--Jacobi point classes \(-2P_i\).  The reduction itself does not
decide whether these particular group elements are easier than generic subset
sum.  This control compares the seven planted norm panels with two ensembles:

1. independent uniform elements of the effective subgroup \(2J\); and
2. doubled classes of distinct random rational curve points.

For every instance it exhausts all subsets and records the number of distinct
sums, collision pairs, maximum bucket, the balanced-layer collision profile,
and the minimum Hamming support of a signed relation.  The last statistic is
exact: two colliding subset masks differ by a relation with coefficients in
\(\{-1,0,1\}\), and cancelling their common coordinates gives its support.

The toy Jacobian over \(\mathbf F_{101}\) has order
\(9758=2\cdot7\cdot17\cdot41\) and is cyclic.  An explicit generator permits
the diagnostic to use integer coordinates, but finding those coordinates is
an exhaustive small-field setup step and is not part of a proposed algorithm.
Both comparison ensembles are restricted to the order-4879 subgroup \(2J\),
so the common parity quotient is not mistaken for useful structure.

There is one exact curve-specific anti-collision fact.  If the full Jacobian
has odd order and \(P_1,\ldots,P_m\) are distinct affine points with distinct
abscissae, then for every \(k\le g\) the sums

\[
 \sum_{i\in S}[P_i-\infty],\qquad |S|=k,
\]

are all distinct.  Each sum is already a reduced degree-\(k\) Mumford divisor,
whose representative is unique.  Multiplication by two is injective at odd
order, so the same holds for the orientation increments \(-2P_i\).  Thus the
curve geometry suppresses, rather than creates, exact collisions in the first
\(g\) weight layers.  The control verifies both the undoubled and doubled
statements in every panel.  Its toy Jacobian has even order, so the doubled
check is empirical there; the theorem applies directly after the stated
odd-order hypothesis, while projection to a proper subgroup additionally
requires excluding collisions in the killed cofactor.

The complete 48-point split pool makes that caveat explicit.  Its 1,128
undoubled two-point sums are all distinct.  Doubling leaves 1,066 values and
62 collision pairs; every bucket has size at most two, every collision uses
four distinct points, and the two undoubled sums differ by the unique rational
two-torsion class.  These are precisely cofactor collisions, not a growing
quotient filtration.  A uniformly sampled nine-slot set retains only
\(62(9)_4/(48)_4=217/5405<0.041\) such pair collisions in expectation.
Thus the finite cofactor effect is too sparse even to appear typically in the
largest planted panel.  Asymptotically, extending this conclusion to a chosen
prime-order component requires a bound on low-support relations landing in
its killed cofactor; it is automatic only when the full group has odd order.

That extension has a simple fixed-weight bound.  Let \(S\) contain \(n\)
distinct nonconjugate points, let \(k\le g\), and let
\(\phi:J\to H\) have kernel \(K\).  The Abel map is injective on the
\(k\)-subsets of \(S\).  For a fixed subset \(D\) and fixed nonzero
\(\kappa\in K\), there is therefore at most one subset \(E\) with

\[
 [E-k\infty]=[D-k\infty]+\kappa.
\]

Consequently the number of unordered collisions after applying \(\phi\) is
at most

\[
 \frac{|K|-1}{2}\binom nk.
\]

Two distinct \(k\)-subsets have a union of at least \(k+1\) points.  A
uniform random \(m\)-point subpool therefore retains at most

\[
 \frac{|K|-1}{2}\binom nk\frac{(m)_{k+1}}{(n)_{k+1}}
 =O_g\!\left(\frac{|K|m^{k+1}}n\right)
\]

collisions in expectation.  With \(n\asymp p\), fixed \(g\),
\(m=O_g(\log p)\), and \(|K|=p^{o(1)}\), this tends to zero.  Thus a small
cofactor does not restore exact early-layer birthday merging after projection
to the cryptographic component.  The statement is deliberately limited to
fixed weights \(k\le g\); it does not control the middle layers where the
orientation problem becomes density-one subset sum.

Across the panels, the constructed instances lie inside the ranges of both
matched ensembles for global and balanced subset-sum collisions.  Their first
signed relations, when present, likewise have ordinary matched-control
support.  There is no observed excess of collisions, small buckets, or
low-weight relations that a generalized-birthday, collision-merging, or
sparse-relation method could exploit.  The finite control therefore gives no
positive route around orientation search.

This is not an average-case hardness proof.  It only rules out the measured
small-field signatures, and the construction could have a subtler asymptotic
property invisible at \(p=101\).  A positive algorithm still must exploit an
explicit algebraic invariant of the curve-derived increments, not merely their
membership in \(2J\) or their origin as doubled rational points.

~~~sh
python3 split_prime_additive_structure.py |
  cmp - split_prime_additive_structure.json
python3 -m py_compile split_prime_additive_structure.py
~~~
