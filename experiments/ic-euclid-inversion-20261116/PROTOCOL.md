# Small-field inverse and matrix arithmetic: frozen factorial comparison

Objective: continue the user's broad IC performance goal through specialized
arithmetic, preserving full end-to-end scope. This experiment tests an engineering
candidate; a component or small-field result does not discharge the broad goal.

| Requirement | Evidence required |
|---|---|
| Arithmetic equivalence | Differential field inverses, general arithmetic, batch inversion and native full witness maps |
| Same target/pipeline work | Immutable candidates/workloads, exact scalar/point/seed, query/matrix count checks |
| Complete cost | Context, factor base, table/cache construction/cleanup, all queries, matrix, final scalar check |
| Fair reference | Separate fresh rho processes using both field backends on identical target/seed |
| Preserve uncertainty | Every target/control/cap/outlier, raw resource receipts, no replacements |
| Broad performance claim | Remains open; this panel is registered15..27-bit CPU evidence only |

[pcc:unverified] Use precisely the five registered curves and prefix bases archived by
experiments/ic-prefix-scale-20261116: N15/18/21/24/27, dimensions6/7/8/9/10,
29/67/127/257/531 sign columns. No curve/base/seed search or replacement. Reuse
exact archives and instance records; all max_trials500000, m2,walk,batch1024,
prefix-inverse-cache1 and x_only1. Baseline is the previous fastest engineered
prefix-cached candidate, not the original scalar builder. It remains unsigned
and unqualified; no claim of a verified baseline is invented.

Four modes in one default-release binary form a2x2 arithmetic comparison:
mitm-prefix (Itoh–Tsujii plus original dense Gauss), mitm-prefix-u32 (matrix
reciprocal only), mitm-euclid (Euclidean inverse only), mitm-euclid-u32 (both).
Euclidean inversion is opt-in for n<=32 with canonical input; wider fields or
noncanonical inputs retain the original chain. It uses polynomial degree/XOR
steps with u64 intermediates. No new arithmetic precomputation is omitted.
Matrix reciprocal setup/fallback and row scans stay in the full pipeline wall.
Defaults remain original. Neither arithmetic change has a timing result yet.

Freeze fresh public fixtures256..279 per curve before timing. All24 IC mode
orders, identical existing StdRng scalar/point/walk seed law. No resampling;
retain duplicate public points. Same positive calibration per field, including
lookup units, computed with the original backend and reused unchanged by all
IC/rho arms; do not reprice a candidate to itself. Whole native table setup
charged once for all arms. Query, relation, rank, matrix work and final checks
must match, despite timing differences.

Each target gets four separate fresh rho processes: plain/negation with original
arithmetic and plain/negation with Euclidean arithmetic, trial cap2million each.
Alternate order of these four processes by fixture parity; run reference block
before IC on even fixtures and after IC on odd fixtures. Report both references;
Euclidean IC must also be compared to Euclidean rho. No reference cherry-picking.
Pre/post original-backend prefix fixture0 A/A bounds0.85..1.15, requiring correct
answers/frozen calibration. All24 targets required for each headline; retain
failed controls, errors,caps,OOMs,outliers. No retries or cap extensions.

Native preparation: CPU4/8GiB900s, compiler780s, locked-j2 unchanged release.
Match exact archived points/columns; compare complete first-witness maps with
original, full/x-only/prefix builders at chunks1/7/1024 under both inverse
backends. Preserve source/toolchain/binary hashes and15 synthetic unit-loader
checks. No attack timing during preparation.

Timing: L4CPU4/8GiB900s, CPU execution only, controller780s, child12s, pinned
allowed CPU, child RLIMIT_AS8GiB and GNU-time RSS/CPU/fault receipts. Archive
requested versus exposed cgroup limits and unknown throttle/OOM/physical memory
properties. Frozen exploratory qualifiednull and recordinvalid for promotion.
Input materialization/calibration/loading/process startup and independent replay
are separate from the stated cold interval. Existing independent Python field/
group arithmetic replays all completed scalar answers. Bootstrap paired median
intervals use10000resamples,seed20261116,linear quantiles; keep all24 observations.
Do not infer asymptotics, GPU throughput or cryptographic-size gains from this.
Preserve previous reports and known PCC custody fork; no ledger rewrites/waivers.

Sources checked: research-kb query “Gf2 inversion Itoh Tsujii Euclidean inverse
performance single word” (lexical). source:c5b44937741b2f73ed2237dced16f1c1,
cryptanalysis:docs/perf/PERFORMANCE_INDEX.md (published internal-analysis, no
independent evidence); source:7eda92c8e608dbd71f4919c7b63481a1,
cryptanalysis:docs/SIDE_CHANNEL_SCOPE.md (same status). Primary owning code
suite/src/cryptanalysis/semaev_decomp.rs documents the existing Itoh–Tsujii,
Frobenius tables, batch inversions and the prior slower pentanomial shift fold;
no claim of mathematical novelty or absence of prior art. Current query/walk
and reciprocal controls derive from published a3f8238210 phase data.
