# Batched additions in a one-target binary index-calculus collector

[pcc:unverified] Protocol frozen before materializing fixtures384..407. Broad requested goal:
aggressive specialized native index-calculus optimization and measured algorithm
performance improvement. This panel tests one candidate; it does not replace that
objective or establish mathematical novelty. All producer results remain unsigned.

## Candidate and controls

Sixteen lanes share ONE public target Q. Each state maintains P=[a]G+[b]Q modulo r.
Native FastCurve pairwise batch addition amortizes inversion across independent
pairs. Reuse already paid jumps to initialize lanes; charge all initialization,
restarts, unused lookahead, allocations and destruction. Generate at most500000
points including identities and unused buffered points; do not extend this cap.
Global duplicate/identity guards, cofactor handling, row construction, matrix rank
and scalar checks remain. The schedule changes versus the incumbent; relation yield
is an observable. Native and scalar variants of the NEW schedule must match exactly.

Three methods: mitm-walk-incumbent, mitm-walk16-scalar, mitm-walk16-native.
All use product-based vector preparation1, prefix inverse cache, original field
inverse and incremental dense Gauss. Same predeclared chunk policy for all:
64 at N15/18/21;1024 at N24/27, fixed from earlier panels before fresh targets.
No lane-count or chunk search on these targets. Native request and actual backend,
pair calls/additions, generated/consumed/unused, pool costs and restarts are recorded.
Backend availability denotes the binary pairwise implementation; hardware CLMUL
support and vector preparation backend are checked separately on the timing host.

Five unchanged registered curve archives N15/18/21/24/27, d6/7/8/9/10 and
29/67/127/257/531columns. Exact identities/archive records in adjacent inputs.
Fresh public fixtures384..407 use the existing locked StdRng point/walk law.
All6method orders repeated4times per field, order=permutations[fixtureoffset%6].
120triples,360IC plus240fresh rho answers expected. Fixture scalar belongs only to
input generation/control/replay; algorithms receive Q, G and public metadata.

## Accounting and decision

Primary paired contrasts: native/incumbent and native/same-schedule scalar, using
collector_wall_seconds (ratio is reference/candidate; >1 lower candidate cost).
The clock begins before matrix construction and includes target-dependent walker
setup, relation collection, rank/scalar checking and owned collector/matrix cleanup.
Source audit: MITM field/factor-base/pair-table preparation uses public field/base/G
metadata and does not use Q. Report base/setup separately. This is a one-target
computation interval with reusable preparation excluded; no target amortization.
Supplementary: context_ns + computation_through_cleanup_ns, outer run_pipeline
return followed by explicit boxed-oracle drop before JSON. Report context/base/
oracle setup and diagnostic report overhead separately where exposed. Preserve old
internal elapsed fields without using them as complete-cold measurements.
Independent existing Python arithmetic replay is outside native intervals: report
its elapsed and CPU duration separately, do not silently add unlike-language replay
to native timing or omit final native scalar checking. Fixture materialization,
calibration, preflight, process startup and serialization are outside compute clocks;
GNU process-wall/rusage retained separately.

Fresh original-arithmetic plain and negation rho on the SAME point/seed, two million
trial cap each, separate processes. Use reference_compute_through_cleanup_ns for
symmetric target-dependent setup/walk/check/owned-cleanup interval. Reverse rho order
and place after IC on odd fixtures, before even. Report both references; no borrowed
multi-target or different-hardware result. Reusable-setup rho comparison is outside
this bounded panel and remains an open requirement for a qualified online claim.

Pre/post incumbent fixture0 A/A collector ratio .85..1.15, correct scalar and frozen
positive original-backend calibration (including lookup units). Retain all caps,
errors, OOM, outliers and failed controls with no retries, filtering or extensions.
Require exact source/method/input/calibration routing. Same-schedule scalar/native
must agree query/relation/rank/matrix work and semantic GroupOps, all deterministic
counters except native-request/backend flags; timing counters excluded. Incumbent
has a different query law, so its query/work counts need not match. Whole-panel
[pcc:unverified] Speed summary requires all24targets per field; do not choose successful subsets.
Frozen paired-median bootstrap10000resamples/seed20261116, linear quantiles. Report
95% intervals, paired ratios, relation yield/query counts, memory, unused work,
AA status and compute/reference ratios. A primary interval above1 with correctness
and controls supports only a raw exploratory improvement for that interval/field.
Intervals spanning1 are inconclusive. No broad/asymptotic/cryptographic-size or GPU
throughput claim follows. No default promotion from this unqualified panel.

## Execution and admission

Native preparation: one L4 allocation,CPU4/8GiB,900s, --apt time; CPU execution.
Locked-j2 default release compile780s. Manifest exact archives; native table smoke
125complete witness-map comparisons plus15synthetic loader checks. Bounded release
walker checks512states per field, exact native/scalar/lazy/eager streams and a,b/Q
identities; independently replay exported2560states with existing Python field/group
code. Native debug tests filter batched_walk,180s cap; preserve every failure.
Pin source, compiler, environment, binary, receipt and raw source-job metadata.
Preparation tests all scalar/native exceptional pair fallback in existing controls.

Timing: one L4 CPU4/8GiB900s allocation, --apt time, controller780s, child12s,
preflight30s, RLIMIT_AS8GiB, pin one allowed CPU, GNU time rusage and cgroup snapshots.
Before any targets all five same-allocation table and walker preflights must pass,
positive vector pairs and backend avx2-pclmul128 or avx2-vpclmul, has_clmul true,
native walker pair count positive/backend1, scalar backend0, complete stream equality.
Unsupported host is a preserved failed admission; no host selection or retry.
Physical host/memory placement, channels, speed and unavailable counters stay unknown.
All Modal/gVisor timings exploratory, qualifiednull, bench recordinvalid for promotion.
No trusted signed execution/performance verdict exists. Keep custody fork unchanged.

Publish this protocol/source before fresh workloads, and frozen inputs/prepared
binary bindings before timing. Checkpoint gate before every launch/materialization.
Raw artifacts and lossless SHA/URI bundle uploaded BEFORE closing each record.
Retain source-linked report, editable diagram/plots, PDF and inspect every page.

## Sources checked

See ../ic-native-profile-20261116/NEXT_LEAD.md and COST_WINDOW_ERRATUM.md for the
profile evidence, exact KB source IDs/revision and primary-source scope. Known
Montgomery batch inversion is not a new mathematical mechanism. Atlas matching
closed_known generic batched-inversion lead and prime constant-engineering track:
prime wider-lane negatives and withdrawn multi-target rho comparisons do not
transfer here. Owning BinaryGroup, FastCurve, collector, MITM preparation and timer
code inspected. No curve/isogeny-route facts change; canonical curve catalog,
experiments/volcano-ic/figures and corresponding route figures remain current.
