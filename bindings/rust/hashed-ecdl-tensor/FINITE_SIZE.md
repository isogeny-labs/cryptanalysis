# Opt-in finite-size backends

The source-compatible default solver, random stream, certificate schema and
Appendix D guards remain available. These paths add exact bounded alternatives;
they do not establish a runtime speedup, sub-rho algorithm or challenge solve.

| Review item | Implementation | Remaining limit |
| --- | --- | --- |
| 1. Hash selectors | `finite::prime_decompose`, `finite::selector_network`, `Encoder::selector_point` | Tuple search is generic; decoder arithmetic and failed codes are charged |
| 2. Encoding/solver choice | `Encoder::schoolbook_multiply`, `width::plan`, `width::count`, `width::witness` | Greedy rank planning, no optimal-width guarantee or SAT/CNF exporter |
| 3. Checked local plans | `Plan::validate` checks the actual graph/pins, exhaustive cutset partition and intermediate ranks | Exact conditioning is implemented; a smaller-parameter Appendix D packet schedule and its proof are **not** implemented |
| 4. Partial relations | `partial::NestedBase`, `Collector`, `partial::solve`, independent `partial::verify` | Up to two outer points per admitted row; sparse elimination/storage can dominate |
| 5. Binary specialization | `binary::Field`, `Koblitz`, `XorBase`, `OrbitPolicy`, `OrbitBase`, shared generic selector engine | Odd-degree Koblitz models only; changed hash distributions need new coverage analysis; official full binary setup is not certified by the field-only test |

## CLI and integration

`hashed-ecdl solve-selectors PROBLEM.json NEW_RECEIPT.json` uses inverse-hash
selectors, caches bounded decodes within a query, enumerates smaller domains
first and derives the last slot from the group equation. Sorting domains
never interchanges slot/point columns. The returned decomposition receives
full membership/subgroup/sum replay before entering the unchanged reduction.

`hashed-ecdl solve-width PROBLEM.json NEW_RECEIPT.json` applies bounded
rank planning and exact local-support witness propagation to the existing
coordinate network. Default policy is rank 16 and at most 16 conditioned
edges; it can return a resource error on even small arithmetic networks.
It never silently changes to another algorithm. `solve` retains the original
backend. All three produce receipts checked by the same `verify` command.
No new CLI command is a promise of practical challenge-size execution.

Library clients can use `reduction::solve_with_oracle` or
`reduction::decompose_with`. An oracle receives the query point and public
bases, not random relation labels or the label RNG. Returned point witnesses
are independently replayed. `finite::selector_network` supplies a separate
graph with selector inputs; clients choose its contractor explicitly. Its
counts are distinct decoded tuples, not cofactor-projection assignment counts.
The scalar decoder uses a separate deterministic nonresidue-search stream;
it never consumes the reduction's random labels. Exhaustion propagates as an
error. The schoolbook encoder is explicitly selected and does not replace
the default Fourier multiplier.

## Exact contraction and local planning

`width::plan` uses a greedy minimum-rank order and selects a cutset if needed.
`Plan::validate` rechecks the free-edge partition, pins and intermediate
factor scopes, even for a caller-edited plan. No high-rank truth table is
allocated before its rank and vector policy pass. Execution also checks live
table storage. `count` includes every cutset assignment and uses BigUint
arithmetic. There is no floating-point or approximate-zero fallback.

`width::witness` performs exact bounded-support propagation and branches on
remaining bits. High-arity predicates wait until sufficiently pinned. It
does not request count precision, and every result passes full graph replay.
Search order can select a different witness from prefix-count lexicographic
extraction. All work and memory limits are errors with unknown result;
only complete exhaustion returns None. Plans certify structural admissibility,
not a speedup. Source packet-recursion constants are unchanged.

## Nested-threshold collector

`NestedBase::new` requires identical prime and hash seed and ordered thresholds.
`partial::solve` generates bounded uniform labelled queries, searches the outer
domains without exposing labels, and sends valid relations to `Collector`.
Outer columns pivot before inner columns. All coefficients are modulo the
certified odd prime subgroup order, with explicit slot/point identities and
original-row provenance. This is not XOR cycle cancellation. Row, column,
provenance, work and storage policies remain explicit.

`partial::Certificate` is a library certificate with its own verifier; it is
not substituted into the source v1 JSON receipt. Replay checks every original
group equation, nested-base membership, all column cancellations and scalar
extraction. A degenerate dependency continues collection; exhausted attempts
are a resource error. Callers must discard a collector after an error.

## Binary fields, hashes and orbits

The binary implementation uses native polynomial arithmetic, Rabin
irreducibility checking, exact inverses, half-trace decompression and checked
Koblitz addition. Subgroup construction checks prime proofs, the generator and
full cardinality by Hasse uniqueness or bounded exact counting. A missing
large-prime proof retains the exact primality fallback; it is not a probable
prime certificate. `Field::new(131, x^131+x^13+x^2+x+1, ...)` is tested, but
that alone does not validate the full ECC2K-130 challenge parameters.

`XorBase` checks and inverts a full-rank binary affine map. It is usable by
the same generic `finite::decompose` engine. `OrbitPolicy::derive` obtains
Frobenius eigenvalue candidates from the known Koblitz polynomial and verifies
the selected candidate on the subgroup generator; no DLP search is used.
Representatives retain a coefficient and replay `[coefficient]point=rep`.
`OrbitBase` hashes the canonical representative and expands its complete
Frobenius/negation orbit in the selector decoder, including shorter orbits.
Duplicate orbit selectors are permitted; this is a witness domain, not a
parsimonious counting claim. Its changed distribution has no inherited
prime-affine coverage guarantee. No claim follows for prime-field curves,
and any future rho comparison must receive the same available symmetry.

Sources and prior negative results are retained in the
[finite-size review](https://github.com/isogeny-labs/crypto/tree/main/research/hashed_ecdl_finite_size_20261030).
The original frozen performance panel is separate and unchanged. Native image/
execution admission and a current execution-host checkpoint are still needed
before any scientific run; development tests do not establish performance.
