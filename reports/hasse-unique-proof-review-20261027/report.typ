#set page(paper: "a4", margin: 1.2cm)
#set text(font: "Liberation Sans", size: 9pt)
#set heading(numbering: "1.")

= Hasse interval theorem: independent proof review

*27 October 2026 UTC · T-493 · producer commit `dc73f979`*

The exact Lean declaration `CurveAudit.unique_multiple_in_short_interval` proves a conditional arithmetic statement: two natural-number multiples of `r` within `width` of one another are equal when `width < r`. The narrow README claim matches this statement. It does not by itself prove P-192 or P-224 curve order.

#figure(image("proof-boundary.svg", width: 100%), caption: [Verified implication and open curve-order inputs. Orange boxes are not Lean-certified by this theorem.])

== Separate verdicts

#table(
  columns: (1.7fr, 1fr, 1fr, 1fr),
  inset: 5pt,
  [*Claim*], [*Machine*], [*Fidelity*], [*Overall*],
  [Nearby multiples are equal under the stated hypotheses], [passed], [faithful scoped], [validated scoped],
  [Full P-192/P-224 curve-order certificate in Lean], [not verified], [partial], [inconclusive],
)

== Evidence and controls

The producer theorem source SHA-256 is `0e0b14f032203329328910ac0bc0f03db88f508087c4fdb236fd1bbe6d7e49f7`; the pin is Lean 4.34.1. An isolated exact-source build exited zero. The transitive audit found one theorem, zero failures, and axioms `propext` and `Quot.sound`; no `native_decide` exception was used. Pre/post source, pin, and auditor hashes matched. The trust boundary is the installed pinned Lean kernel; an independent `lean4checker --fresh` binary was unavailable.

A deliberately false theorem with `sorry` compiled, but its axiom audit exited 1 and printed `sorryAx`. Auditing an unknown module exited 1. A Lean checked concrete counterexample at `width = r = 7` shows the strict bound is sharp; `r = 7`, `width = 3`, `n = m = 14` shows the original assumptions are satisfiable. Full commands, exits, digests, and logs accompany this PDF in `machine-receipt.json` and `control-receipt.json`. Test input bytes are archived as `.lean.txt` to exclude them from the repository's theorem inventory.

== Independent fidelity review

Reviewer A derived the implication from the statement alone and attested no producer-source or sibling-report access. Reviewer B compared the declaration with the README and Rust certificate path, checked committed input and archived digest consistency, and attested no access to A. The prior and assignments were committed before dispatch as `3b704f1`. Attestations are self-reported; filesystem reads were not monitored.

The checked-in P-192/P-224 values match historical NIST FIPS 186-4 Appendix D.1.2. B recomputed the candidate integer bounds, spacing, trace, and twist arithmetic. That document is a historical parameter source, and this review did not independently run Rust or Sage. Hash agreement does not authenticate archived execution.

== Obligations before a full formal order claim

Bind the JSON inputs to Lean; prove primality checker and parser correctness; connect finite-field and point code to a nonsingular elliptic group; prove exact point order and Lagrange divisibility; prove Hasse for the actual curve; convert squared bounds to a strict natural interval; instantiate this theorem with actual cardinality and proposed order. Formal trace and twist results require further identities. The producer README correctly labels this broader proof as partial.

The full source-linked analysis, reviewer reports, controls, and raw logs are in `report.md` and its companion files. No measured performance data were generated here, so the existing performance graphs have no new data to absorb.
