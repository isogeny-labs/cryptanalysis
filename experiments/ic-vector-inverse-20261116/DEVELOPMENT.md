# SIMD products in the existing four-accumulator inverse

Requested scope remains specialized native arithmetic and measured IC performance.
The preceding constant-reduction panel is frozen separately. Its table-only code
change moved the scoped setup-included interval; collector interval remained
inconclusive. This successor changes the existing inverse product passes, keeps
one scalar inversion and the same field/point/query/base/matrix/guard semantics.

Gf2.batch_inv ALREADY interleaves four scalar accumulators. Proposed engineering:
pack those products into four AVX2 lanes using existing ordinary-PCLMUL polynomial
products/reduction. Bounded8..16element stack kernel; peel multiplication by the
initial identity and the unused terminal accumulator updates. Zero inputs remain
zero, padded lanes are1 and their work is charged/reported. Unsupported host/field,
noncanonical denominators and other lengths retain the existing batch inverse.
Full point formulas and initialization remain as before; activation is opt-in.
No allocation in the inverse kernel; exact actual element/batch/padding counters.

Before timing: all accepted field widths, zero patterns, lengths0..31, direct
existing batch-inverse comparison, actual curve-point API checks, append/scratch/
exception controls; full scalar/native/vector/vector-inverse512state traces with
coefficients, forced restarts, eager/lazy pools and generation caps. Framework
same-schedule work/rank/row/scalar controls and independent Python replay remain.
Freeze source/controls/protocol then fresh workload manifests before target timing.

Sources checked: KB source:d246eaa2741bee8d9c7128d2c1e3e2de,
crypto-autoresearcher:knowledge/frontiers/ecdlp/generic-rho/KR-RHO-cb1c58.yaml,
published internal-analysis/evidence none/not superseded; owning YAML read.
Atlas match four lane SIMD Montgomery batch inversion prefix products reviewed:
KR-RHO-cb1c58 known and LEAD-RHO-batched-inversion-shared-pm closed_known. No new
batch-inversion mechanism or mathematical novelty assertion. Owning primary
Gf2.batch_inv_body, Simd256 multiply/reduction, FastCurve.add_pairwise_vector,
CountedGroup and BatchedWalker read. Existing group coefficients/field identities
are retained; canonical curve catalog and volcano/isogeny-route graphs unchanged.
