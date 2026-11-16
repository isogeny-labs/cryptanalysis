# Production binary subtraction: speed-frontier protocol

Status: prospective timing freeze; native correctness controls already ran and are development evidence. No frontier timing data have been collected. Publish this protocol and exact source before generating held-out performance fixtures or launching any build/run.

## Original objective and acceptance

Continue orientation/y-x relation work, establish a faster baseline, deliver paired PRs in isogeny-labs/crypto and isogeny-labs/cryptanalysis, and reach the applicable speed frontier. The prior tiny-field complete-relation checker is a correctness control, not the production or external frontier comparator. A ready PR or passing unit tests do not complete the speed objective. [pcc:unverified]

The production API returns one witness. Preserve the scalar oracle's first witness exactly for scalar/full-batch/lazy variants, including no-hit decisions. Table references may return a different valid witness: require the same decision and independently check every full-point equation. Never compare first-hit latency to complete-relation enumeration as though they were identical workloads.

## Named comparisons

1. Inherited generic SubtractOracle: production scalar arithmetic and existing base indexes.
2. subtract-binary-batch with lazy=0: full native batched additions.
3. subtract-binary-batch with lazy=1, block in {8,32,128}: native CLMUL/available SIMD, deferred ordinates, identical witness order.
4. Existing negation-folded pair-table oracle, including cold construction. Also include crypto's current signed-Frobenius layout/counting path when the factor-base recipe admits it; its different recipe must be labelled, not called a matched-base comparison.
5. OpenSSL EC2M as an external arithmetic/control reference. EC_POINT_invert's observed Y=0 exception makes the raw API invalid on the full supported point domain; retain that negative control. The matched reference applies affine negation through BN_GF2m_add and uses OpenSSL EC_POINT_add. The current C++ helper is correctness-only; an admitted timed wrapper still has to be bound before measuring the external frontier.
6. Matching scalar A/A and strongest applicable signed-Frobenius rho for pipeline accounting. No claim of global fastest status without a current external implementation survey and matched runs.

## Workload and boundaries

Initial end-to-end EKS panel: K0/GF(2^13) and K1/GF(2^17), the same dimension-5 standard subspace in every matched-base arm, eight public targets per curve, target seed 202611153001, five measured alternating rounds after one warmup, measurement seed 202611153002. Proposed native spec: frontier-panel.json in crypto. First-witness-preserving variants must reproduce the same target stream, relation decisions and recovered scalars; disclose any failure rather than filter it.

A separate component continuation extends to K0/GF(2^31), dimensions 4,6,8, and uniform versus planted positive targets as separate strata. Preserve identity, x=0, equal/inverse operands, absent relations and duplicate-label correctness controls. Export actual field polynomials, coefficients, base points and targets so cross-repo/external comparisons use identical bytes. Do not claim a cryptographic-size or higher-arity result from these rungs.

Primary one-target cost is cold: include base/index creation, prepared negatives, kernel scratch growth, all failed searches, every computed batch lane (including lanes past the first hit), matrix/recovery work and verification. Setup-reuse and component query-only intervals are secondary and explicitly separate. Keep resident memory, hash lookups, ordinate completions, field work and group-call counts visible; a group-add count is not a wall-time cost. Do not count inversion internals twice.

## Execution and decision

Use the existing EKS L2 route with exact source/image/executable hashes, current pool/quota readback and current daily/monthly remaining-budget plus reservation accounting. Proposed campaign ceiling USD 5, one job at a time, 4 CPU/4 GiB, original 900-second job deadline, zero retries; include build/failures and stop if remaining budget is unknown. These bounds do not authorize changing providers, quotas or the protocol to avoid admission. Cryptanalysis also requires its checkpoint gate before an experiment.

Retain every raw sample, A/A outcome, isolation gate, timeout, provenance and independent replay. Report ratios with intervals on identical workloads; require A/A to admit the run. A candidate becomes a measured improvement only if it wins against the named incumbent on held-out inputs without invalid answers or a hidden cost increase. If a table or external implementation wins, keep it as the incumbent and use the profile to select the next optimization. If admission fails, preserve the failure and keep frontier status open. No leaderboard promotion without the repository validation gate. [pcc:unverified]
