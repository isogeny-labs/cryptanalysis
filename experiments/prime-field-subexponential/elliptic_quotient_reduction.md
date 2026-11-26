# Why a universal fixed-genus theorem would include elliptic DLP

A classical \(p^{o(1)}\) algorithm that works for every smooth genus-\(g\)
curve over growing prime fields would be stronger than a generic-curve
result. Degree-two covers transfer elliptic-curve discrete logarithms into
genus-\(g\) Jacobians. Consequently a universal theorem would imply a
classical subexponential algorithm for elliptic-curve DLP.

This reduction does not rule out an algorithm valid on an open dense family
of curves. The covers below lie on a special elliptic-quotient locus, which
a genuinely generic theorem may exclude.

## Degree-two cover construction

Let \(E/\mathbb F_p\) be an elliptic curve in odd characteristic. Choose a
separable quadratic extension of function fields

\[
 \mathbb F_p(E)\subset \mathbb F_p(E)(\sqrt h)
\]

whose branch divisor has \(r=2g-2\) geometric points and is stable under
Frobenius. For fixed \(g\) and sufficiently large \(p\), such \(h\) can be
found by sampling bounded-degree functions and rejecting repeated or
incorrectly sized branch divisors. Let \(C\) be the smooth projective curve
of the extension and let

\[
 \pi:C\longrightarrow E
\]

be the resulting degree-two map.

Riemann--Hurwitz gives

\[
 2g(C)-2
 =2(2g(E)-2)+r
 =r=2g-2,
\]

so \(g(C)=g\). All construction and divisor-arithmetic costs are polynomial
in \(\log p\) when \(g\) is fixed.

## DLP transfer

The map induces pullback and norm homomorphisms

\[
 \pi^*:J_E\longrightarrow J_C,\qquad
 \pi_*:J_C\longrightarrow J_E
\]

satisfying

\[
 \pi_*\pi^*=[2]\quad\text{on }J_E=E.
\]

Let \(P\in E(\mathbb F_p)\) have odd prime order \(\ell\), and suppose
\(Q=[a]P\). Then

\[
 \pi^*Q=[a]\pi^*P.
\]

Moreover, \(\pi^*\) is injective on \(\langle P\rangle\): if
\(\pi^*([b]P)=0\), applying \(\pi_*\) gives \([2b]P=0\), hence
\(b=0\bmod\ell\). A DLP oracle in \(J_C(\mathbb F_p)\) therefore recovers
\(a\bmod\ell\). Final verification can be performed back on \(E\).

The Jacobian is isogenous to

\[
 J_C\sim E\times\operatorname{Prym}(C/E),
\]

which makes the embedded elliptic factor explicit.

## Hyperelliptic scope

Every smooth genus-two curve is hyperelliptic. Therefore a uniform
subexponential algorithm for all genus-two hyperelliptic Jacobians would
already imply subexponential elliptic-curve DLP through the construction
above with two branch points.

There is also a direct affine model. Write

\[
 E:y^2=x^3+Ax+B
\]

and choose \(a\in\mathbb F_p\) such that \(f(a)=a^3+Aa+B\) is a nonzero
square. Then

\[
 C:Y^2=f(Z^2+a),\qquad
 \pi(Z,Y)=(Z^2+a,Y)
\]

