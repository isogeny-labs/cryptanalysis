# Production binary-subtraction speed-frontier admission

- **Status:** open
- **Kind:** access/tool limit; measurement and external-comparison gap; broader test qualification
- **Affected work:** [production study](../research/binary_subtract_frontier_20261115/README.md), [prospective protocol](../research/binary_subtract_frontier_20261115/PROTOCOL.md), crypto PR 4344 and cryptanalysis PR 1575 (earlier baseline PR 4335 retained)
- **Next action owner:** continuing baseline task; existing EKS/checkpoint operator for access prerequisites
- **Last updated:** 2026-11-15

## Problem

The native two-point oracle is implemented and has producer correctness evidence, but a speed-frontier result is not established because admitted matched timings, live budget/pool readback, external timed comparison and independent verification are missing.

The API is a first-witness search over ordinary binary curves on the existing single-word FastCurve backend (degree at most 62). Initial prospective pipeline rungs are K0/n13 and K1/n17; development/native checks also reach K0/n31. Complete ordered-relation enumeration, higher arity and cryptographic-size fields are separate workloads. The user's objective remains a faster baseline at the applicable frontier, with PRs in both repos. [pcc:unverified]

## Evidence and uncertainty

- Observed producer checks: five targeted controls pass in each repo; 12,900 general-arithmetic first-witness cases, 880 native-field/re-prepare cases, 90 OpenSSL-backed cases, actual known-answer pipeline recovery and extra-lane/failure controls. See evidence/production-controls.log under the study. [pcc:unverified]
- Execution access: the current executor has no EKS connector; actual AWS STS check in the preceding baseline exits 255 with no credentials. Current shared budget remainder and live pool capacity cannot be read. Cryptanalysis checkpoint custody is also required before an experiment.
- External control: OpenSSL 3.5.7 native binary inversion incorrectly treats the concrete finite Y=0 control as self-inverse; the preserved raw control and primary ec2_smpl.c source identify this case. A corrected comparator applies explicit affine negation with OpenSSL BN field addition before EC_POINT_add. Its timing wrapper remains to be admitted. [pcc:unverified]
- Broader qualification: full-suite commands/status are retained separately. Crypto's full optimized library-test build exceeded a 600-second local development bound; this is not an algorithm timeout or proof of a speed limit. [pcc:unverified]
- Derived/proved speed advantage: not established. Deferred ordinates and shared inversions are implementation mechanisms; unit-test elapsed time is not a performance measurement.
- Missing capability: authorized EKS/budget/pool and checkpoint access, exact admitted source/image/binary wrapper, current fastest-applicable external survey and matched timed runs.
- This evidence does not establish a fastest implementation, pipeline gain, field-size transfer or global record. It does not resolve the objective merely by recording the obstruction or merging code.

## What would unblock it

- [ ] Read current account/lane daily and monthly budgets/reservations and all-tenant pool/quota capacity using the existing authorized identity; satisfy Git/checkpoint custody.
- [ ] Build the frozen source with recorded source/image/executable hashes and admit L2, A/A, native replay and full-output correctness.
- [ ] Execute the named incumbent/candidate panel, retain every raw sample and failure, and independently recompute cost/ratios under the exact cold interval.
- [ ] Complete the external timed wrapper and matched reference review before a fastest claim; qualify broader tests on the exact head without bypassing their gates.

These are necessary admission/verification conditions. A run may show a loss; that keeps the actual winner as baseline and directs the next optimization rather than promoting the candidate.

## Next discriminating step

- Action: run the prospective crypto frontier-panel.json through the existing EKS native harness after all admission conditions hold; external and n31 component continuations remain explicitly separate.
- Controls: inherited scalar, full batch, lazy blocks 8/32/128, cold negation-folded table, strongest applicable rho and matching A/A. Preserve first witnesses for equivalent search variants, verify any table witness independently.
- Limits: proposed USD 5 total including builds/failures, 4 CPU/4 GiB, one job, original 900-second deadline, zero retries; existing cost controls take precedence and unknown remainder stops launch.
- Outcomes: a valid loss retains the incumbent; a valid win proceeds to holdout/scaling and independent verification; a measurement/admission failure is retained and repaired at its actual cause. No local timing substitute or quota/provider change.
- Recheck trigger: restored existing execution identity/budget/capacity/checkpoint readback or new admitted evidence.

## Resolution and history

Unresolved. On 2026-11-15 the continuation moved from tiny fixtures to both production backends, added native CLI/ecbench integration and general/OpenSSL correctness controls. No cloud experiment or speed-frontier declaration occurred. This record is mirrored in both repos so the requested timing objective remains visible.
