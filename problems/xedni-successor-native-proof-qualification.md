# Xedni successor native proof qualification

- **Status:** resolved for the five successor declarations
- **Kind:** corrected proof elaboration; successful source-bound native verification; historical artifact access limit retained
- **Affected work:** [bounded-witness successor](../experiments/xedni-bounded-witness-20261030/RESULT.md), PR #1288 and its original circular-hypothesis review
- **Next action owner:** CI repair maintainer
- **Last updated:** 2026-10-30

## Problem

The five successor declarations passed native compilation and their required exact declaration/foundation checks in job124071531124, run41058369134, at source9ea15c18e59e3d25f1cf637724a4f1a2dab3cc54. Their proof source is unchanged from the targeted elaboration correction. The earlier failures below remain historical; they do not qualify the new proof.

The successor replaces the circular universal bound on all integer relations with existence of a bounded witness under the explicit height/witness assumptions. Successful compilation and exact declaration/foundation audits remain required; the original fourteen historical declarations do not qualify it.

## Historical evidence and uncertainty

- **Observed:** Source `3c9337fe396ca2b5a638a21460b3c0862b708f99`, run41024184539/job123958270613, failed at `check_new_hecke` with lake exit1. The complete job log is preserved in [the diagnostics packet](../reports/ci-xedni-native-diagnostics-20261030/README.md). The runner retained exact command/stdout/stderr as command-n6vlrqgd but did not print the source path or compiler error.
- **Derived or proved:** All nine original sealed files and the successor witness source remain byte-exact. The 46 software process/custody/admission controls pass; these are not native proof evidence.
- **Suspected explanation:** Unknown. No guessed failing source or Lean error is asserted.
- **Missing capability:** Artifact ZIP access returned403; no verified local bytes of artifact12963207488 are available. Existing GitHub job-log access works.
- **Limits:** Neither this failure nor successful software controls establish a mathematical obstruction or a successful successor proof.

## What would unblock it

- [x] Run the existing native corpus workflow on the published diagnostics source with unchanged Lean4.35.0-rc4/Mathlib021c46 pins, proof admission rules and execution limits.
- [x] Compile the actual successor module and retain successful audits for all five declarations, including axiom-free output where applicable; retain exact source/dependency identity.
- [x] Pass every applicable current-head check and address the original P1 on the basis of that native evidence.

These conditions qualify the successor formal statements only. The height/Lang witness bridge and actual curve-selection sampling law remain open.

## Next discriminating step

- **Action:** Publish the existing gate diagnostics repair and inspect the next native corpus run. It prints the source before compilation and a bounded tail on failure while preserving complete original output bytes.
- **Inputs and controls:** Existing corpus and successor source, unchanged pins and all foundation checks; real-child-process failure/success controls verify the diagnostic path.
- **Execution limits:** Existing native corpus workflow and its original900-second per-source timeout; no new scientific trial or budget change.
- **Outcomes:** A compiler failure now identifies the precise source/error for a targeted correction. Success requires checking all five audits before resolving review. An infrastructure failure remains separately recorded.
- **Recheck trigger:** Next current-source native job output.

## Resolution and history

2026-10-30: Recorded the observed failure and preserved its complete job log. Added tested failure diagnostics without changing the theorem, proof policy or pins. Unresolved; publication of this record does not establish a proof.

2026-10-30 native diagnostics update: Source832e01578 run41042594820/job124018778233 identifies WitnessObstruction.lean errors at lines80,87,90: free-variable decide, integer-successor nonzero simplification, and natAbs/cast simplification. The targeted elaboration correction preserves every statement and principal proof. Core-only Lean4.34.1 compatibility controls pass: one is axiom-free and two use only standard propext; they do not qualify the pinned4.35.0-rc4 project. See [the complete failure and repair receipt](../reports/ci-xedni-proof-elaboration-repair-20261030/README.md). Fresh native5-declaration build/audits remain the exit condition.

2026-10-30 native resolution: source9ea's actual five-declaration successor build
and required standard-foundation printout checks passed in the pinned4.35.0-rc4/
Mathlib021c46 environment. All29applicable checks passed before PR1288 merged
as3e963f65113710cf0f90a20ca33841427554efcf; the original P1 was resolved.
The complete decoded successful job log and exact checker/source contract are
retained in [the qualification packet](../reports/ci-lean-source-admission-20261030/README.md).
Individual foundation sets remain in the command evidence artifact; this
record states only the standard allowed set actually enforced by the gate.
No lean4checker --fresh or artifact-ZIP verification is claimed. The separate
broad reports/ci-* discovery exclusion introduced by the final repair is
tracked in [its own admission record](lean-ci-evidence-source-admission.md),
where the source correction requires those three engineering lemmas to run.
The height/Lang bridge and curve-selection distribution remain open.
