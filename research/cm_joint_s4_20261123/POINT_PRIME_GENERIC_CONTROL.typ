#set page(paper: "us-letter", margin: 0.7in)
#set text(font: "Helvetica", size: 10pt)
#set heading(numbering: "1.")
= Point-selected primes on a second ordinary curve
2026-11-25 · Exact finite-field control · PCC unverified

The split orbit algebra selector maps a supplied point Q to the maximal ideal
(X - x(Q)). The fixture scalar checks orientation; the selector reads only Q.

#table(
  columns: (auto, auto, auto, auto, auto),
  inset: 6pt,
  [Curve], [Order], [D], [x-primes], [m_G to m_3G],
  [F_47: y²=x³+x+38], [61], [-19], [30], [3, 58],
  [F_43: y²=x³+x+3], [47], [-163], [23], [3, 44],
)

#figure(image("point_prime_generic_control.svg", width: 95%), caption: [The point coordinate selects a prime on both curves. Computing its unknown action index remains the missing operation.])

Both curves have ordinary reduction, prime group order, and nonexceptional j.
The second row changes the Frobenius discriminant and curve equation. Every
ordinary finite-field elliptic curve has CM, so this is a control against
dependence on the special D=-19 setup, not a non-CM comparison.

Trivial Frobenius on a reduced ray fiber does not collapse distinct x-values.
These rows contain 30 and 23 distinct values. They do not construct a
characteristic-zero ray field or label its Artin action. A useful next step
must extract a nontrivial quotient of the action index from coordinates
without enumerating the orbit, then pass a full single-target cost test.

Sources and reproduction: `POINT_PRIME_GENERIC_CONTROL.md`,
`point_prime_generic_control.py`, `point_prime_generic_control_results.json`,
`RAY_CLASS_REDUCTION_AUDIT.md`, and `REDUCED_RAY_PRIME_BRIDGE.md` in this
study directory. The older proposal is
`crypto-autoresearcher:ledger/proposals/IDEA-20260808-5158fa.yaml`.
