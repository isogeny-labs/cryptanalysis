# Prime-field auxiliary-map IC measurement qualification

- **Status:** open
- **Kind:** independent-validation and empirical-qualification gaps
- **Affected work:** [retrospective import](../experiments/prime-field-auxiliary-ic/README.md),
  claims `PCC-20261115-288dc5` and `PCC-20261115-bb0887`
- **Next action owner:** explicitly unassigned; no new experiment is scheduled
- **Last updated:** 2026-11-15

## Problem

The imported 31-bit CPU measurements cannot establish a repository-qualified
IC performance improvement because signed independent replay, admitted
isolation, a fresh target panel, and exclusive online timing are absent.
[pcc:unverified]

The exact instance is `p=2147483647`, `y²=x³+2x+14`, order `2147505293`,
`P=(1,814455902)`, `Q=(988441464,1643383878)`. Three search seeds reuse that
known target. The historical full-wall interval includes reusable preparation
and process startup and is not the repository's primary online interval.
[pcc:unverified]

## Evidence and uncertainty

- Observed artifacts: [frozen source inventory](../experiments/prime-field-auxiliary-ic/SNAPSHOT_SHA256.json),
  [raw latest records](../experiments/prime-field-auxiliary-ic/snapshot/algebraic/optimized/results/field31_s5_base0/),
  [unsigned recomputation](../experiments/prime-field-auxiliary-ic/producer-recompute.json).
- Historical `verified` flags describe producer checks. They do not provide an
  independent signed verdict or execution proof. [pcc:unverified]
- A separate certificate binds the public scalar equation only. It does not
  attest search method, work count, or native timing. [pcc:unverified]
- No mathematical obstruction or impossibility is inferred. Whether the
  measured differences persist under the admitted protocol remains unknown.

## What would unblock it

- [ ] Freeze exact canonical candidates/bases and at least five fresh public
  points after candidate selection, with a declared resource envelope.
- [ ] Meet the checkpoint, GPU execution, admitted placement/noise, and
  single-target online-accounting requirements before measurement.
- [ ] Compare the same public points with the strong repository rho reference,
  retain all failures/censoring, and obtain independent replay and signed PCC
  verdicts for the exact source and raw output digests.

These conditions would qualify the stated panel; they would not establish an
asymptotic result, superiority on every curve, or full 61-bit recovery.
[pcc:unverified]

## Next discriminating step

Prepare and review the immutable panel/protocol before running either arm.
Controls must include the preserved IC baseline, A/A checks, matched rho,
exclusive phase costs, and scalar/relation replay. Run only within an admitted
allocation and its explicit limits. A passing panel can support the bounded
claim; a failed qualification retains exploratory rows; an execution failure
retains the blocker. Recheck when an independent replay allocation and frozen
protocol exist. No such run is launched by this import PR.

## Resolution and history

2026-11-16, requested random-versus-special comparison: source `5e3a4202`
adds ordinary random equal-column subgroup bases and fixed-prefix relation
yield without early recovery, alongside the retained same-special-base direct
control. It includes cofactor clearing for the archived 61-bit subgroup.
The [comparison specification](../experiments/prime-field-auxiliary-ic/random-vs-special/COMPARISON.md)
requires all three arms, matched public query prefixes and separate full cold
recovery costs. The [scoped producer checks](../experiments/prime-field-auxiliary-ic/random-vs-special/README.md),
claim `PCC-20261116-8d7a97`, cover the implementation; they do not meet the
fresh timing admission criteria or demonstrate an auxiliary speedup. The
actual frozen panel, cost accounting and independent signed replay remain
open. [pcc:unverified]

2026-11-16, reviewed native-floor integration: upstream PR #1586 has merged;
source `bbdf695d` adopts its Rust 1.85 native/consumer floor. Both locked
all-target minimum-version checks and the separate stable correctness scopes
pass locally. This supersedes the earlier statement that the native floor is
still unrepaired, while preserving that failed check and its original scope.
The IC core's Rust 1.78 support is unchanged. Hosted CI, inherited GLV source
binding, CodeQL classification and timing qualification remain open. See
[the scoped follow-up](../experiments/prime-field-auxiliary-ic/rust-validation/ci-msrv-followup-20261115/),
claim `PCC-20261116-f7dd33`. [pcc:unverified]

2026-11-15, hosted CI follow-up: the dedicated Rust 1.78/stable and archived
Python jobs passed on `54e4331a`. A separate structured-consumer job reached a
stale wrapper lockfile after its earlier native checks. The lock was
synchronized while preserving the locked validation commands and package
versions. The corpus job instead stopped at inherited
[live GLV source-pin drift](live-glv-source-pin-drift.md); the known
[native Rust-floor gap](hashed-ecdl-rust-msrv.md) also remains reproducible.
See [the follow-up evidence](../experiments/prime-field-auxiliary-ic/rust-validation/ci-consumer-followup-20261115/).
These are integration observations, not a new performance result.
[pcc:unverified]

