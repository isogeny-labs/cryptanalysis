#set page(paper: "us-letter", margin: 0.7in)
#set text(font: "Helvetica", size: 9.5pt)
= Ideal arithmetic of the finite point-orbit bridge
2026-11-25 · Exact algebraic audit · PCC unverified

For a prime-order rational group, the orbit polynomial has every
nonidentity x-coordinate as a simple root. The Chinese remainder
theorem identifies A_x = F_p[X]/F_G with a product of (r-1)/2 copies
of F_p. The supplied point Q selects the maximal ideal m_Q that
vanishes at the coordinate x(Q).

#figure(image("split_orbit_ideal_arithmetic.svg", width: 50%), caption: [The finite point selector is compact, but its ideal multiplication is idempotent and does not supply CM class-group relations.])

In the product presentation, m_Q²=m_Q, and distinct selected ideals
multiply by taking the union of their zero-coordinate sets. Each is
proper and noninvertible. The Picard group of the split product ring
is trivial. This standard CRT consequence is scoped to the finite
coordinate algebra, not the characteristic-zero ray field.

The Sage replay checks the Bezout identity proving idempotence for
all 30 roots on the p=47, r=61 control and all 23 roots on the p=43,
r=47 control. The accompanying Lean 4 theorem proves selected-ideal
membership, idempotence, properness, and noninvertibility in the
product-ring presentation. The quotient-to-product CRT isomorphism
is used in the written proof and is not in the Lean file. [pcc:unverified]

The remaining step is an efficiently oriented, point-dependent
characteristic-zero ray object or a new operation on the compact
selector that extracts an action-index quotient. Its construction
and full same-target cost must be charged.

Sources: `SPLIT_ORBIT_IDEAL_ARITHMETIC.md`,
`split_orbit_ideal_arithmetic.py`, its retained JSON,
`formal/SplitOrbitIdeal.lean`, and `REDUCED_RAY_PRIME_BRIDGE.md`.
