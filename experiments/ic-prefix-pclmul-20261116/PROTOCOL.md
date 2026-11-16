# AVX2 reduction with guarded wide or ordinary carryless products

Continue the original broad IC performance objective. This is a new candidate
and fresh experiment after the initial timing allocation lacked VPCLMULQDQ.
The failed initial admission, all raw data and no-SIMD conclusion remain in
experiments/ic-prefix-avx2-20261116; no rerun or replacement under that protocol.
See problems/ic-simd-host-capability.md.

Candidate: AVX2/PCLMUL is the required vector capability. Wide VPCLMUL products
are selected only when detected; otherwise four ordinary128-bit PCLMUL products
feed the identical four-lane AVX2 sparse-tail reduction. Dispatch occurs once
per chunk into separately compiled loops. Keep field inverse/matrix defaults,
exact scalar fallback for unsupported CPUs/fields/cache/exceptional pairs,
ordered first witnesses and x+1 keys. Record total vector pairs, ordinary-PCLMUL
pairs and wide-VPCLMUL pairs. Positive vector use is mandatory for timing.

Reuse exact five registered N15/18/21/24/27 curves and archived prefix bases,
d6/7/8/9/10,29/67/127/257/531 sign columns. No curve/base/seed search or
replacement. Freeze fresh public fixtures320..343 with existing locked StdRng
scalar/point/walk law before timing. Four modes form a2x2 comparison:
mitm-prefix scalar1024; mitm-prefix64 scalar64; mitm-vector vector1024;
mitm-vector64 vector64. All24 orders once per field. The two chunk sizes are
fixed from the preceding fallback diagnostics, with every new arm retained.
No adaptive winner selection. max_trials500000,m2,walk,original dense Gauss,
original field inverse. All setup/query/matrix/scalar checks counted in cold.

Same positive original-backend calibration per field, including lookup units,
reused unchanged across IC/rho. Native preparation includes allocation,
feature/field detection, inverse cache, table construction and cleanup once per
target. Require exact manifest input/params/backend routing and equal query,
relation/rank/matrix work. Plain/negation rho in separate fresh processes on
same point/seed,2million trials each. Reverse reference order and place block
after IC on odd fixtures, before IC on even. Pre/post scalar-prefix1024 fixture0
A/A0.85..1.15 with correct answers/frozen units. Retain every error,cap,OOM,
failed control,outlier,duplicate; no retries/resampling/cap extension.

Native preparation L4CPU4/8GiB900s, --apt time, CPU work only, locked-j2 default
release, compile780s; debug vector product test180s within job900s hard cap.
Exercise ordinary-PCLMUL products even on wide-capable hosts; native test must
accept at least50 field widths and match scalar products. Native table checks
full/x-only/cached/vector builders at1/7/64/1024/4096 chunks,100complete maps,
positive vector counts, exact archived points/columns and15loader controls.
Pin source including build.rs, compiler, binary, receipts and job metadata.

Timing L4CPU4/8GiB900s, --apt time, CPU work only, controller780s, attack child12s,
RLIMIT_AS8GiB, one pinned allowed CPU, GNU-time RSS/CPU/fault receipts. BEFORE
any target comparison, each of the five registered cases runs a30s maximum
native map/capability preflight on this exact timing allocation, with actual
positive vector counts and backend diagnostics required. Preflight is a
correctness stage outside the cold interval and within controller780s. If it
fails, retain the allocation/output as failed admission and do not choose a new
host. A successful earlier preparation is never used to infer timing capability.

[pcc:unverified] All24 targets per field required for raw headline diagnostics;
bootstrap10000resamples,seed20261116,linear quantiles, paired medians. Existing
independent Python arithmetic replays all completed IC/rho scalars. Requested
and exposed resources remain separate; unknown physical memory/speed/channels,
placement/throttle/OOM stay unknown. Frozen exploratory qualifiednull and
recordinvalid for promotion. Public materialization, calibration/loading,
process startup, native preflight and replay are separate; cold includes context,
base/table/cache construction/cleanup,allqueries,matrix,scalarcheck. No GPU,
cryptographic-size,asymptotic or broad-breakthrough claim from this panel.

Evidence requirements: four-mode immutable manifests/120workloads; native
kernel tests and100map checks; timing-host preflight; actual backend counts;
all480IC+240rho answers, controls and resource receipts; arithmetic replay;
raw files individually and losslessly bundled; editable diagrams/inspected PDF.
Original goal remains open after a scoped result. PCC custody fork/unsigned
standing is preserved, no ledger rewrite/waiver or host filtering.

Sources checked: owning koblitz_fast.rs simd512 and simd256 modules; failed
admission report/claim28dc44 and prior research-kb source receipts in the
initial AVX2 PROTOCOL.md. This extends an implementation capability, with no
mathematical novelty or absence-of-prior-art assertion.
