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
