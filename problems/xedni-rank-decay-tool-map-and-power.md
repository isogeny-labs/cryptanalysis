# Xedni rank-decay execution, evidence, point-map, and power gaps

- **Status:** open
- **Kind:** tool/access limit; implementation and evidence gap; resource limit
- **Affected work:** [rank-decay protocol](../research/xedni_rank_decay_20261118/PROTOCOL.md), [mechanism amendment](../research/xedni_rank_decay_20261118/AMENDMENT.md), PR #1768
- **Next action owner:** research agent for executor/evidence/inference gaps; environment operator for licensed Magma and checkpoint transport; research agent for the cubic point map and calibrated exposure plan
- **Last updated:** 2026-11-19

## Problem

The full requested 16--32-bit rank-decay falsification cannot yet produce its
decision statistic. The deterministic runner plans calibration and sentinel
rosters but intentionally has no natural-row executor. A production executor
still needs enforceable public/private phase separation, raw evidence and
complete relation-inventory binding, and a rigorous optimizer over mixed
per-prime unresolved counts. Separately, no licensed Magma executable is
available, the `r=7..9` plane-cubic lift lacks a certified Jacobian model with a
map for every selected point, the checkpoint gate lacks upload transport, and
direct exposure at the frozen slower-decay alternative is larger than the
available local compute. These are distinct gaps; none is a mathematical proof
that the decay law holds. [pcc:unverified]

The executable short-Weierstrass scope is `r=2..6`. PARI can supply certified
rank intervals, but the protocol requires independent Magma 2-descent for every
event and unresolved row. A Jacobian rank for an unrelated model cannot classify
the selected plane-cubic points. At `p=2^32`, 30 expected events require
`128,849,018,880` rows at rate `p^-1`, `503,316,480` rows at rate `p^-0.75`, or
`1,966,080` rows at rate `p^-0.5`, per cell before factorial expansion. Zero
events needs `50,260,046` independent rows merely to reject a rate at least
`p^-0.75` at 95 percent. [pcc:unverified]

## Evidence and uncertainty

- **Observed:** the managed environment has no `Magma` executable, license, or
  configured remote Magma route. A public PARI container is feasible and its
  adapter is covered by deterministic controls. [pcc:unverified]
- **Observed:** `runner.py plan` deterministically reports 1,080 executable and
  648 blocked `r=7..9` calibration rows, and 12,150 executable plus 7,290
  blocked sentinel rows. It has no natural-row command; this is a planned
  roster, not execution. [pcc:unverified]
- **Observed:** the bounded PARI height-pairing/LLL proposer recovers planted
  control relations only after exact rational and source replay. A rejected,
  trivial, or noninvertible candidate does not certify absence of a different
  useful relation, so ranked non-successes remain unresolved. [pcc:unverified]
- **Observed:** the current source record contains private ordered scalars.
  Selector material omits them by convention, but there is no hash-linked
  redacted public object plus separate evaluator process that makes scalar
  access impossible for the selector/proposer. [pcc:unverified]
- **Observed after explicit user authorization:** at pushed head
  `bfefa7c0a2a668643e3aabef5b6796b70a743b93`, checkpoint `push` and `gate`
  both exited 1 because the environment still had no upload profile, token,
  or token file. Zero natural rows started. Authorization resolved permission,
  not checkpoint transport. Claim `PCC-20261119-e03654` has unverified
  standing. [pcc:unverified]
- **Demonstrated anti-circularity gap:** M3 accepted values standing in for
  private scalar-derived data under the innocuous feature name
  `proxy_curvature` and used them for selection. The current key-name filter
  and selector hash therefore do not certify feature provenance. This canary
  does not assert intentional scalar use by an existing selector.
  [pcc:unverified]
- **Demonstrated implementation gap:** uniform all-failure and all-success
  allocations do not bound a slope. With admitted counts `(10,7)` and unknown
  counts `(90,93)` at `(p,4p)`, the two uniform signed slopes are about
  `-0.257` and `0`, while the mixed low-p-success/high-p-failure allocation is
  about `-1.918`. [pcc:unverified]
- **Partial implementation:** `mixed_censoring.py` now exhausts the full
  integer allocation box for bounded cases and has an independently
  brute-force-checked conditional-Poisson optimizer for the aggregate
  per-prime box. Binomial-cloglog remains exhaustive and state-limited, and
  cluster bootstrap correctly returns `BLOCKED` because aggregate per-prime
  totals do not determine within-cluster allocations. It is not integrated
  into the production analyzer. [pcc:unverified]
- **Post-authorization scaffolding:** `public_boundary.py` passed 33 focused
  controls including fully rehashed direct-DLP mutations; `natural_executor.py`
  passed 21 state-machine and durability controls; and `row_provenance.py`
  passed 48 mutation/path/inventory controls. All three fail closed for
  production: they are not wired into `runner.py` or `FREEZE.json`, there is
  no signed independent verifier backend, and provenance returns only
  `HASH_GRAPH_ONLY`, `production_eligible=false`. [pcc:unverified]
- **Observed:** the archived plane-cubic panel evaluates exact relations through
  `r=9`, but does not provide the certified cubic-to-Jacobian selected-point map
  required for full curve or selected-subgroup rank classification.
  [pcc:unverified]
