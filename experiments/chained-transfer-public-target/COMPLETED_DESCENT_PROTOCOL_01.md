# N4 completed-transfer individual descent: prospective correctness candidate

2026-11-13. This document must be committed and normally published on ready
PR1523 before candidate implementation. It authorizes bounded development
correctness only. A benchmark needs a separate admitted performance protocol.

The question is whether the actual completed q223 map can replace the
original N4 rejection of nonsplit/exceptional transfer triples while retaining
all five public-target solves. Baseline: the frozen original public-target
solver in `native/derived/public_solver.rs`, four literal plumbing changes
from the original N4 solver, prospective protocol7e016c/f888. The current
candidate has no admitted cost advantage or candidate identity.

Use a new crate and whole solver derivative. Preserve all four original
files, P1, V1, V2 and all relation collection, factor-base selection, linear
algebra, logarithm assignment, descent walk and final verification bodies.
The function may accept CheckedInstance rather than an unbound Inst so that
the exact V2 field/model certificate is available. At the start of individual
descent, construct the actual V2 adapter with the actual chosen factor-base
P0. Charge its setup in any future accounting; do not move it outside a cold
comparison silently.

For each r0, r0+G, r0+Q, use the complete raw degree-six divisor space at
kappa(lambda⁻¹(P))=T−I(P), with exact field/model/P0 and complete fibres,
including multiplicities. The source group formula computes T−I(P) at all
points, including both missing old exceptional branches. Reduce this Gen
with the same original Picard engine at the same actual P0. Keep the affine
raw origin, because the original three-point difference cancels it. Never
subtract a fitted scalar or silently reinterpret final keys at another P0.

Replace only the original split-cubics triple admission with these complete
spaces and change the corresponding reduction input from fixed k3 cubics to
the actual complete Gen. Map errors fail the attempt explicitly; no old
split-map or generic-DLP fallback is allowed. Retain the original deterministic
random stream up to the first triple. A complete map should admit its first
triple; subsequent descent randomness may differ from the old rejection path.

Controls and fixed workload:

1. Use the same actual five public requests and outside known-answer metadata
   as P1: residues1,2,17,floor(ell/2),ell−1 on the frozen q223/seed1 source.
   No witness or scalar goes to either public solver.
2. Pair baseline and candidate under the original retry schedule, attempts1..6,
   c=2+0.4*(attempt−1), nfb=ceil(c*sqrt(223)), rows_mult1.2, max_desc100000,
   sge=false, maxw12, lp2=true, verify_rel=true, seed100+attempt. Preserve every
   failure and success, including first-attempt relation shortfalls.
3. All five candidate targets must solve within that cap and every reported
   baseline/candidate success must pass the original independent source check.
   Retain k_found, failure, phase logs/counters and all original statistics.
   Differences in individual-descent trials are observations, not a speedup.
4. Before solves, require complete raw classes to equal all actual legacy
   split classes in the frozen V2 panel at the actual winning P0; record the
   nonzero geometric origin. Require both actual public-point inverse and
   affine three-point cancellation controls, including a nonzero base.
5. One unfiltered serial Rust test contains these checks and all five paired
   solves. No ignored or filtered test is accepted. Compiler and native
   processes are separate, each bounded900seconds; runtime2GiB address space.
   A completed outside dependency cache may be reused and must be labelled
   non-cold. Freeze every actual source before launch and require final guards.
6. Preserve whole sources, exact literal diff, command/environment, original
   stdout/stderr and exits, every native record and all failures as one whole
   standard tar/XZ plus complete member index. Use genuine artifact migration
   when original policy requires. Never split/prune/rename to evade a limit.

Falsification: any wrong answer, missing target, exhausted frozen retry cap,
map/geometry mismatch, altered original relation/LA/descent body beyond the
explicit map plumbing, unreported failure, source-guard change or ignored test
rejects this correctness candidate. Preserve and diagnose it under a versioned
correction; do not redefine the five-target acceptance after observing a run.

The competing outcomes are fewer split-transfer retries versus larger complete
map/setup cost or changed descent behaviour. Original counters do not cover
all arithmetic in the separate completed-map engine; keep that coverage gap
explicit. A future comparison must include those costs, actual setup and
recovery, strongest applicable rho/precomputation references, one public target
per primary workload, A/A and positive controls, matched resources and complete
cold/online boundaries. This protocol does not admit that performance run.
