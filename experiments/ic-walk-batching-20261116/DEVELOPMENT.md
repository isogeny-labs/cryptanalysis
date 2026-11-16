# Development plan: batched additions in a one-target binary IC collector

Original scope remains aggressive specialized native index-calculus performance.
This applies a known simultaneous-inversion implementation to a new opt-in
collector schedule, informed by ic-native-profile-20261116/NEXT_LEAD.md. It makes
no mathematical novelty claim. Broad performance objective remains unresolved.

Proposal: sixteen states for the SAME public target Q; each state tracks
P=[a]G+[b]Q modulo r. Reuse the already paid jump points to initialize extra
states from one random start. Advance a bounded wave of independent pairs using
FastCurve::add_pairwise and its owned reusable scratch. Keep exact scalar mode
of this NEW schedule as a control, and preserve the incumbent guarded single walk.

Each state's next jump depends on its current affine point. This is a new
schedule/query law, not an identical replay of the incumbent. Global duplicate
and identity guards, coefficient arithmetic, row/cofactor construction, lazy
pooled restarts, rank criterion and scalar verification remain. Generated points
have their own hard max_trials budget, including identities and unconsumed
lookahead; no extra generated wave extends the cap. Generated/consumed/unused,
semantic pair additions, native backend requests/actual support, restarts and
pool costs remain counters. Charge initialization, all buffered unused work,
allocation and cleanup. No work is shared across challenge targets.

Correctness before timing: native/scalar schedules must emit identical points,
a,b and guard/restart streams; check every emitted P independently against aG+bQ
in bounded controls. Cover zero/one and non-multiple-of16 caps, duplicate/identity
restarts, eager/lazy pool behavior, generic scalar fallback, normal/exceptional
native point pairs, and complete pipeline scalar/rank/rows/work equality for the
same new schedule. A new schedule may change natural yield; the performance
comparison must measure it, not assume it.

Before timing fix the old clock boundary described in
../ic-native-profile-20261116/COST_WINDOW_ERRATUM.md. Add outer computation through
explicit oracle cleanup; matrix/collector interval includes owned matrix and
collector-buffer destruction; rho gets symmetric target-dependent cleanup.
Do not price these diagnostic clocks as primitive work. For MITM, preceding
field/base/table preparation is target-independent; independent Python scalar
replay remains separate with its cost visible. Preserve original internal fields
and all frozen raw data. No old ratio is promoted to complete-cold or online.

Performance protocol (not yet launched/frozen inputs): exact five registered
N15/18/21/24/27 archives, same bases; fresh public fixtures384..407. Compare three
methods: incumbent single walk, new16-state schedule scalar pair arithmetic,
and new16-state schedule native batch arithmetic. Use the same previously measured
chunk policy for all three:64at N15/18/21,1024at N24/27, with vector preparation,
original inverse and matrix. This policy is fixed from earlier panels, not selected
from the new targets. All6method orders repeated4times per field. Primary contrasts
are native-vs-incumbent and native-vs-same-schedule-scalar, on one-target compute
wall through verification/owned cleanup. Reusable setup and complete computation
through cleanup remain supplementary; fresh same-point original rho references.

Freeze exact source/method/workload/calibration metadata and a full PROTOCOL.md
before target materialization and native timing. Retain every failed/capped/AA
control/outlier and measure relation yield, queries, useful rank, memory and
unconsumed buffered work. Follow the standing isolation/PCC/resource gates; all
unqualified timing stays exploratory. Do not widen limits or select hosts.

Sources checked are recorded in the profile study NEXT_LEAD.md, including KB
revision9141e386254340a9bdba3036f2bb706a, owning collector/arithmetic code, atlas
closed_known batch-inversion lead and the prime engineering track's wide-batch
negatives. No source result from another field, target count or reference is
transferred into a new performance claim.
