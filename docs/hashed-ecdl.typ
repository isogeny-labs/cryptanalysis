#set page(paper: "a4", margin: 19mm)
#set text(font: "DejaVu Sans", size: 10pt)
#set heading(numbering: none)
= Hashed-factor-base ECDL reference
2026-10-29 · Implementation report · Partial replication

The requested source is Akshima et al., _A Subexponential Time Algorithm for
Elliptic Curve Discrete Logarithm_, version 0.2, October 29, 2026. Upstream
revision: #text(size: 8pt)[1ee44e562b1b9a50ea339f3b8f81112b5a24b96f].
#link("https://github.com/bochum-crypto/subexponential-ecdl")[Source repository].

== Delivered code
The same native Rust algorithm is exposed as
`crypto_lib::cryptanalysis::hashed_ecdl` and `cryptanalysis::hashed_ecdl`.
It implements the affine-hashed bases of section 3.2, inverse-hash enumeration
of section 3.5, and Figure 2's relation/dependency reduction. Every decomposition
is checked; a certificate retains the successful trial's hashes, relations and
modular dependency. Replay checks every relation, cancellation, V != 0, and
the final scalar multiplication.

#image("hashed-ecdl.svg", width: 100%)

== Implementation boundary
The default oracle enumerates m-1 slots and checks the final group residual.
It is generic decomposition, not tensor contraction. The compact O(mb)-edge,
low-degree Boolean arithmetic/decomposition encoder and the assumed fast
contraction algorithm are *not implemented*. The paper's Theorem 2 relies on
external Theorem D.1 of [Ope26]; it was not independently verified here.
The full conditional asymptotic replication remains unresolved.

The reference supports prime fields at most 65521, exact cofactor-one odd-prime
cardinality, 2 through 8 slots and at most 512 dense columns. Public seeded
SplitMix64 supplies reproducible fixtures, not a cryptographic or ideal uniform
randomness guarantee. The small-field square-root table has O(p) setup and
space. These bounds and choices do not implement the paper's full complexity.

#pagebreak()
== Validation and remaining work
Nine shared unit tests cover independent point-scan factor-base checks,
all-target oracle checks, every logarithm in a 19-point fixture group, seeded
two/three-slot solves, corruption rejection, V=0 extraction and resource limits.
The cryptanalysis API additionally cross-checks scalar arithmetic against its
independent C implementation. Actual integration commands and outcomes are
recorded in the PR; the Markdown companion gives reproducible commands.

No performance experiment, IC/rho comparison, deployed-curve run, new theorem,
Lean proof or general runtime guarantee is claimed. Scoreboards, progress
timelines, leaderboards and curve diagrams remain unchanged because no admitted
measurement or new curve/route fact was produced. The open problem record
`problems/hashed-ecdl-tensor-backend.md` in crypto names the missing encoder,
backend, review and validation exit conditions. Passing tests or merging this
code does not resolve that problem.

== Sources checked
Upstream abstract, limitations, Theorems 2/4 and sections 3.2–3.5; crypto's
index-calculus boundary ledger, `semaev_decomp.rs` and
`aps_single_relation.rs`; cryptanalysis's existing multiplicative finite-field
IC binding; and the sibling ECDLP atlas's first-fall-degree assumption lead.
No novelty or performance conclusion is inferred from that review.
