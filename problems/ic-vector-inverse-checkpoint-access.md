# SIMD inverse timing checkpoint upload access

- **Status:** open
- **Kind:** access/tool limit
- **Affected work:** [frozen SIMD inverse panel](../experiments/ic-vector-inverse-20261116/PROTOCOL.md), [prepared inputs](../experiments/ic-vector-inverse-20261116/prepared-input.json)
- **Next action owner:** environment operator for checkpoint upload access; T-6859 for the frozen panel
- **Last updated:** 2026-11-16

## Problem

The prepared SIMD inverse comparison cannot start because the required checkpoint upload fails before the timing launcher executes. The unchanged panel covers N15/18/21/24/27, fixtures456..479, three logical methods and two immutable native binaries. Source and fresh input manifests are published through commit `9d310eeb969f6a02da6434584fa548dc96ea37e9`.

## Evidence and uncertainty

- **Observed:** [Three admission logs](../experiments/ic-vector-inverse-20261116/admission-001/) preserve presigned POST HTTP403, profile `ecc-challenges-new` PutObject `InvalidAccessKeyId`, and profile `default` PutObject `AllAccessDisabled`. The official profile route was selected with a scoped environment; credential and token files were unchanged. No target timing launcher ran. These are producer observations, not signed verification. [pcc:unverified]
- **Observed:** `default` and `ecc2k130` authenticated to STS; bucket HEAD requests returned403. HEAD failure alone does not establish PutObject permissions. Only `default` was tested against the exact checkpoint prefix after successful STS authentication. [pcc:unverified]
- **Derived or proved:** no mathematical obstruction established.
- **Suspected explanation:** checkpoint storage authorization or bucket state; precise cause unknown.
- **Missing capability:** a functioning authorized checkpoint upload transport.
- **Limits:** this admission failure gives no timing result for the SIMD inverse kernel. Prior constant-reduction and vector-query panels retain their original scope.

## What would unblock it

- [ ] `scripts/checkpoint.sh gate` exits zero and uploads the current branch checkpoint through the supported token or profile route.
- [ ] Run the existing prepared controller once under the frozen protocol; retain every admission, control and replay outcome.

Successful checkpoint admission permits timing; it establishes no performance conclusion by itself. No gate bypass or credential-policy change is proposed.

## Next discriminating step

- **Action:** refresh the existing checkpoint transport, or identify an already authorized named AWS profile, then rerun the required gate.
- **Inputs and controls:** retain the two binary pins, fixtures456..479, six balanced orders, A/A controls, paired references and all replay checks in the protocol.
- **Execution limits:** one L4 allocation, four CPUs,8GiB,900seconds; no replacement allocation or sample tuning.
- **Outcomes:** gate success permits the frozen timing command; another failure is appended as access evidence. Measurements require the specified controls and analysis before interpretation.
- **Recheck trigger:** refreshed upload credentials/token or an authorized named profile supplied by the environment operator.

## Resolution and history

2026-11-16: unresolved. Three supported upload attempts failed before target timing. The benchmark record remains open with no commands, samples or metrics. Index registration is pending because `problems/README.md` is reserved by T-6315; this scoped record and the study handoff retain the link.

2026-11-16 17:21 UTC: rechecked the supported token route at published head64ef14113. The gate again exited1 with HTTP403; original log004 is preserved under admission-001. No timing command or allocation was started. Access remains unresolved. [pcc:unverified]

2026-11-16 17:22 UTC: the third consecutive goal-turn admission audit again returned exit1 HTTP403 at clean published head305e91a20. Log005 is preserved. No timing allocation exists. The performance objective is blocked pending a functioning supported checkpoint transport; the implementation and frozen panel remain ready. [pcc:unverified]

2026-11-16 19:24–19:25 UTC: after explicit goal resumption, three fresh consecutive audits at clean head918259a0b again failed checkpoint admission with HTTP403. Original resumed-001/002/003 logs are retained under admission-001. Repository artifact configuration still names the same bucket; no migrated destination was supplied. Timing remains unstarted. The goal is blocked again pending a functioning supported checkpoint transport. [pcc:unverified]
