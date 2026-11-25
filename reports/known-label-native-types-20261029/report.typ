#set page(paper: "us-letter", margin: 0.65in)
#set text(size: 11pt)
= Known-label identities: native type collection
T-790 · 2026-10-29 · Implementation and evidence boundary

#image("type-evidence.svg", width: 100%)

== Observation
Four frozen ring identities have a pinned native compilation and transitive axiom audit path. Their explicit elaborated types are absent from the historical claim matrix. This gap prevents a complete independent comparison of the actual theorem interfaces with the intended statements.

== Implementation
The corpus gate now creates an isolated type-printing wrapper after compiling and auditing the original module. It imports the freshly built original object through the same isolated LEAN_PATH. Four fully qualified check commands request explicit universe and binder output. The gate rejects missing, duplicate or wrong-name output and propagates command failure. It retains wrapper bytes, actual stdout and their digests in the native log.

== Validation
32 Python orchestration and refusal tests passed. These tests use synthetic Lean output and do not establish native elaboration or theorem truth. The original Algebra.lean bytes and workspace pins remain unchanged. Exact hashes and the test transcript accompany this report.

== Pending evidence
The existing hosted Lean gate must execute the changed collector at the final head. Independent review must inspect the wrapper and compare all four actual elaborated types with their intended ring identities. Current native type status: not_verified. Overall review outcome: inconclusive.

== Scope
No local heavy build or experiment was launched. The original mathematical proofs, historical receipts and archived reviews are preserved. This change does not establish graph-to-group, cancellation, probability, cost, historical execution or complete cryptanalytic claims. No performance graph changes are justified; the diagram records the evidence flow only.

Sources: tools/lean/current-corpus-gate.py; tools/lean/test_current_corpus_gate.py; docs/known-label-next-leads-20261028/Algebra.lean. Base 934bf8329bcff52d943e282be59e0c9b62275f66. See bindings.json and unit-tests.txt.