2026-11-15, native proof admission: Lean 4.35.0 was installed and six ring
identities compiled with standard foundation printouts. Source-bound corpus
admissions and six refusal/plumbing controls pass. See the
[additive proof note](../experiments/prime-field-auxiliary-ic/rust-validation/field-fibers-20261115/FORMAL_ADMISSION.md),
claims `PCC-20261115-8cb342` and `PCC-20261115-496600`. This supersedes the
missing-toolchain part of the history below; the structural finite-field
proof and measurement qualification remain open. [pcc:unverified]

2026-11-15, field-fiber leads: source `facaac33` pre-splits the terminal and
implements power fibers from p-1 and norm-one trace fibers from p+1, with
trace-orbit preparation and exact same-column direct IC controls. The
[field-fiber report](../experiments/prime-field-auxiliary-ic/rust-validation/field-fibers-20261115/REPORT.md)
and [receipt](../experiments/prime-field-auxiliary-ic/rust-validation/field-fibers-20261115/producer-checks.json),
claim `PCC-20261115-82ccdd`, retain 20 core checks on each toolchain and four
CLI checks, plus failures and the empty 61-bit degree-nine coset fixture.
These support implementation correctness only as unsigned producer evidence.
The requested runtime gain remains unestablished. [pcc:unverified]

The trace-orbit and homogeneous coefficient arguments have readable proofs
and six Lean identity sources, but no local Lean/lake toolchain is available;
no formal theorem or axiom audit is reported checked. Completing the formal
bridge requires the cyclic norm-one construction, primitive-trace criterion,
complete-fiber/orbit proofs and the target-group relation bridge. The shared
KB is unavailable and the relevant owning lead-atlas files are encrypted;
an owner checkout is needed to review/update those dispositions. These are
named tool/access and proof gaps, not mathematical obstructions.
[pcc:unverified]

2026-11-15, continued optimization: source commit `27fc983` shares the center
shift product and extracts candidate indices during evaluation. Explicit
polynomial-product checks cover mixed/zero shifts and a 128-root fixture across
multiple SIMD tiles with tail padding. The retained [kernel-fusion receipt](../experiments/prime-field-auxiliary-ic/rust-validation/kernel-fusion-20261115/producer-checks.json),
claim `PCC-20261115-d2f58b`, reports 15 core checks on each toolchain and three
CLI checks passing. This implements further arithmetic/indexing changes; it
does not establish a measured runtime improvement. [pcc:unverified]

Access probes found no expected local checkpoint credentials or Runpod API
key. The existing cloud-status workflow is `disabled_manually`, and its
read-only dispatch returned HTTP 422 without starting a job. Timing still
requires usable checkpoint/runner access and the admitted protocol; the
resource question has been sent to the user while code work proceeds.
[pcc:unverified]

2026-11-15, CI follow-up: the native dependency-consumer checks passed, but
the auxiliary workflow failed before any job started because repository action
policy rejected `dtolnay/rust-toolchain@master`. The replacement uses direct
`rustup` installation and retains the Rust 1.78/stable matrix, tests, lints and
documentation checks. Local workflow/toolchain checks passed; the corrected
remote workflow remains pending. See [the follow-up receipt](../experiments/prime-field-auxiliary-ic/rust-validation/ci-followup-20261115/producer-checks.json),
claim `PCC-20261115-2a4d0d`. [pcc:unverified]

Merge also requires maintainer classification of the current 23 CodeQL
annotations: three archived scalar fixtures and 20 logging sinks for the CLI's
mathematical recovery-witness data. The code-scanning API still returns HTTP
403. No alert was dismissed, check disabled or frozen evidence changed.
Successful CI would address repository integration; it would not discharge
the independent replay or measurement requirements above. [pcc:unverified]

2026-11-15, native integration: added a dependency-free Rust circuit and
bounded complete solver, a direct batched-subtraction IC control, safe Rust
re-exports, and `ca-ic auxiliary` with optional repository C rho. Correctness
checks cover both requested fields, complete small-field recoveries, public
31-bit row replay, and separate dense/C arithmetic controls. These are producer
checks; they do not resolve the empirical-qualification gap. [pcc:unverified]

Exact Rust-stage commands, source pins, logs and failures are retained in
[the producer check report](../experiments/prime-field-auxiliary-ic/rust-validation/producer-checks.json),
claim `PCC-20261115-c2f013` (unsigned). [pcc:unverified]

The checkpoint gate was retried for the Rust stage. It reported no AWS profile
`ecc-challenges-new`, no `CHECKPOINT_UPLOAD_TOKEN`, and no local checkpoint token
file. No checkpoint was uploaded, so no new research benchmark was launched.
Fresh-panel execution also still requires an admitted GPU allocation. The Rust
CLI leaves `qualified_speedup` and `online_exclusive_phases` null; replay mode
also leaves attack time and query counts null. [pcc:unverified]

2026-11-15: retained the existing implementation and raw evidence, explicitly
corrected the producer/independence distinction, and registered retrospective
benchmark records. Unresolved; merging the import does not qualify the timing
claims. [pcc:unverified]
