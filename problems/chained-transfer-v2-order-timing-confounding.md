# Chained-transfer v2 order-dependent timing nuisance

- **Status:** investigating
- **Kind:** statistical identifiability obstruction under unconstrained sequence-conditioned timing; empirical carryover on actual hardware unknown
- **Affected work:** [CT182 reader PR #1711](https://github.com/isogeny-labs/cryptanalysis/pull/1711), [CT183 producer #1713](https://github.com/isogeny-labs/cryptanalysis/pull/1713), [CT184 integration #1714](https://github.com/isogeny-labs/cryptanalysis/pull/1714), [CT185 falsification #1715](https://github.com/isogeny-labs/cryptanalysis/pull/1715), [root queue #3904](https://github.com/isogeny-labs/crypto/issues/3904)
- **Next action owner:** Chained ECDLP Transfers measurement research lane
- **Last updated:** 2026-11-17

## Problem

The current deterministic 48-packet, 8-block ABBA/BAAB cold-transfer panel cannot on its own distinguish intrinsic route speed from a *sequence-correlated* change in first-four-position timing. The v2 scorer may therefore attribute a time/order nuisance to treatment even though the mathematical counterbalance and trailing A/A controls pass. Whether the nuisance exists in the actual CT125 Rust measurement host is **unknown**. [pcc:unverified]

## Evidence and uncertainty

- **Observed:** CT181 already falsified fixed ABBA with a stationary positional null. CT182 added ABBA/BAAB counterbalance, and CT184 confirmed synthetic producer-to-reader serialization (all source-only). CT185 prospective protocol and source code generate a separate order-conditioned treatment null and call the exact pinned v2 scoring function; hosted exact-head CI and code-review standing are recorded in PR #1715. [pcc:unverified]
- **Derived, conditional:** Under physical A=B=1, slot multipliers (3,2,2,3) for ABBA and (2,3,3,2) for BAAB give A-slot sum 6, B-slot sum 4 in *both* arms' schedules. Four of each sequence per packet then return a 3/2 A/B estimator ratio, while identical trailing A/A controls return log drift 0. This is a constructive *counterexample* to a claim of robustness under arbitrary sequence-dependent nuisance. It is not a claim that real A/B has equal speed or that such a nuisance occurred during a hardware benchmark. [pcc:unverified]
- **Suspected explanation:** A test host could have sequence-associated OS/cache/thermal/process-launch state or carryover. No such measured confound has been established.
- **Missing capability:** An independently calibrated, prospectively frozen same-route sham in the first four treatment slots (and/or randomized/blinded order assignment and an estimable period/carryover model) plus admitted same-host native execution.
- **Does not establish:** No native timing bias, speedup, mathematical transfer obstruction, ECDLP solver result or signed PCC is demonstrated.

## What would unblock it

- [ ] Freeze a bounded same-route A/A *treatment-position* sham sequence, matched to the A/B allocation (not merely the existing trailing A/A pair), with explicit admission limits, source/executable hashes, and prespecified nuisance tolerance.
- [ ] Measure and report this sham on the same host, workload and clock, with original input/counter/output parity and an independently checked null/adjudicator. Include raw evidence and uncertainty; fail closed if the null calibration reveals allocation bias.
- [ ] Prefer randomized order assignments with independently replayed roster and a period/carryover diagnostic before interpreting a measured ratio as intrinsic speed. Passing these controls is necessary but not logically sufficient against every possible nuisance.

A passing calibration would improve *measurement interpretability* only. Complete cold ECDLP costs, independent artifact custody and signed PCC remain separately required.

## Next discriminating step

- **Action:** Execute the prospective CT185 source-only falsifier against pinned CT182 scorer. Then design a real first-four-slot same-route sham as a *new* protocol without changing frozen v2 evidence.
- **Inputs:** immutable original selected-48 public fixture, deterministic v2 roster, positive stationary control and treatment-null sequence-locked negative.
- **Limits:** no EKS/Spot/GPU or unapproved paid native workload; source-only CI is bounded to five minutes, no Rust child execution.
- **Outcomes:** If scorer yields 3/2 at the null, annotate v2 readout as non-causal without sham. If scorer rejects or null passes, inspect assumptions and arithmetic; do not infer native safety without a measurement. Any CI failure is retained and fixed explicitly.
- **Recheck trigger:** exact-head source CI, approved native preflight, new sham protocol or independent audit.

## Resolution and history

- 2026-11-17: CT185 protocol frozen before code. Prior source v2 controls checked, uncalibrated deterministic sequence nuisance modeled. Unresolved. [pcc:unverified]
