# Timing boundary and accounting correction

Source `25049631bc58ca848cbb00169eda193529d9fc87`, baseline `fcbaca78`;
claim `PCC-20261116-d1cfbe`, unsigned/unverified. This is an accounting change,
not an algorithmic or measured runtime improvement. [pcc:unverified]

The target point was previously constructed/checked before the IC caller
clock, and a profiled report's primary online field described only the core.
The optional rho clock stopped before its final Rust scalar replay. Version 2
puts the supplied target-point validation after reusable preparation and
inside the IC caller interval; it also charges rho's final scalar check.
Neither correctness check is removed. [pcc:unverified]

For a profiled v2 IC report, integer nanoseconds obey
`online_wall_ns = input_validation + core + call_overhead`. The core retains
its seven exclusive phases; it is nested, not an additional charge. An
unprofiled core/overhead stays null. The observed CLI partition separately
charges preparation, pre-online bookkeeping, online, reporting and rho
reference. IC's observed total excludes that reference interval. Rho's native
operation count excludes the Rust replay even though wall time includes it.
[pcc:unverified]

Upstream auxiliary preparation, process start/exit and independent replay
remain unknown; `cold_total` and qualified speedup stay null. The CLI interval
ends before accounting serialization. It is not the full process or a fully
verified single-target interval. Version 1 outputs are preserved with their
old core-only profiling semantics; the checker reads them separately and
refuses mixed-version comparisons. [pcc:unverified]

| Check on this source | Unsigned producer outcome |
| --- | --- |
| Targeted CLI | Ten tests pass |
| Python comparison checker | Fifteen test methods pass |
| Actual v2 public three-arm fixture | Aligned |
| Archived v1 public three-arm fixture | Aligned separately |
| Strict CLI lint/format, fatal-warning stable and Rust 1.78 core docs | Pass |

The actual report hand-off uses the existing **p=127 correctness fixture**.
Scripted-duration controls cover reference exclusion, exact sums, invalid
boundary order, nanosecond overflow and unknown unprofiled costs. Existing
recovery, bounded-stop, replay and rho scalar checks remain. Malformed v2
reports cannot manufacture a cold total or hide validation/wrapper costs.
Commands, exits, complete outputs and input/report digests are retained by
[the validator](validator.json). These are producer consistency checks, not
signed execution or benchmark evidence. No failed development command was
observed in this scoped validation. [pcc:unverified]

Core arithmetic/solver modules, native consumers and the original frozen
snapshot have no changed paths. Earlier test/hosted receipts keep their own
source scopes. No fresh 31/61-bit target panel, calibration or performance run
is supplied. The comparison still needs upstream/process cost capture,
checkpoint/runner access, admitted frozen inputs and independent signed replay.
See [the plan](PLAN.md) and [measurement qualification problem](../../../../problems/prime-field-auxiliary-ic-validation.md).
[pcc:unverified]
