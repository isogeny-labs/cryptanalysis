# Frozen native-base three-sum yield screen

## Question and instance

On the existing ordinary horizontal degree-five pair over `F_1009`,
does selecting an eight-point factor base independently by the same
coordinate rule on each endpoint change the number of naturally
decomposable target points? The source is `y^2=x^3+4x+10`; the
codomain, already fixed by the first degree-five Sage edge in this PR,
is `y^2=x^3+888x+852`. Both have prime order `1069` and maximal CM
order with discriminant `-555`. This screen is fixed before its output
is collected. [pcc:unverified]

## Frozen selection and measures

For each curve, enumerate all rational points in increasing integer
`x`, then `y`. The native base consists of both signs above the first
four admissible `x` values, giving eight distinct points. For every
three-element multiset from that base, sum its points; retain distinct
nonidentity sums. The primary result is the number of these sums among
the 1068 nonidentity targets, or equivalently the exact hit probability
for a uniform target. Source-base transport through the isogeny has
the same support size by the [transport theorem](TRANSPORTED_RELATION_GATE.md);
the independent codomain base can differ. This is a full census, not
a sampled-query yield estimate. [pcc:unverified]

As a descriptive control, on **each** curve draw 128 bases by choosing
four distinct admissible `x` values uniformly with Python
`random.Random(20261125)`; include both signs. The two curve streams
use independent instances of that same seed, with no pairing claim.
Report every support count and min/median/max. The random panel
quantifies ordinary same-size base variation; it is not a calibrated
significance test of a curve or edge chosen earlier. [pcc:unverified]

The runner uses integer field arithmetic, checks nonsingularity and
the exact point counts, checks inverse and order identities on every
enumerated point, and emits one JSON record. No polynomial solving,
linear algebra, relation collection, or rho timing is in this screen.
If native endpoint support is materially larger, the next gate is a
frozen same-target coordinate-solver comparison with extraction and
full costs. If it ties or falls below source, this fixed base rule
does not justify that more expensive experiment. [pcc:unverified]
