# Integrated M31 end-to-end experiment, prospective local protocol

User request: tie the relation components into an end-to-end solver and
make it fast. Preserve the earlier component-only experiments. The input
is public curve/group data and Q coordinates, never d or planted summands.
Use E/Fp: p=2147483647, y^2=x^3+2x+14, N=2147505293,
G=(1,814455902). Local CPU runs/storage remain explicitly authorized.

## Implementation and hypothesis

The new target-independent signed pair index stores all collision witnesses
and probes m3/m4 through batched exact additions. This combines retained
partial-sum/sign witnesses, balanced m4 splitting, canonical x/sign lookup,
native exceptional arithmetic and the original public-coefficient walks,
sparse coefficient elimination and full scalar/row/cancellation verifier.
The hot path uses rational points, so no nonrational-root salvage call is
necessary. Polynomial alternatives remain available for diagnostics; they
are not forced into a large-domain per-query solver.

Hypothesis: paying O(B^2) setup and memory once per target reduces repeated
decomposition work enough to produce actual M31 recoveries faster than the
existing same-base direct split search. The batched m3 pair strategy already
exists in the suite MITM framework; this is native integration, not a claim
of a new MITM algorithm. Measure optimized m3 and m4 as pipeline competitors.
Reference baseline is the existing native PreparedSolver::solve_multi path
on exactly the same base, seed, query envelope and certificate verifier.
Do not claim improvement against an absent globally verified IC baseline.

Correctness before tuning: all nonzero targets on E/F127 of order109,
bothm3/m4, full certificate and forged-scalar checks; exhaustive signed
finite-domain comparison including identity pair sums; memory/scratch/base
guard checks; M31 planted point-sign/cache controls. Existing native tests
remain unchanged and must pass. Producer checks are not signed independent
verification; no new PCC IDs will be minted for synthetic known-answer cases.

## Cold boundary and common settings

Release Rust1.88.0 native worker. Fixed one thread; walker64 lanes; pair
chunk64; pair reservation at most4194304 raw witnesses; max2000000 queries;
native online soft cap5000ms; independent process20s/2GiB guard. Retain all
failures, caps and missing outputs. Fresh process for every timed cell.
CPU affinity is fixed to the first allowed logical CPU when taskset exists;
record actual mask/host/build flags and sampler/base seeds. Shared host has
no admitted isolation or hardware-counter claim.

Primary observation is cold_to_report_ns: main entry, argument parse,
base construction, group preparation, pair setup, online generation/solve,
complete internal certificate verification, an extra full replay, proof
serialization preparation and math-object teardown. It excludes runtime
startup and final stdout emission. Also record whole process lifetime under
the common watchdog, all phase costs, work, memory and the full certificate.
No reusable setup is free or amortized in a cold row. Profiling runs are
separate from timing rows and instrumentation overhead is not subtracted.

## Frozen development selection

Use two previous public targets only: (2144058214,807222724) and
(1764015007,688050509). Sampler/base streams are newly domain-separated
as specified in seeds.json; no wallclock randomness. No held-out target
coordinates are generated until selection.json is committed.

1.16 cells: interval base, B=64,128,256,512, m3/m4, two targets.
2. Select B,m by completed recovery count (both targets preferred), then
   geometric mean complete cold time, then smaller pair reservation. A
   capped configuration cannot win over one completing both targets.
3.4 cells: same B,m, torus subset/random bases, two targets. Reuse the
   interval observations from step1; choose base by the same rule. Torus
   subsets are explicit subsets of complete fibers, not claimed complete
   membership circuits. Record exact point lists.
4. Save selected configuration and the best completed interval m3 candidate
   as a separate optimized-MITM reference; commit selection before held-out
   fixture generation. No successful configuration is inferred if none
   completes both targets; diagnose and file a separate successor protocol.

## Held-out run (fixed five targets)

Native evaluator fixture helper receives derived private scalars, maps each
to1..N-1 and outputs Q; solver processes receive only Q coordinates. Scalar
custody stays separate from solver input/argv. Independent base/sampler
streams for each target are frozen in seeds.json before development data.

For each of five targets run: selected indexed pipeline twice in distinct
fresh processes (A/A repeatability/noise), same-base direct baseline once,
and the separately selected optimized m3 reference once. Alternate arm
order by target index. The A/A pair has identical input/seed; it is not an
independent target. Count every failure/cap and compare paired cold times
only when both complete with a valid full certificate.20 timed IC cells.

Five strong native C batched negation-map rho references use identical
public targets and sampler seeds, one thread and200000 group-op cap through
the existing ca-ic auxiliary CLI. Its enclosing reference-call interval
includes group/options construction, search and Rust final scalar replay;
keep search/replay and process lifetime separate. The unused one-query IC
wrapper overhead is not charged to rho's reference-call interval. Report
boundary differences explicitly; never treat rho as a hidden IC fallback.

One separate phase-profile run on development target0 uses the final
selected pipeline. Native timers locate stage costs; perf/valgrind/profile
wrapper are unavailable here, so do not invent PMU/sampling counters. This
run's time is not included in timing comparisons.

## Evaluation and allowed conclusions

Engineering target: all five held-out primary recoveries certify correctly,
with median measured cold time below1s on this local host. Every successful
answer must equal the evaluator scalar and replay Q, every row and every
cancellation weight. Keep the original verifier support and trust rules.
If timing target fails, retain it and investigate the dominant measured
phase under a separately recorded optimization; never relax the target.

Freeze analysis before held-out data: report completion counts, paired
costs, A/A spread, and conditional paired log-ratio/bootstrap intervals
(10000 resamples, fixed seed1729) for complete pairs only. Incomplete rows
remain in completion statistics and do not acquire a fabricated solve time.
The panel is exploratory and open-label, and local shared-host clocks lack
admitted isolation; no qualified speedup, asymptotic claim or rho victory
will be promoted. Full cold/setup costs and distance to rho stay visible.

Planned initial processes:20 development,20 held-out IC,5 rho,1 phase
profile =46. Unit tests/fixture preparation/replay validation are separate.
The canonical protocol schema/tool cannot be read in this checkout or
through the available source endpoint; this local narrative and seed file
are committed before outcomes, with no canonical admission claimed.
Source, commands, seeds, inputs, hashes, complete certificates, caps, raw
logs and report/PDF remain reproducible in the authorized local archive.
