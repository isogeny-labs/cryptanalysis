# ECC2K-130 index-calculus relation yield

- **Status:** `open`
- **Kind:** empirical bottleneck and implementation gap
- **Affected work:** [fixed-parameter workflow](../suite/docs/ic/FIXED_PARAMETERS.md), [exact parameter profile](../suite/docs/ic/params/ecc2k130-fixed.json), [cold full-rank control](../experiments/ecc2k130-cold-fullrank-20261006/RESULT.md), [PR #1758](https://github.com/isogeny-labs/cryptanalysis/pull/1758)
- **Next action owner:** ECC2K-130 index-calculus research
- **Last updated:** 2026-11-18

## Problem

The exact public ECC2K-130 curve, subgroup, generator, target, basis conversion,
and frozen Hamming-weight-two factor base can now be constructed and checked by
the Rust CLI, but the challenge scalar cannot yet be recovered because no
full-size factor base and decomposition method has demonstrated sufficient
ordinary-target relation yield at an affordable complete campaign cost.

The affected instance is the Certicom Koblitz curve K_0 over GF(2^131), with the
published prime-order subgroup, generator, and target in
`suite/docs/ic/params/ecc2k130-fixed.json`. The requested acceptance criterion is
an end-to-end run that collects enough independently checked relations, obtains
the necessary rank, descends the public target, and replays the resulting scalar
as `Q = kP` on the exact curve.

## Evidence and uncertainty

- **Observed:** The checked-in weight-two profile materializes 14 signed
  Frobenius-orbit columns and 3,668 signed points in both the native Rust
  preflight and the durable workflow. The fixed-parameter guide records its
  three-summand uniform-target counting ceiling as approximately 1.21e-29.
  These statements are producer self-checks pending independent PCC standing.
  [pcc:unverified]
- **Observed:** The n=131 native preflight checks the exact curve, generator,
  target, Frobenius transport, basis map, and factor-base census without using a
  target scalar. Focused unit and CLI integration tests exercise that path.
  [pcc:unverified]
- **Observed:** The retained cold full-rank experiment explicitly concludes
  that its toy-curve controls do not supply n=131 relation yield, rank, target
  descent, or an end-to-end attack. [pcc:unverified]
- **Derived or proved:** No impossibility theorem is established. The counting
  ceiling applies only to the frozen weight-two base, the three-summand model,
  and uniformly distributed nonzero subgroup targets.
- **Suspected explanation:** The frozen base is too sparse for practical random
  relation production. A wider or differently structured base may improve
  yield, but its decomposition cost and linear-algebra size may erase that gain.
- **Missing capability:** A frozen n=131 candidate with measured ordinary-target
  yield, a resumable affordable collector, enough independent equations for the
  induced factor-base columns, and a completed public-target descent.
- **What this evidence does not establish:** It does not establish that index
  calculus cannot solve ECC2K-130, that no useful factor base exists, or that a
  bounded failed run is evidence of challenge security.

## What would unblock it

- [ ] Freeze a full-size factor-base and decomposition protocol whose blinded
  ordinary-target control produces reproducible nonzero relation yield whose
  witnesses pass independent group-addition replay, with complete setup, query,
  storage, and verification accounting. [pcc:unverified]
- [ ] Complete a resumable exact-parameter campaign that reaches the required
  independent rank, descends the published target, and emits a scalar replayed
  as `Q = kP` by an independent verifier.

The first condition establishes a viable relation source, not a solve. Both
conditions are sufficient for the requested scalar-recovery conclusion only
after the repository's evidence and independent-verification gates give the
result standing.

## Next discriminating step

- **Action or proof obligation:** Run the already identified bounded ordinary-
  target decomposition gate on one wider structured base, using the durable
  collector interface and preserving all failed probes.
- **Inputs and controls:** Pin the exact ECC2K-130 curve and subgroup, blind the
  target set before collection, include the current weight-two profile as a
  negative/sanity control, verify every returned decomposition by group
  addition, and report the induced base size and rank obligation.
- **Execution limits and stop condition:** Use the existing reviewed experiment
  and allocation rules; stop at its prospective query and resource limits or
  when its predeclared yield decision threshold is reached. This record does
  not authorize a new compute budget.
- **Outcomes and next actions:** A reproducible nonzero yield advances to a
  frozen rank-and-cost campaign. Zero yield is a bounded negative result for
  that candidate and redirects factor-base design. Excessive setup or query
  cost rejects the candidate on accounting grounds. Infrastructure failure is
  retained separately and does not update the mathematical hypothesis.
- **Recheck trigger:** A new full-size factor base, decomposition oracle,
  ordinary-target yield artifact, or complete campaign receipt.

A planned step is not a completed experiment. Apply the existing execution,
review, budget, and archival rules before acting on it.

## Resolution and history

Unresolved. On 2026-11-18 the exact-parameter Rust preflight removed the
wide-field parameter and factor-base construction gap; the relation-yield,
rank, target-descent, and scalar-replay obligations remain open. Completing
this record or merging its PR does not establish a research result.
