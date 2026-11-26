# Semi-regular branch systems retain a linear solving degree

The transverse oversampling controls match the standard semi-regular Hilbert
prediction.  That prediction gives a quantitative barrier for direct
Macaulay inversion in both hyperelliptic and higher-degree split-fiber
models.

## Binary case

Let \(r\) be the affine section-parameter count and let the genus excess be
fixed at \(g\), so there are \(m=r+g\) quadratic branch equations.  The
semi-regular Hilbert series is governed by

\[
 \frac{(1-z^2)^m}{(1-z)^r}
 =(1+z)^m(1-z)^g.                                  \tag{1}
\]

The coefficient of degree \(D\) in (1) is the fixed-order Krawtchouk value

\[
 \sum_{j=0}^g(-1)^j\binom gj\binom m{D-j}.
\]

For fixed \(g\), its first sign change occurs at

\[
 D=\frac r2+O_g(\sqrt r).
\]

The usual affine witness degree is one past that sign change.  This predicts
degrees 4, 4, and 5 at \(r=4,5,6\), exactly the one-root values measured in
the transverse controls.  Planting up to ten roots did not change the
five- and six-variable values.

At \(D=r/2+o(r)\), the Macaulay column count is

\[
 \binom{r+D}{r}
 =2^{(1.377443751\ldots+o(1))r}.                  \tag{2}
\]

Exact signed-fiber coverage has

\[
 r=g\log_2p+o(\log p),
\]

so (2) is

\[
 p^{1.377443751\ldots g+o(1)},
\]

not \(p^{o(1)}\).

## Degree-\(d\) split fibers

For a product of \(d\) affine branch evaluations per equation, the analogous
series is

\[
 \frac{(1-z^d)^m}{(1-z)^r}
 =(1+z+\cdots+z^{d-1})^m(1-z)^g.                  \tag{3}
\]

At the coverage threshold

\[
 m=\frac{g\log p}{\log d}+O_g(1),\qquad r=m-g,
\]

the first sign in (3) occurs near \((d-1)r/2\).  Stirling's formula gives the
following asymptotic ledger:

| branch degree \(d\) | witness degree / \(r\) | \(\log_2\) columns / \(r\) | column exponent / genus |
|---:|---:|---:|---:|
| 2 | 0.5 | 1.377444 | 1.377444 |
| 3 | 1.0 | 2.000000 | 1.261860 |
| 4 | 1.5 | 2.427376 | 1.213688 |

Larger fibers reduce the number of variables enough to improve the positive
constant, but they do not make it vanish.  In this semi-regular model, even
letting \(d\) grow through the fixed choices available at genus \(g\) only
moves the exponent toward a positive multiple of \(g\).

## Exact scope

Semi-regularity is a model, not a theorem for the curve-derived norm system.
The calculation therefore does not prove an index-calculus lower bound.  It
does prove what a successful direct algebraic attack must exhibit:

- curve-specific syzygies appearing at degree \(o(r)\); or
- a root-extraction method that avoids the full Macaulay quotient despite a
  linear witness degree.

Additional representations alone are not such a mechanism in the measured
panels.  The next useful experiment should search explicitly for low-degree
syzygies forced by the Vandermonde/Hankel evaluation structure and compare
them with random branch-product systems of the same dimensions.

[Binary Krawtchouk ledger](semiregular_krawtchouk_ledger.py) ·
[Frozen binary ledger](semiregular_krawtchouk_ledger.json) ·
[Degree-2--4 ledger](semiregular_branch_degree_ledger.py) ·
[Frozen degree ledger](semiregular_branch_degree_ledger.json)

~~~sh
python3 semiregular_krawtchouk_ledger.py | cmp - semiregular_krawtchouk_ledger.json
python3 semiregular_branch_degree_ledger.py | cmp - semiregular_branch_degree_ledger.json
~~~
