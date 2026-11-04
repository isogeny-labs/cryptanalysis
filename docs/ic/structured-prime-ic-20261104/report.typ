#set page(paper: "a4", margin: 18mm)
#set text(size: 10pt)
= C1–C3 native consumer integration
2026-11-04 · producer report · PCC-20261104-f011a3, unverified

The new tensor-structured command accepts explicit public parameters and query
points in a strict versioned JSON request. It prepares the structured network
once, returns exact counts and signed prefix witnesses, and supports semantic
replay on matching selected source files. [pcc:unverified]

#image("integration.svg", width: 100%)

*C1:* rational two-isogeny fibre and actual subgroup predicates use the existing
complete point-summation charts. *C2:* prefix-count extraction and arithmetic
replay are exposed through the consumer. *C3:* a root-based local membership
diagram and the prepared network are reused across the request's query points.
The suite adapter names its separate structured backend so its older tensor
types and APIs remain available. [pcc:unverified]

*Resource and receipt contract.* One budget covers validation, setup and every
count-plus-witness query. A later resource error emits no partial success JSON.
The semantic digest binds the request, signed-tuple policy and answers. Replay
recomputes these answers, including when a changed answer has been rehashed.
Selected source pins are partial provenance; diagnostic counters are not part
of semantic replay. Receipts carry producer_assertion standing. [pcc:unverified]

*Development panel.* Public-fixture controls cover counts/witnesses, replay,
forged/rehashed answers, source mutation, nested duplicate fields, invalid inputs,
empty fibres in both modes and mid-batch exhaustion. Native library checks,
Clippy, formatting and Rust1.78 accompany the consumer controls. Raw output and
observed summaries are retained in checks/ and checks.json. Initial portability
compile failures are retained too. These are producer reports. [pcc:unverified]

*Retrieval and next step.* Autoresearcher record KN-OPEN-08ba7e links the sources
and asks for a compact full constrained summation-boundary message. Local
membership reuse is the implemented component; full-message construction and
live-storage accounting are the next algorithmic dependency. This integration
does not change research statuses or scientific findings.

*Sources.* Landed C1–C3 study and native API; PKM2016; Hexagon2610.00600v1,
2610.00594v1 and2610.00613v1; Kosters–Yeo1503.08001v3. The README carries exact
links and reproduction commands. No new mathematical theorem is asserted.
