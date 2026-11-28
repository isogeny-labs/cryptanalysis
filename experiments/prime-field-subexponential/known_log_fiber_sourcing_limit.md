# Known-log doubling chains cannot source hyperelliptic fibers

A tempting direct DLP construction is to choose each binary fiber from a
known scalar multiple $P_i=a_iG$. If all $P_i$ are curve points, a signed
fiber inverter returning

\[
 Q=\sum_i\epsilon_iP_i
\]

immediately gives
$\log_GQ=\sum_i\epsilon_i a_i$. Choosing $a_i=2^i$ would also give a
succinct repeated-doubling circuit for the input fibers.

This construction is available on an elliptic curve, where the curve is its
Jacobian, but not on an Abel curve of genus at least two. Let
$\iota:C\hookrightarrow J$ be the Abel embedding. The points whose doubles
are again curve points lie in

\[
 \iota(C)\cap[2]^{-1}\iota(C).
\]

This intersection is proper. Otherwise $[2]$ would restrict to a nonconstant
self-map of $C$. Riemann--Hurwitz makes every self-map of a genus-at-least-two
curve an automorphism, while the pullback of a theta polarization under
$[2]$ has four times its degree on $C$, a contradiction.

Embed the principally polarized Jacobian by $3\Theta$. Poincare's formula
gives degree $3g$ for the Abel curve, while the cycle
$[2]^{-1}\iota(C)$ has degree

\[
 3g\,2^{2g-2}.
\]

Bezout therefore bounds the geometric intersection, including multiplicity,
by

\[
 9g^2 2^{2g-2}.
\]

This is constant at fixed genus and independent of the field. Consequently a
doubling orbit contains only $O_g(1)$ distinct consecutive Abel-curve points;
it cannot supply the $\Theta_g(\log p)$ distinct fibers needed at binary
occupancy.

Arbitrary known scalars do not repair the setup cost. A large prime-order
subgroup has $p^{g+o(1)}$ elements, while the curve has only
$p+O_g(\sqrt p)$ rational points. A uniformly sampled known scalar multiple
therefore lands on the Abel curve with probability at most
$p^{1-g+o(1)}$. Sourcing even one this way has expected cost
$p^{g-1+o(1)}$.

## Exact genus-two control

On the frozen genus-two curve over $\mathbb F_{101}$, the Jacobian has 9,758
classes and the Abel curve, including infinity, has 98. Only two Abel classes
double back onto the Abel curve. They are infinity and one nontrivial class;
97 starting classes have distinct doubling-chain length one and one has
length two. No chain has three distinct curve classes.

## Exact limit

The geometric argument rules out this known-log doubling-chain source, not a
new inversion algorithm on independently sampled fibers. The density bound
concerns scalar sampling in a subgroup of order $p^{g+o(1)}$; special
lower-dimensional subgroups or curves with extra decompositions require
separate analysis. Higher-degree divisor atoms also lie outside the binary
curve-fiber construction. No DLP exponent improvement is claimed.
