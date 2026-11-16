# Direct S3 coefficient construction: producer evidence

[pcc:unverified] The optional direct coefficient path lowers observed S3
construction time in the frozen stage panel. All 30 pairs have equal canonical
coefficient checksums; all 32 assignment checks per process pass. No calibration
bound fails. Qualified values remain null on the unprepared gVisor host.
This run is invalid for promotion and does not establish full IC performance.

| Field degree | Basis dimension | Polynomial | Cold reference / direct | Build reference / direct | Median cold µs, reference / direct |
| --- | --- | --- | --- | --- | --- |
| 31 | 8 | S3 | 1.3956× | 4.0666× | 103.54 / 70.22 |
| 31 | 20 | S3 | 1.7115× | 2.2139× | 244.62 / 142.51 |
| 53 | 24 | S3 | 1.7707× | 2.0715× | 528.69 / 300.40 |
| 63 | 32 | S3 | 1.8937× | 2.0348× | 1210.39 / 651.92 |
| 23 | 6 | S4 | 1.0004× | 1.0011× | 4793.37 / 4823.07 |

Ratios are medians of six paired ratios, rather than ratios of the separately
reported median absolute times. Cold means fresh Gf2 context plus first descent
construction; field-polynomial selection, fixture generation, correctness
checks and serialization are outside this stage interval. S4 is the unchanged
path control and remains close to parity. Every individual ratio is retained.

## Implementation

The direct formula calculates each symmetric basis pair once, then emits
cross masks, linear masks and the constant in canonical order. It eliminates
generic polynomial maps and sorting for two summands. The generic default and
three-summand route remain available. Enable with `s3-direct-coefficients`.
The word-field implementation covers degrees at most63; it does not supply a
131-bit symbolic descent engine. Separate multiword field kernels are retained
in the preceding arithmetic reports.

The IC framework now charges symbolic descent and system packing in setup and
relation phases, including unsuccessful queries. That correction applies to
both variants and is distinct from the optional constructor change. Historical
S values must be rerun under this accounting before comparison.

## Verification and limits

[pcc:unverified] Producer checks: seven symbolic tests pass in default,
direct-feature and combined field-feature builds; each includes 140 ordered
coefficient comparisons across widths7/15/31/53/63, dimensions1/2/4/8/16/24/32
and four random/degenerate cases. The existing two algebraic-oracle pipeline
tests pass with default and direct builds. Library/probe clippy and formatting
of changed Rust files pass. The entire repository test suite has not run.

[pcc:unverified] Pinned Lean check006 passes for the algebraic identity and
symmetry, with all five lemmas audited using only standard foundational axioms.
This is partial formalization: Rust word arithmetic, memory operations and full
IC execution are outside that proof. The generic audit helper's Lean API
failure, initial proof/compile failures, and the interrupted expensive curve
fixture are preserved. The affected split test now constructs only the field
it needs, retaining its dimensions and assertions. Whole-suite formatting
also reports inherited differences outside the changed files.

The panel used one L4 allocation,4 requested CPUs,8GiB and a900-second cap;
CPU work finished in346.8 seconds including both release builds. It did not
measure GPU execution. Source and executable hashes, compiler version, host
snapshots, command outputs and all pairs are archived. Source/protocol were
pushed at84a7f723a197 before frozen fixtures60..65 were generated. Source claim
PCC-20261116-b2e44e and raw-observation claim PCC-20261116-80355e are unsigned
and not covered by independent standing.

Artifacts: [PDF](REPORT.pdf), [all ratios](ratios.svg), [mechanism](flow.svg),
[protocol](PROTOCOL.md), [proof scope](PROOF_MAP.md), [Lean source](S3Direct.lean),
[producer recomputation](validation.json). Raw values: run-001/summary.json,
pairs.json and arms.jsonl, hydrated through their artifact manifests.

Next discriminating measurement: actual relation/IC execution against the same
current baseline, including equation construction, solvers, failed queries,
linear algebra and scalar verification, with exact curve/base/target identities
and the same-target rho reference. Constructor ratios alone leave that total
algorithm result unresolved.
