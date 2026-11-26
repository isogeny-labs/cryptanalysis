# Lifting to a growing-genus cover does not remove the prime-field exponent

A finite cover gives a correct and efficiently verifiable transfer of the
discrete logarithm, but applying the known growing-genus index calculus to the
cover does not give \(p^{o(1)}\) work for a fixed-genus source over a growing
prime field.

## Correct transfer

Let \(\pi:C'\to C\) be a separable degree-\(n\) cover.  Pullback and norm
satisfy

\[
 \pi_*\pi^*=[n]\quad\text{on }J_C.
\]

Consequently pullback is injective on every prime-order subgroup of order
\(\ell\nmid n\).  A DLP in that subgroup can be lifted to \(J_{C'}\), solved
there, and verified back in \(J_C\).  For an unramified cover,

\[
 g'=n(g-1)+1.
\]

The obstruction is complexity, not correctness.

## Direct use of the known growing-genus algorithm

The explicit order-free hyperelliptic bound in the prior note is

\[
 \exp\!\left(O\!\left(\log p+
 \sqrt{g'\log p\log(2g')}\right)\right).
\]

The first \(\log p\) term cannot be made \(o(\log p)\) by choosing the cover
degree.  More concretely, that algorithm uses all split and ramified places
through a positive degree cutoff \(d\ge1\).  In the subpolynomial-genus range,
the degree-one split-place count is \(p/2+O(g'\sqrt p)\), so merely enumerating
the prescribed base costs \(p^{1-o(1)}\).  Taking larger \(g'\) only increases
the square-root term or makes construction itself non-subexponential.

Thus this particular growing-genus solver remains polynomial in \(p\), even
though it is subexponential in the much larger ambient group size
\(p^{g'}\) as \(g'\to\infty\).

## Partial lifts pay the Prym constraint

Suppose a source factor base of size \(B=p^{o(1)}\) is lifted sheet by sheet,
giving at most \(nB\) point labels on \(C'\).  The pullback target lies in the
\(g\)-dimensional subvariety \(\pi^*J_C\) of the \(g'\)-dimensional ambient
Jacobian.  Any relation distribution that mixes in \(J_{C'}\) hits this image
with probability

\[
 p^{-(g'-g)+o(1)}.
\]

Equivalently, the extra sheet choices must cancel their component in the
Prym, whose dimension is \(g'-g\).  At the ordinary coverage scale an ambient
long-sum search therefore needs

\[
 (nB)^m\gtrsim p^{g'},
\]

not merely \(p^g\).  The apparent entropy from choosing sheets is consumed by
the Prym cancellation condition.

This statement is conditional only on ambient mixing.  A non-mixing solver
that uses special Prym structure could behave differently, but it would be a
new inversion algorithm rather than an application of the existing
growing-genus method.

## Complete fibers collapse to the source problem

The divisor formed by a complete fiber is a pullback:

\[
 \sum_{P'\in\pi^{-1}(P)}P'=\pi^*P
\]

with ramification multiplicities.  Restricting every relation atom to a
complete fiber removes the Prym component identically, but then a sum of
fiber atoms is exactly the pullback of a sum on \(C\).  The hidden-choice
problem and its \(B^m\gtrsim p^g\) coverage threshold are unchanged.

Hence the two natural extremes are exact opposites:

- partial fibers add choices but also add \(g'-g\) cancellation constraints;
- complete fibers remove those constraints but give no new choices downstairs.

Intermediate deck-orbit blocks obey the same norm/Prym accounting unless an
additional algebraic correlation is proved.

## Scope

This rules out a black-box composition of pullback with the stated
all-small-place growing-genus algorithm, plus the naive partial- and
complete-fiber factor bases.  It does not rule out a cover family with a new
Prym-specific inverter, a special small embedding degree, or another
algorithm whose setup avoids enumerating the degree-one places.

[Executable ledger](cover_lift_tradeoff.py) ·
[Frozen ledger](cover_lift_tradeoff.json)

```sh
python3 cover_lift_tradeoff.py | cmp - cover_lift_tradeoff.json
```