- **Implementation route identified:** pinned Sage can construct an exact
  birational map with `EllipticCurve_from_cubic(..., morphism=True)`; the group
  map must translate by the image of the chosen chord origin and then verify
  every selected point and reduction identity. PARI `ellfromeqn` supplies only
  Jacobian coefficients. This environment has neither Sage/eclib nor Magma,
  and no adapter/verifier has been implemented. [pcc:unverified]
- **Derived:** the exposure numbers above follow directly from `30/q` and from
  `ceil(log(0.05)/log(1-2^-24))`; they are prospective power calculations, not
  measurements. [pcc:unverified]
- **Suspected explanation:** none. Missing licensed software, a missing map, and
  insufficient exposure are directly observed or calculated gaps.
- **Missing capability:** a natural executor with complete cost accounting; an
  enforceable redacted-public/private-evaluator boundary; executable binding
  of the frozen roster, prime, seed, raw transcripts, and complete relation
  inventory; rigorous minimization over all per-prime unresolved allocations;
  licensed Magma execution; an exact general-cubic Jacobian/point-map
  certificate; checkpoint transport; and an authorized resource allocation or
  a valid fixed-probability two-phase design large enough for the stated effect.
- **What this evidence does not establish:** the rank-event rate, the useful
  recovery rate, either decay exponent, or whether any amended lift family
  changes those rates. [pcc:unverified]

## What would unblock it

- [ ] A natural executor composes source, local, lift, invariant, relation,
  rank, recovery, and work-accounting stages without omitting failed attempts,
  duplicates, proposals, or raw transcripts.
- [ ] A hash-linked redacted public record contains no source/target scalar;
  selectors and relation proposal run in a process that can access only that
  record, while a separate private evaluator performs exact replay.
- [ ] An executable provenance validator reconstructs every row from the exact
  frozen roster, prime manifest, stage seed, raw rank transcripts, all relation
  proposals/coexistence classes, and rational/source replay proof digests.
- [ ] Every required slope model rigorously minimizes its simultaneous signed
  lower bound over the full integer product `S_i in [A_i,A_i+U_i]`.
- [ ] A pinned Magma version runs known-rank, planted-dependence, malformed,
  timeout, and PARI-agreement controls, then retains exact scripts, output,
  return codes, and resource use.
- [ ] For every admitted `r=7..9` row, an exact cubic-to-Jacobian construction
  maps the chosen origin and every selected point, checks good reduction, and
  replays each relation in both representations.
- [ ] A separately committed allocation reaches the protocol's discovery and
  replication exposure, or a fixed-inclusion-probability two-phase design has
  enough effective sample size for the same frozen alternative.

The first two conditions complete the classification machinery. The third is
needed for the requested finite-range exponent decision; a small sentinel can
only detect a gross departure and must remain labeled underpowered.

## Next discriminating step

- **Action or proof obligation:** first close and freeze the executor,
  anti-circularity, provenance, inventory, and mixed-allocation gaps. After
  licensed Magma and checkpoint transport are restored, run the excluded
  controls and two-row 16/18-bit cost calibration; do not launch a discovery
  panel from calibration outcomes.
- **Inputs and controls:** known-rank curves, planted and independent selected
  points, mutated certificates, PARI/Magma agreement, fixed timeouts, and all
  three unresolved-case allocations.
- **Execution limits and stop condition:** the frozen PARI 60/300-second and
  Magma 300/1,800-second tiers; stop and retain the row on any semantic conflict
  rather than coercing a rank.
- **Outcomes and next actions:** passing controls gives a cost/unresolved-rate
  estimate for the separately frozen allocation; disagreement returns to the
  adapter; a cubic mapping failure keeps `r=7..9` blocked; insufficient exposure
  leaves the exponent unresolved rather than negative.
- **Recheck trigger:** an executor/evidence/inference acceptance item lands, a
  Magma license/runtime or valid checkpoint transport appears, a completed
  point-map certificate lands, or an approved compute allocation becomes
  available.

A planned or underpowered panel is not a completed decay experiment.

## Resolution and history

2026-11-18: opened after the prospective protocol, scalable source layer, and
rank-adapter controls separated the three blockers. Unresolved.

2026-11-19: expanded after the executor and analyzer audits identified four
additional independent production gates: no natural executor, no enforceable
redacted public/evaluator process boundary, no complete row/relation-inventory
provenance validator, and no rigorous mixed per-prime censoring optimizer.
Producer controls do not close these gates. Unresolved. [pcc:unverified]

2026-11-19: user explicitly authorized execution. A pushed-head checkpoint
retry still failed for absent upload transport, and an adversarial M3 canary
showed that innocuous-key feature smuggling passes the current interface.
Authorization did not launch or validate a natural row. Unresolved.
[pcc:unverified]

2026-11-19: added non-production public-boundary, resumable-executor,
row-provenance, and mixed-censoring scaffolds with adversarial mutation tests.
The new code narrows locally implementable gaps but remains outside the freeze;
checkpoint transport, Magma, signed verification, runner wiring, complete
relation lattices, cluster inference, the cubic map, and powered exposure stay
open. Unresolved. [pcc:unverified]
