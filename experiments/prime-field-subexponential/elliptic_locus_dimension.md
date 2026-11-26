# The elliptic-cover obstruction is a thin hyperelliptic locus

The explicit elliptic-to-hyperelliptic reduction shows that a universal
fixed-genus algorithm would solve elliptic-curve DLP. It does not rule out
an algorithm on a quantified generic or density-one family. This note makes
that distinction explicit.

The moduli space \(\mathcal H_g\) of hyperelliptic curves has dimension
\(2g-1\). Fix the degree

\[
 d=\left\lceil\frac{g+1}{2}\right\rceil
\]

used by the cover construction. A degree-\(d\) rational map is a point of an
open subset of \(\mathbb P^{2d+1}\). Quotienting by the three-dimensional
source action of \(\operatorname{PGL}_2\) leaves dimension \(2d-2\). The
elliptic target contributes its one-dimensional modulus. Therefore the
image of all pairs \((E,h)\) in hyperelliptic moduli has dimension at most

\[
 2d-1.
\]

For genus two this parameter count is not sharp. A degree-two elliptic map
gives an extra involution of the six hyperelliptic branch points. Normalize
that involution to \(t\mapsto-t\). The branch divisor consists generically
of three pairs \(\{\pm a_i\}\); quotienting the three parameters by the
one-dimensional centralizer gives dimension two. Thus the elliptic-cover
locus has codimension at least one inside the three-dimensional
\(\mathcal H_2\).

The resulting bounds are:

| Genus | Cover degree | \(\dim\mathcal H_g\) | Cover-locus dimension at most | Codimension at least |
| ---: | ---: | ---: | ---: | ---: |
| 2 | 2 | 3 | 2 | 1 |
| 3 | 2 | 5 | 3 | 2 |
| 4 | 3 | 7 | 5 | 2 |
| 5 | 3 | 9 | 5 | 4 |
| 6 | 4 | 11 | 7 | 4 |
| 7 | 4 | 13 | 7 | 6 |

All degrees are bounded when \(g\) is fixed. Standard finite-field point
bounds on bounded-degree images therefore give density
\(O_g(p^{-c_g})\) among hyperelliptic moduli points, where \(c_g\) is the
last column. Stack automorphisms and singular boundary points change only
bounded factors or lower-dimensional terms.

Consequently the reduction has two precise implications.

1. A theorem covering every hyperelliptic curve, or one whose exceptional
   set is smaller than this locus, would yield a subexponential ECDLP
   algorithm.
2. A density-one theorem may consistently exclude the entire locus. It must
   state its curve distribution and prove an exceptional-set bound; the
   word "generic" alone is not enough.

This is a scope calculation, not an algorithm or a hardness proof for the
complementary density-one family.

~~~sh
python3 elliptic_locus_dimension.py | cmp - elliptic_locus_dimension.json
~~~
