# Two-line list recovery must be projective and union-aware

The interleaved evaluation-code formulation places each local symbol
\((B(x_i),C(x_i))\in\mathbb F_p^2\) in a union of two known lines.  This is
more succinct than an ordinary point list, but neither standard subspace
erasure decoding nor ordinary affine-code list recovery can be used as a
black box.

## Taking the span erases the constraint

At a split unramified fiber the two allowed lines are

\[
 L_{i,+}=\{(z,t_i^+z):z\in\mathbb F_p\},\qquad
 L_{i,-}=\{(z,t_i^-z):z\in\mathbb F_p\},
\]

with \(t_i^+\ne t_i^-\).  Therefore

\[
 \operatorname{span}(L_{i,+}\cup L_{i,-})=\mathbb F_p^2.
\]

Any decoder that accepts one subspace per coordinate and replaces the union
by its span sees a complete erasure at every coordinate.  Retaining one line
requires choosing a sign, which restores the \(2^m\) branch space.  Thus
sum-rank error/erasure decoders for a single supplied row or column subspace
do not directly address this problem.

## Affine output has a mandatory factor \(p\)

The product code \(RS_b\times RS_c\) is linear, and every local allowed set is
homogeneous.  If a nonzero pair \((B,C)\) is valid, then

\[
 (\lambda B,\lambda C),\qquad \lambda\in\mathbb F_p^*,
\]

is also valid.  These are the same projective section but \(p-1\) distinct
affine codewords.  The zero codeword is locally valid as well, although it is
not a section.

At the oversampled binary coverage scale

\[
 m=g\log_2p+O(\sqrt{\log p}),
\]

the expected number of projective answers is \(p^{o(1)}\), while any decoder
that explicitly lists affine codewords must output

\[
 p^{1+o(1)}
\]

vectors.  This output-size cost alone violates the end-to-end target.

The exact genus-two controls reconstruct the homogeneous section kernel for
all seven split-norm panels.  Each chosen sign pattern has rank \(r\) in
\(r+1\) homogeneous coefficients, hence exactly 101 affine kernel vectors,
100 nonzero representatives, and one projective orbit.

## Projective normalization removes the output inflation, but not the union

Choose a nonzero coefficient and normalize it to one.  There are only
\(r+1=O(\log p)\) charts, or a random linear functional misses a fixed
projective answer with probability \(1/p\).  In one chart the scalar orbit is
removed and the expected output returns to \(p^{o(1)}\).

The price is that the message set is now an affine slice rather than a linear
code.  Each coordinate remains a union of two affine hyperplanes.  Taking
their affine span again removes the constraint, while multiplying their two
linear equations produces the original quadratic norm system.

Consequently the precise positive target is a **projective union-of-subspaces
decoder** for the paired Reed--Solomon evaluation map.  It must:

1. preserve a union of two lines at every coordinate without branching;
2. quotient scalar orbits without enumerating them;
3. exploit the shared RS evaluation structure strongly enough to work at
   redundancy \(g=O(1)\).

No located subspace-list-recovery or interleaved error/erasure theorem has
these three properties.  This is a scope statement about direct theorem
application, not a lower bound on a new projective decoder.

[Exact scaling control](projective_scaling_control.py) ·
[Frozen result](projective_scaling_control.json)

```sh
python3 projective_scaling_control.py | cmp - projective_scaling_control.json
```
