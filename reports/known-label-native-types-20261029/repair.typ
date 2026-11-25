#set page(paper: "us-letter", margin: 0.65in)
#set text(size: 11pt)
= Known-label proof evidence: review repair
T-790 · 2026-10-29 · Candidate, awaiting independent review

== Independent findings
The review of a2aa1586 found two blocking workflow defects: failed native diagnostics were discarded, and runtime auditor / compiled-module identities were not bound. The original review and its six hash-verified artifacts are archived unchanged.

== Repaired evidence flow
#block(fill: rgb("eef4fb"), inset: 12pt, width: 100%)[
Frozen source + three workspace inputs + pinned auditor
→ retained input record
→ compilation + complete command diagnostics
→ compiled object / sidecar hashes
→ retained auditor execution + boundary checks
→ retained type wrapper and output + boundary checks
→ always-run hosted artifact upload
]

== Validation
38 Python controls pass. They include a real diagnostic child exiting 7 with non-UTF8 output and 4000-byte stderr, a simulated timeout, malformed zero-exit type output, missing or replaced compiled objects, added sidecars and changed auditors. Synthetic object and type fixtures test orchestration only.

== Trust and limits
These hashes check phase boundaries. They do not establish an immutable workspace or detect transient edits restored between checks. Lean executable, dependency binaries/cache and runner integrity remain trusted. No local native build or experiment ran. The frozen theorem source and dependency pins are unchanged.

== Remaining gates
Fresh exact-head hosted Lean execution, complete downloaded diagnostic artifacts, independent repair review, and semantic comparison of all four actual elaborated types remain required. No theorem, historical execution, security or performance promotion follows from these controls.

Sources: review-response.md; unit-tests-f2.txt; repair-bindings.json; reviewers/TASK-20261029-b339cc/report.md. The earlier report.pdf remains an immutable description of the initial candidate.
