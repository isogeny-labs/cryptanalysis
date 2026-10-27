#set page(paper: "a4", margin: 1.2cm)
#set text(font: "Liberation Sans", size: 9pt)
#set heading(numbering: "1.")
= Squared Hasse predicate bridge: technical review
*27 October 2026 UTC · T-504 · producer `f1c2dca`*

The Lean theorem connects the Rust-style natural-number checks to uniqueness: both unsigned deviations from `p+1` square to at most `4p`, and `r²>16p`. Actual curve-cardinality facts remain outside the theorem.

#figure(image("proof-boundary.svg", width: 100%), caption: [Checked arithmetic implication and separate curve-order obligations. No performance data were generated.])

== Separate verdicts
#table(columns: (2.2fr, 1fr, 1fr, 1fr), inset: 5pt,
[*Claim*], [*Machine*], [*Fidelity*], [*Overall*],
[Nat squared-predicate uniqueness], [passed], [faithful scoped], [validated scoped],
[Full P-192/P-224 order proof], [missing bridges], [partial], [not verified])

== Evidence and controls
Producer source SHA-256: `26e3e7bbf28aad0f60f72137fca027427b435f05bcef9f5de5881d7979307c42`. Pinned Lean: 4.34.1. The exact-source build passed. The transitive audit found five new-module theorems, zero failures, zero `native_decide` exceptions, and only `propext`, `Quot.sound` or no axioms. The positive `p=101,r=41,n=m=82` application and sharp `p=1,r=4,n=0,m=4` boundary built and audited. The `sorry` false theorem compiled but its audit rejected `sorryAx`; the missing-module audit failed closed. All nine exits matched expectations and input hashes stayed unchanged. Commands, exits and hashes are in `machine-receipt.json` and raw logs.

Blind reviewer A derived the implication and sharp boundary without producer source. Reviewer B checked the Lean statements against the proof map and Rust predicate, disclosing extra generic process and neighboring Rust reads beyond the plan's literal list, but no sibling review access. These attestations were self-reported.

== Remaining work
A complete certificate still needs a concrete prime field and elliptic group, exact point order and Lagrange divisibility, Hasse for the actual cardinality, Rust BigUint and parser correspondence, and P-192/P-224 input binding. The installed Lean kernel is the machine trust boundary; independent `lean4checker --fresh` was unavailable. No measured performance quantity changed, so existing performance graphs and dashboard values remain as they were.
