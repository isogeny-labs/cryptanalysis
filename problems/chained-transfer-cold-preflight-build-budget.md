# Cold preflight compilation exceeds the original build envelope

- **Status:** investigating
- **Kind:** observed resource limit; engineering replay incomplete
- **Affected work:** [replay build protocol03](../experiments/chained-transfer-public-target/NONDUAL_REPLAY_BUILD_PROTOCOL_03.md), [timeout record](../experiments/chained-transfer-public-target/evidence/nondual22-cold-build-timeout-02/scope.json)
- **Next action owner:** continuing Chained ECDLP Transfers research
- **Last updated:**2026-11-14

## Problem

The original120s no-run build on fresh source72c69bec times out before
the unchanged isogeny engine finishes, so the new replay does not reach
any mathematical test. Both CI and fresh local execution have actual
compile124/tee0, runner1 and preserved source guards;5d8adb retains the
whole source, logs, artifacts and exact original checkpoint. This is not
a mathematical counterexample or evidence of impossibility. [pcc:unverified]

## Evidence and uncertainty

The last completed Cargo artifacts include the original GHS and public
target libraries; the original isogeny engine has no completion artifact.
The first relative-path launcher defect12665d was separately fixed748f1d.
No test executable or native record was emitted by the build timeouts.
The former warm-cache native27fb3a/6d2c97 observations are unchanged.
The cause within compiler optimization or host scheduling has not been
profiled; no runtime performance inference follows. [pcc:unverified]

## What would unblock it

- [ ] Under the prospectively declared protocol03, cold compile only the
  unchanged original engine within900s, preserve its complete Cargo/source
  custody, then pass all original120s wrapper builds and the entire exact
  native/control/proof/binding/source-guard matrix. [pcc:unverified]
- [ ] If claiming the original full cold120 envelope, separately demonstrate
  that full fresh build within120s. Engine preparation does not establish
  this criterion. [pcc:unverified]

The first condition would unblock replay in the new explicit resource
envelope. It would not satisfy the second, construct new Jacobian maps,
prove signed execution or show an ECDLP advantage. [pcc:unverified]

## Next discriminating step

Publish protocol03, add one900s engine-only preparation phase with unchanged
profiles and a fresh cache, and inspect exact Cargo reuse before the
original fixed matrix. Preserve timeout, build failure, unexpected reuse
failure and every later result. Recheck after that new bounded experiment;
do not silently extend a further deadline or weaken the checks.
[pcc:unverified]

## Resolution and history

Unresolved. Actual initial cold120 attempts in CI43629921346 and local
ct78-nondual22-full-01 remain negative resource records. [pcc:unverified]
