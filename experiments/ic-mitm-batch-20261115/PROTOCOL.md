# Bounded batch-inversion MITM preparation: full cold comparison

Hypothesis: native binary negation-folded pair-table preparation can replace
independent affine inversions with existing exact FastCurve::add_pairwise,
using bounded chunks. Preserve loop order, first witness per abscissa and the
query path. Default chunk1024, bounded1..65536. All map allocation, scratch,
exceptional additions and batch inversion work belong to cold setup. Native
preparation nanoseconds replace hypothetical independent-addition pricing;
never count both, and preserve complete cold wall as a separate measurement.
This is an implementation specialization of existing Montgomery batching.

Reuse exact registered N15/N18 curves, fields, generators, prime-order cofactor
quotient policy and archived prefix bases dim6/7,58/134 rational lifts,29/67
sign columns. No curve/base search. Freeze fresh target fixtures136..141 before
materialization, locked StdRng scalar/point/walk law, keep accidental duplicates.
One-target immutable workload and source/candidate identities before timing.

Compare one default release executable, runtime modes: original negation-folded
MITM, native batched MITM chunk1024, cached column-affine with residual12 and
complete subtraction fallback. All six method orders across six fixtures. All
use m2,walk,incremental-gauss,50k trials. Same exact point/base/walkseed; original
and batched MITM must return exact same witnesses and deterministic relation,
trial and matrix counts. Preserve any mismatch and treat it as invalid, never
filter it away. Plain and negation rho complete on each exact point/seed.

Before/after original MITM fixture0 A/A bound0.85..1.15. Fresh process each arm.
Full cold: context, base, oracle/table setup, successful/failed queries, signed
lifting, collection, matrix and final verification. Keep context-inclusive
counted-S, pipeline counted-S, cold wall, wall equivalents, calibration, process
and replay intervals separate. All frozen triples required for headline median;
partial data and every cap/failure/outlier remain visible. Existing independent
Python arithmetic replays every completed scalar answer.

Separate CPU4/8GiB900s preparation, compile780s, locked-j2 unchanged release
profile. Bind source/toolchain/binary hashes and archive-equivalent manifests.
One L4 timing allocation CPU4/8GiB900s hard,780s controller,12s per process,
one pinned allowed CPU. CPU execution only, no retry or extension. Container
gVisor placement unqualified; qualified values null; record invalid for promotion.
Upload raw files before closing record. Previous fixed panels retained.

Owning PairTable constructor and FastCurve::add_pairwise inspected; existing
native batch addition is prior work. This is not an algebraic novelty claim.
The current-source column panel has its own frozen binary and must remain
separate from this later code. PCC chain fork still requires custody-preserving
reconciliation; no trust edits, waiver, promotion or merge bypass.
