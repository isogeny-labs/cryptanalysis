# Packed characteristic-two squaring in cached IC preparation

Continue aggressive specialized native IC arithmetic optimization and the broad
performance objective. Baseline: current guarded AVX2/PCLMUL vector preparation,
including prefix inverse caching, original inverse and matrix algorithms. Compare
both frozen chunk sizes 64 and 1024; no adaptive winner choice. Prior compatible
panel and all negative/failed evidence remain immutable. This is an engineering
candidate, with no claim of mathematical novelty or absence of prior art.

Candidate: canonical elements a,b of at most 32 bits satisfy
(a + b*z^32)^2 = a^2 + b^2*z^64 over characteristic two. Each raw square has
at most 63 bits. AVX2 word shuffle 0xd8 packs adjacent 32-bit elements; one
wide VPCLMUL or two ordinary PCLMUL instructions produce four raw squares.
The existing sparse-tail reduction acts on these four words with high words
zero. Keep ordinary multiplication unchanged. Dispatch once per chunk to a
const-generic loop; packed helpers only execute for field degree <=32.
Larger fields retain product-based squaring. Unsupported CPU/field/base shapes,
exceptional point pairs, invalid denominators and remainder chunks retain exact
existing fallbacks. Add actual packed-square pair counts. vector_prepare=1 is
the original vector comparison; opt-in value2 selects packed squaring.

Prediction: fewer carryless instructions for the square component may lower
native preparation and complete cold cost. It may instead be neutral/regress
because shifts, packing, reduction or table work dominate. No whole-pipeline
gain follows from static instruction counts. Freeze this protocol before
new workload materialization/timing and publish the input commit before launch.

Exact five registered N15/18/21/24/27 curves and archived prefix bases,
d6/7/8/9/10, columns29/67/127/257/531. No curve/base/seed replacement. Fresh
public fixtures352..375 using the existing locked StdRng scalar/point/walk law.
Four modes: mitm-vector (product1024), mitm-vector64 (product64),
mitm-vector-packed (packed1024), mitm-vector-packed64 (packed64). All24 orders
once per field. max_trials500000,m2,walk,original dense Gauss/inverse. Primary
engineering diagnostic: paired product1024/packed1024 full cold ratio. Include
all other baseline1024 ratios and matched-chunk product64/packed64 diagnostic;
never choose a field-specific winner after seeing targets. This preparation
study is supplementary to the unresolved primary one-target online objective;
it does not replace that objective. Report setup/query/matrix/check intervals.

Same positive original-backend calibration per field, including lookup units,
reused unchanged across every IC/rho arm. Require exact input/params/routing
and equal query/relation/rank/matrix work. All target-dependent IC work and
setup/context/table construction and cleanup charged in cold diagnostic.
Two fresh original-arithmetic rho processes on the same point/seed,2million
trials each; reverse order and place after IC on odd fixtures, before even.
Pre/post baseline-vector1024 fixture0 A/A .85..1.15 with correct answers and
frozen units. Retain all errors/caps/OOM/outliers/failed controls; no retries,
resampling, filters or cap extensions.

Native preparation: L4CPU4/8GiB900s, --apt time, CPU execution only, locked-j2
release, compile780s and debug vector test180s inside job900s hard cap. Native
test compares selected-native and forced ordinary PCLMUL multiplication AND
packed squares against scalar arithmetic across >=50 accepted widths, including
larger-field square fallback. All five builders full/x-only/cache/vector/packed
at chunks1/7/64/1024/4096:125complete witness-map comparisons, positive vector
and packed-square counters, exact archives and15loader controls. Pin source,
compiler, environment, binary, receipts and source-job metadata.

Timing: L4CPU4/8GiB900s, --apt time, CPU only, controller780s, attack child12s,
preflightchild30s, RLIMIT_AS8GiB, one pinned allowed CPU, GNU-time rusage.
Before any targets, all five same-allocation native map/capability preflights
must pass25comparisons each, positive vector AND packed-square pair counts,
with total vector pairs exactly twice packed pairs and backend identified.
Unsupported allocation is preserved failed admission; no host retry/filter.
Never infer timing capability from native preparation's allocation.

All24 targets per field required for raw headline diagnostics; frozen bootstrap
10000resamples/seed20261116/linear quantiles of paired medians. Existing
independent Python arithmetic replays all completed480IC+240rho answers.
All timing exploratory, qualifiednull, recordinvalid for promotion. Requested
and exposed hardware distinct; unavailable physical placement, memory/speed/
channels and throttle/OOM unknown. Materialization, calibration/loading,
startup/preflight/replay are separate from cold. [pcc:unverified] No GPU-throughput,
cryptographic-size, asymptotic or broad-breakthrough conclusion from this panel.
Keep PCC custody fork and unsigned standing; no ledger rewrite or gate waiver.
Archive raw separately and in a lossless SHA/URI-pinned bundle before record
closure; retain editable plots/report and inspect all rendered PDF pages.

## Sources checked

Research-kb query: PCLMUL packed two 32-bit squares Frobenius. Read owning
koblitz_fast.rs simd256 and its product-based slope/square loops. Read primary
files from commit39340d0c7426800a3dc7ec81d762d1651d8ef03f using git show:
- source:26ff3fa625e3550521c3659d0fb6a75e,
  cryptanalysis:papers/ecdlp-constant/sec-ecc2k-arith.tex; primary-source,
  external-source,evidence_levelnone,notsuperseded. Describes characteristic-two
  squaring in a normal basis and packed polynomial products; does not certify
  this candidate or transfer normal-basis costs to polynomial-basis IC.
- source:68fe0ee5383e917e1c26273c773eb13d,
  cryptanalysis:papers/frobenius-orbits/sec-layout.tex; primary-source,
  external-source,evidence_levelnone,notsuperseded. Discusses orbit records and
  key packing, not an implementation/performance proof for this square kernel.
These are context, not independent evidence of the new source or timing.
