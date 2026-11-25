#set page(paper: "a4", margin: 18mm)
#set text(font: "DejaVu Sans", size: 10pt)
#set heading(numbering: none)
= Hashed-factor-base ECDL tensor implementation
2026-10-29 · Native implementation report · Correctness evidence only

The compact encoder, exact contraction machinery and Figure 2 relation
reduction are implemented in both isogeny-labs/crypto and cryptanalysis.
The source is Akshima et al., A Subexponential Time Algorithm for Elliptic
Curve Discrete Logarithm, v0.2, revision
#text(size: 8pt)[1ee44e562b1b9a50ea339f3b8f81112b5a24b96f].
#link("https://github.com/bochum-crypto/subexponential-ecdl")[Bochum source].
The external contraction algorithm is OpenAI's October 25 manuscript,
Appendix D.1/D.4, revision
#text(size: 8pt)[7ef5c0cc5ca4b0e072b7a050fca09ab24bc6fa3a].
#link("https://github.com/openai/math/tree/7ef5c0cc5ca4b0e072b7a050fca09ab24bc6fa3a/preprints/The-Exponential-Time-Hypothesis-is-False-October-25-2026")[External source].

#image("hashed-ecdl.svg", width: 100%)

== Public interface
The shared crate is `hashed_ecdl_tensor`. Both repository APIs export it as
`hashed_ecdl::tensor`; the earlier bounded generic reference is preserved.
The native runner reads a public JSON problem, writes an exclusive new
receipt, and independently replays a receipt. OS randomness is the default;
seeded fixtures provide reproducibility, not ideal-uniform runtime guarantees.

#pagebreak()
== Compact encoding and general inputs
Ripple addition, comparison and zero tests compose with two-stage Fourier
integer multiplication over the paper's canonical residue words. Quotient and
carry identities implement canonical modular products. Point predicates cover
identity, inverse, ordinary addition and doubling; affine hash membership uses
coordinate bits, without a factor-base lookup. Constant-degree equality trees
distribute shared bits into ordinary graph edges.

Integers are arbitrary precision. Exact AKS prime certification, with a fixed
small trial-division prefix, and Tonelli–Shanks replace the earlier field bound
and root table. Curve construction certifies the subgroup and full cardinality
c*r through the Hasse interval or exact counting in ambiguous cases. Cofactor
clearing projects free Si to Ai=[c]Si. Counts retain preimage multiplicities;
the projected witness language remains the requested subgroup decompositions.
The paper's unchanged asymptotic extension assumes fixed c.

== Exact contraction
The implementation includes the unramified coefficient ring modulo powers of
two, conditional-expectation packet packing, integral Cauchy deformation,
streamed weighted modes, implicit packet tensors, depth-first contraction and
tapered Hermite recovery. Retained entries are evaluated at their immutable
creation precision before canonical lifting. Interpolation uses residue-distinct
points; reconstruction uses exact rational arithmetic and checks integrality.

Literal admission guards matter. The source has
u=floor(ceil(log2(s))/131072), where s is its network-size parameter. It is
zero for all practically addressable graphs.
Those inputs use exact finite-size fallback. Private built-in metadata permits
enumerating free input bits with uniquely determined auxiliaries. Caller
predicates cannot assert such metadata. Execution counters report Direct,
Functional or Recursive. Forced small recursion tests bypass admission/shrink
size bounds only; their outputs are compared with direct contraction. They do
not measure asymptotic behavior.

== Reduction and replay
Factor bases are enumerated by inverse hashes and root extraction. Each
slot/point has its own matrix column. Tensor search receives only a target and
seed. A trial collects N+1 relations within 20(N+1) attempts; deterministic
modular elimination chooses a dependency without u/v, and V=0 restarts.
Replay rebuilds the bases and independently checks every membership, group
equation, slot-column cancellation, nonzero dependency and scalar extraction.
Execution counters are informational and do not attest discarded trials.

#pagebreak()
== Validation and limits
The 27 core controls include arbitrary graph truth tables and prefix witnesses,
parallel edges, exact ring units/interpolation, creation-precision retention,
Cauchy kernels, tapered Hermite recovery, weighted tuples and a full forced
packet recursion versus independent direct contraction. Arithmetic products
are checked independently through 513-bit input words, with explicit edge and
degree inequalities. Point networks cover every pair on two small curves,
including infinity, inverses, doubling and two-torsion. Hash enumeration is
compared with a subgroup scan.

Coupled controls check parallel ports and quadratic modes, then retain an old
packet's creation precision through two recursion levels, against direct counts.

The full tiny relation pipeline recovers a public scalar and rejects corrupted
relations, dependencies and scalar certificates. Cofactor projection is checked
separately. The cryptanalysis binding additionally cross-checks all 199 scalars
of a small curve against its independent C arithmetic. The current validation
receipt records the actual final-source tests, lint, minimum compiler, CLI,
source parity and broad-root regression outcomes; pending work is not a pass.

The native runner caps input files at 16 MiB and refuses to overwrite receipts.
Caller bounds govern steps, vectors, precision, columns and trials. Exhaustion
returns an error: it is not a zero count or a proof of nonexistence. Practical
input sizes can exhaust these policies long before cryptographic sizes.

== Requirement status
Code replication now includes the encoder, contraction backend and reduction,
with public integration in both repositories. General correctness and complexity
audit of the external theorem remains open in the canonical problem record.
No conditional theorem was independently proved, no deployed-curve run or
security consequence was established, and no IC/rho performance experiment was
launched. No new mathematical result or Lean proof is claimed. Passing bounded
tests or merging code does not prove the general algorithm.

The historical first-reference receipt remains intact. No frozen evidence,
validation gate, leaderboard, curve route or benchmark is changed. See
`docs/hashed-ecdl.md`, `docs/hashed-ecdl-tensor-validation.md`, and crypto's
`problems/hashed-ecdl-tensor-backend.md` for source links and remaining review
obligations. Prior literature/code review is recorded there; no novelty claim
is inferred from finding no prior executable implementation.