is a degree-two map from a smooth genus-two hyperelliptic curve. Its two
branch points are \((a,\pm\sqrt{f(a)})\) on \(E\); the two points at infinity
of the even-degree model lie over the point at infinity of \(E\). The exact
control enumerates every rational fiber, reconstructs
\(\#J_C(\mathbb F_p)\) from point counts over \(\mathbb F_p\) and
\(\mathbb F_{p^2}\), and verifies that \(\#E(\mathbb F_p)\) divides it.
[Implementation](elliptic_cover_control.py) ·
[Frozen result](elliptic_cover_control.json)

## Uniform hyperelliptic covers in every fixed genus

The transfer can in fact be kept hyperelliptic in every fixed genus. Put

\[
 d=\left\lceil\frac{g+1}{2}\right\rceil,
 \qquad k=2g+2-3d.
\]

Then \(0\le k\le d\) and \(k\equiv d\pmod2\). For \(k=0\), take
\(h_0(t)=t^d\). For \(k>0\), take

\[
 h_0(t)=\frac1{D(t)},\qquad
 D(t)=t^{d-k+1}\prod_{i=1}^{k-1}(t-i).
\]

The map \(h_0:\mathbb P^1\to\mathbb P^1\) has degree \(d\) and exactly
\(k\) poles of odd order. The first pole has order \(d-k+1\), which is odd,
and the remaining poles are simple. When \(k=0\), the unique pole of
\(t^d\) has even order.

Write \(h=h_0+c=N/D\). There are only \(O_g(1)\) shifts
\(c\in\mathbb F_p\) for which a root of \(f=x^3+Ax+B\) is a critical value
of \(h\). For fixed \(g\) and sufficiently large \(p\), scanning
\(O_g(1)\) shifts therefore finds one for which \(h\) is unramified above
all three roots. Factor

\[
 D=S^2K,
\]

where \(K\) is the squarefree product of the \(k\) odd-order poles, and put

\[
 G=N^3+AND^2+BD^3,
 \qquad H=GK.
\]

The polynomial \(G\) has \(3d\) simple roots and is coprime to \(K\).
Consequently \(H\) is squarefree of degree

\[
 3d+k=2g+2.
\]

Thus

\[
 C:Z^2=H(t)
\]

is a smooth hyperelliptic curve of genus \(g\). The identity

\[
 D G=S^2H
\]

gives the degree-\(d\) morphism

\[
 \pi:C\longrightarrow E,
 \qquad
 (t,Z)\longmapsto
 \left(\frac ND,\frac{SZ}{D^2}\right).
\]

As before, \(\pi_*\pi^*=[d]\). Pullback is injective on every prime-order
elliptic subgroup of order \(\ell>d\). The construction uses only
fixed-degree polynomial arithmetic and a bounded shift search, so it is
polynomial in \(\log p\) for fixed \(g\).

For \(g\ge3\), the construction has \(k\ge1\), hence a rational branch
point and an odd-degree (imaginary) hyperelliptic model after moving that
point to infinity. In genus two, the universal construction remains an
even-degree model; an imaginary model for every input elliptic curve is not
claimed.

The exact control constructs all genera two through seven for six elliptic
models over \(\mathbb F_{101}\), including cases with \(A=0\) and \(B=0\).
It checks squarefreeness and the branch count and verifies the displayed map
on every affine nonpole rational point. The zero-coefficient model forces
the bounded shift search to move past its first candidate.
[Higher-genus implementation](elliptic_hyperelliptic_cover_control.py) ·
[Frozen result](elliptic_hyperelliptic_cover_control.json)

## Consequence for the research goal

There are three materially different claims:

1. an algorithm for a specified generic open family of curves;
2. an algorithm for density-one curves with a quantified exceptional set;
3. an algorithm for every smooth curve of the genus.

The present coset coverage and inversion program targets the first or
second claim. Any final theorem must state the curve family, exclude or
handle special quotient loci, and quantify how bases and targets are
sampled. A universal theorem for hyperelliptic curves already implies an
elliptic-DLP breakthrough through the construction above and must not be
inferred from generic-family evidence. For \(g\ge3\), the same warning
applies even when the theorem is stated only for odd-degree hyperelliptic
models.

The obstruction is nevertheless thin in hyperelliptic moduli. The cover
locus used here has codimension at least \(1,2,2,4,4,6\) in genera two
through seven, respectively. Thus a density-one result can exclude it, but
only with a stated curve distribution and a proved exceptional-set bound.
[Dimension ledger](elliptic_locus_dimension.md)
