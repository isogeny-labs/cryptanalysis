#set page(paper: "a4", margin: 17mm)
#set text(size: 10pt)
#set par(justify: false)
#set heading(numbering: none)
= Exact rejection pruning for hashed ECDL
Implementation record · 2026-10-30 UTC · Conductor T-873

*Scope.* Improve the finite-size functional fallback in the native Boolean
tensor / hashed-factor-base implementation. This is software validation;
runtime benefit and the general ECDLP objective remain open.

#image("hashed-ecdl-functional-pruning.svg", width: 100%)

== Why the skip preserves the answer
Enumeration digit zero changes fastest. Each signal receives the minimum
position of any free input that can affect it. A failing check with minimum
position k cannot change while digits below k vary. Resetting those digits and
incrementing the suffix skips only rejected inputs. Pinned derived outputs
retain the dependencies of their computation. Successful inputs advance one
at a time, preserving multiplicity; canonical witness order stays unchanged.

== Evidence and controls
The crypto native suite passes 37 tests, including exact full seeded
certificate agreement with the exhaustive prefix-count control and independent
algebraic replay. New regressions cover 81 interface pin configurations,
transitive dependencies, unused inputs, aliases, constant rejection,
fully pinned inputs and exhausted budgets. Strict Clippy and Rust 1.78 checks
pass. The fixed diagram values are assertions in the native regression,
not sampled timing measurements. The Markdown report records mirror and
integration outcomes, commands and source hashes.

== Boundaries and reproduction
Disable #raw("Counter::functional_pruning") for exhaustive enumeration.
Also disable #raw("functional_witnesses") for the original prefix-count
control. Preparation is charged to Meter, so tight budgets can be exhausted
earlier. There is no measured runtime, large-instance scaling or challenge
result. No benchmark or paid cloud job was launched for these checks.

Source base: crypto #raw("bd4c2fe5e6f"). See
#raw("docs/hashed-ecdl-functional-plan.md") and the modified
#raw("network.rs"), #raw("contraction.rs"), #raw("reduction.rs").
The existing recursive backend and theorem parameters are unchanged.

#link("https://github.com/bochum-crypto/subexponential-ecdl/blob/1ee44e562b1b9a50ea339f3b8f81112b5a24b96f/subexponential-ecdl.pdf")[Primary source: Bochum v0.2, Section 2 and Lemma 1; Section 3 parsimonious encodings.]
The optimization is standard dependency-based pruning; no novelty claim is made.
