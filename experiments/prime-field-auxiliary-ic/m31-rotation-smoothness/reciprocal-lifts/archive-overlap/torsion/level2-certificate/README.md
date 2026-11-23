# Exact threshold on the archived level-two fiber

Threshold.lean states an equivalence for every natural-number smoothness
bound. A common scale and two independently rotated representatives of an
eligible sibling pair exist precisely for inclusive bounds at least 211.
Membership uses mathlib's Nat.smoothNumbers with strict cutoff b+1.
The eight input pairs are bound to the archived manifest by fixture.py.

For B=8 a compatible scale has (8s²)^31=1. The proof reduces all such scales
to a rotation of either 16384 or its negative. Each input word is a positive
field representative. At cutoff 210 the kernel verifies that at least one
side of each signed pair has, in each of its 31 rotations, a divisor greater
than one and coprime to 210!. Its smallest prime factor therefore exceeds
210. This exclusion also covers pairs of square character.

At cutoff 211 the seventh pair with positive scale 16384 attains the bound.
Its two rotated integers, at offsets 16 and 7, are 1,890,051,279 and
2,058,966,525. The kernel verifies smoothness, negative Euler character,
distinct orbit keys and reciprocal compatibility. Monotonicity gives the
claim for all bounds. Because 2 is an allowed factor at these cutoffs,
removing powers of two to obtain an odd representative preserves smoothness
and stays inside the same rotation orbit.

Run python3 fixture.py in the checkout and run lake env lean on the absolute
path to Threshold.lean from the Lean 4.34.1 mathlib environment.
