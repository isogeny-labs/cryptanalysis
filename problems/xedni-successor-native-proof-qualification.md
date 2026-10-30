# Xedni successor native proof qualification

- **Status:** investigating
- **Kind:** observed native compilation failure; unknown precise source/error; artifact access limit
- **Affected work:** [bounded-witness successor](../experiments/xedni-bounded-witness-20261030/RESULT.md), PR #1288 and its original circular-hypothesis review
- **Next action owner:** CI repair maintainer
- **Last updated:** 2026-10-30

## Problem

The five successor declarations cannot yet be reported as kernel-checked because current-source corpus compilation exits nonzero before its retained compiler diagnostics can be inspected locally.

The successor replaces the circular universal bound on all integer relations with existence of a bounded witness under the explicit height/witness assumptions. Successful compilation and exact declaration/foundation audits remain required; the original fourteen historical declarations do not qualify it.

## Evidence and uncertainty

- **Observed:** Source `3c9337fe396ca2b5a638a21460b3c0862b708f99`, run41024184539/job123958270613, failed at `check_new_hecke` with lake exit1. The complete job log is preserved in [the diagnostics packet](../reports/ci-xedni-native-diagnostics-20261030/README.md). The runner retained exact command/stdout/stderr as command-n6vlrqgd but did not print the source path or compiler error.
- **Derived or proved:** All nine original sealed files and the successor witness source remain byte-exact. The 46 software process/custody/admission controls pass; these are not native proof evidence.
- **Suspected explanation:** Unknown. No guessed failing source or Lean error is asserted.
- **Missing capability:** Artifact ZIP access returned403; no verified local bytes of artifact12963207488 are available. Existing GitHub job-log access works.
- **Limits:** Neither this failure nor successful software controls establish a mathematical obstruction or a successful successor proof.

## What would unblock it

- [ ] Run the existing native corpus workflow on the published diagnostics source with unchanged Lean4.35.0-rc4/Mathlib021c46 pins, proof admission rules and execution limits.
- [ ] Compile the actual successor module and retain successful audits for all five declarations, including axiom-free output where applicable; retain exact source/dependency identity.
- [ ] Pass every applicable current-head check and address the original P1 on the basis of that native evidence.

These conditions qualify the successor formal statements only. The height/Lang witness bridge and actual curve-selection sampling law remain open.

## Next discriminating step

- **Action:** Publish the existing gate diagnostics repair and inspect the next native corpus run. It prints the source before compilation and a bounded tail on failure while preserving complete original output bytes.
- **Inputs and controls:** Existing corpus and successor source, unchanged pins and all foundation checks; real-child-process failure/success controls verify the diagnostic path.
- **Execution limits:** Existing native corpus workflow and its original900-second per-source timeout; no new scientific trial or budget change.
- **Outcomes:** A compiler failure now identifies the precise source/error for a targeted correction. Success requires checking all five audits before resolving review. An infrastructure failure remains separately recorded.
- **Recheck trigger:** Next current-source native job output.

## Resolution and history

2026-10-30: Recorded the observed failure and preserved its complete job log. Added tested failure diagnostics without changing the theorem, proof policy or pins. Unresolved; publication of this record does not establish a proof.
