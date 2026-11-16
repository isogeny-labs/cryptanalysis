# Direct S3 in complete fixed-instance IC execution

[pcc:unverified] All48 paired cases completed on the twelve frozen one-target
workloads. All96 pipeline answers match their manifests; same-method non-timing
counts agree between generic/direct builds. Both plain and negation-map rho
complete for every workload, giving24 reference answers. Existing independent
Python field/group arithmetic reproduces all120 scalar-to-point checks. These
are unsigned producer checks, not signed execution standing. Claims
PCC-20261116-ed23f0 and PCC-20261116-2d1adb record the observations and replay.

| Method | N15 cold reference / direct | N18 cold reference / direct |
| --- | --- | --- |
| buchberger-f2 | 1.037624× | 0.999717× |
| f4-f2 | 1.066591× | 1.030510× |
| fes-f2-wide | 1.106034× | 1.050697× |
| mitm | 1.005862× | 1.004081× |

Ratios are medians of six same-target paired ratios. Higher values mean less
time in the optional direct-constructor build. The cold interval includes fresh
field/curve context and the first full pipeline execution: base construction,
oracle setup, all failed/successful queries, solver, relation LA and scalar
verification. Input loading, planted-input generation, benchmark calibration
and output encoding remain outside it; outer process time is retained.
No compiler executes in this timing allocation.

## What this changes

[pcc:unverified] The constructor change moves the full algebraic-pipeline raw
medians by about0–11% on this panel. MITM remains the fastest tested method on
both exact bases; the constructor has no algorithmic effect on it. Therefore
these measurements do not establish a gain over the best tested IC pipeline.
This result changes the next optimization priority from equation packing to
avoiding the expensive oracle work and quadratic-size pair-table preparation.

[pcc:unverified] Reference MITM medians: N15 cold wall0.672993ms and
context-inclusive counted S22.404693; N18 cold wall1.284538ms and counted
S37.847719. Median per-target counted-S gaps to matched negation rho are
2.520450 and5.106161; raw cold wall gaps are4.215321 and7.130182. Each ratio
uses the same target and its actual completed reference. S is the existing
framework cost model plus separately measured context conversion. Complete
wall-derived equivalents are distinct and retained; partial native counters
must not be mistaken for a complete instruction ledger.

[pcc:unverified] On N18, median MITM table preparation is730056ns against
1172456.5ns median pipeline time (about62%, a ratio of medians). This motivates
the native affine S3 core already implemented in
suite/src/cryptanalysis/s3_affine_projection.rs. Its three focused tests pass,
covering exhaustive small even/odd fields, dense subspaces through degree63,
and explicit unsupported-input/cap outcomes. It has no signed-point adapter,
IC integration or performance result yet. The existing half-trace/projection
mechanism is prior work, and the general section is not a novelty claim.

## Standing, controls and retained failures

The timing job20261116-055509-28d3 completed with no per-arm caps. One N15 MITM
before/after A/A ratio fails the frozen0.85..1.15 bound. One N18 direct MITM arm
(fixture103) has cold ratio0.031768, with a43.338ms pipeline interval; it remains
in every plot and raw file. Its cause is unresolved. No rows are removed.
Known gVisor placement evidence is incomplete. Qualified values remain null;
the benchmark record is invalid for promotion regardless of answer agreement.

The original run-001 reference compilation reached its330-second cap and stays
censored. It produced no algorithm output. Separate build preparation completed
from source8e638a9aa53b and passed both native manifest checks. Hashes and compiler
metadata are frozen in prepared-input.json; timing used those exact executables
from the retained volume archive. Timing-controller source was publishedd6bd907c6d
before launch. Later affine prototype source is not part of those executables.
The record keeps preparation, attack interval and process cost separate.

Artifacts: [PDF](REPORT-timing001.pdf), [paired ratios](ratios-timing001.svg),
[absolute method costs and rho](costs-timing001.svg),
[protocol](PREPARED_TIMING_PROTOCOL.md), [original capped attempt](REPORT.md),
[analysis](analysis-timing001.json), [independent arithmetic replay](independent-arithmetic-timing001.json)
and raw timing-001 outputs through their SHA-256 manifests.

[Next implementation](NEXT_LEAD.md): complete signed lifting, explicit
degeneracy and cap handling for the native affine core, then test its setup/query
tradeoffs against MITM on fresh frozen targets with full same-target references.
The broader performance objective remains active and unachieved.
