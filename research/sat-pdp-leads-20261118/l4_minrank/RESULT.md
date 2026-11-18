# L4: support-minors MinRank on the lin21 leaf, killed by counting (2026-11-18)

This is a desk check plus one exact sampling computation. There is no
solver run and no timing claim. Everything here is `[pcc:unverified]`.

## Correction to the leads note

L4 as first written said the leaf matrix M(x3) has entries of degree at most
2 in x3's bits. That is wrong. The leaf's coefficient is u = x(R − P3).
Computing it goes through the group law and through y3, which is a
half-trace of an expression in x3, so u is not a low-degree function of
x3's bits. The round-4 discard table says the same for t(x1)
(`crypto:research/sat_leads_round4_20261116/PROPOSALS.md`, "Additive FFT"
row).

The only MinRank-shaped form keeps u as n free bits. Then the lin21 leaf
(`crypto:examples/ic_algebraic_floor/linear21.rs`, variant Full) reads

  p² + u·p + u²·s² + b = 0,  with s ∈ span(1, …, z^(d−1)) and p ∈ span(1, …, z^(2d−2)).

That is n equations, F2-linear in the 3d − 1 bits of (s, p). The
coefficients are linear in u's bits, because squaring is F2-linear.

## Counting check

The MinRank condition "the augmented leaf system is consistent" is a rank
condition on a matrix that is linear in u. If it holds for a constant
fraction of all u, it cannot single out the roughly 2^d true values
u = x(R − P3), for x(P3) ∈ V. Prediction: a fraction of about
2^−(n − 3d + 1).

`rank_fraction.py` computes the leaf's consistency exactly. It uses 4,000
uniform u per n for the relaxation, and every true u from 20 random targets
per n.

| n | d | (s, p) bits | relaxed fraction | predicted 2^−(n−3d+1) | fraction among true u |
|--:|--:|--:|--:|--:|--:|
| 13 | 4 | 11 | 0.218 | 0.250 | 0.169 |
| 15 | 5 | 14 | 0.396 | 0.500 | 0.400 |
| 17 | 5 | 14 | 0.114 | 0.125 | 0.131 |
| 19 | 6 | 17 | 0.218 | 0.250 | 0.248 |
| 21 | 7 | 20 | 0.386 | 0.500 | 0.405 |

Raw data: `rank_fraction.json`.

## Decision: kill

The relaxed rank condition holds for about 2^(n−3d+1) of all u: between
2^(n−2) and 2^(n−1) values. Only about 2^d of those are true. True u values
pass at the same rate as random ones, so the condition carries no
information that separates them. Support-minors, or any MinRank solver on
this matrix, would find a solution set of size about 2^(n−2) and gain
nothing.

All the information that isolates the true u values sits in the link
S3(x3, u, xR) = 0 with x3 ∈ V. Adding that link back gives exactly
round-4 lead D's bilinear (t; q) system, which is proposed and costed
there. L4 therefore adds nothing beyond D. If anything here is pursued, it
is D's Macaulay-rank measurement.

The measured fractions sit somewhat below the prediction; the lowest is
0.77 of the predicted value, at n = 15 and n = 21. The likely cause is that
the leaf's columns are not uniformly random, for example because of trace
constraints. This does not affect the conclusion.
