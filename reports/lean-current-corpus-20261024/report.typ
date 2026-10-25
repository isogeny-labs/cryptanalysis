#set document(title: "Current cryptanalysis Lean corpus evidence")
#set page(paper: "a4", margin: 1.9cm)
#set text(size: 10pt)
#set par(justify: true)

= Current cryptanalysis Lean corpus evidence

24 October 2026. Source-bound audit based on cryptanalysis main
`9d320ae7df3b8aa15d4497d6895f63644daa92d5`, with two additional
GLV axiom print directives in this PR.
The authoritative machine-readable evidence is in `receipt.json` and the
full scope statement is in `report.md`.

#figure(image("coverage.svg", width: 100%), caption: [Tracked research Lean files with
native proof-build evidence. This is a file inventory, not a percentage of
historical experiment claims.])

== Method and result

The October 21 native corpus audit compiled 93 files. At the current head,
91 of those files have identical SHA-256 bytes and unchanged effective Lean
toolchain pins. Two revised Orbit files pass `lake build` and exact axiom
output for three public theorems. One new GLV theorem file passes the pinned
C-selector source binding and reproduces a corrected eight-theorem Lean
receipt. Two public theorem axiom printouts were absent from the prior
receipt. All fresh theorem axiom sets contain only `propext` and
`Quot.sound`. The historical generic gate's real imported-file probe failed
because it did not build a local prerequisite; the replacement CI check uses
the exact corpus bridge and fails closed on a new source or pin.

== Limit

These are 94 research-file build-evidence rows, with 91 inherited by exact
source and pin equivalence and recorded prior axiom checks. They do not
exhaustively audit every declaration's axioms or verify that every theorem
matches its research claim or that the historical experiments executed as
recorded. A claim-to-theorem-to-run matrix remains open. No curve, benchmark,
or performance result changed in this audit.
