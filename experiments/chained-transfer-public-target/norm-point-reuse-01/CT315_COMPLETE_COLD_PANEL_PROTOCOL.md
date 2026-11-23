# CT315 — complete cold single-target ECDLP cost-panel admission (preregistered)

Date: 2026-11-22. Existing draft cryptanalysis PR #1912. [pcc:unverified]

## Why this experiment is needed

CT311 calculates 48 direction/sector **primitive-only** deltas from fully captured 695-record native traces. Even a genuine positive delta cannot demonstrate cheaper **complete** prime-field ECDLP: source-target map, model setup, precomputation, relation generation, sparse linear algebra, individual descent, recovery, verification, teardown, memory and strongest comparator are all outside CT311. CT310's `peak_rss_kib` is currently null. An outcome that lacks these costs must not pass.

## Prospective admission contract

1. This new offline checker accepts a future, separately sourced, *actual* ABBA cold panel; it neither produces solver measurements nor authenticates execution. For each preregistered block (minimum four blocks), run retained-lift / candidate / candidate / retained-lift in that order on the **same public (P,Q), source curve, host, CPU affinity and protocol**, and once each matched optimized negation/Frobenius-aware rho, BSGS, and best existing index-calculus baseline. Every arm is an independently cold process; record exact source and executable SHA, stdout and capture-receipt SHA, trial ID, matched recovered log, external elapsed time, and measured peak resident memory. No selective omission, over-limit exclusions, or changing the best comparator after seeing the result.
2. All seven methods' runs within a block must have every phase: `setup,transfer,precomputation,relation_collection,linear_algebra,individual_descent,recovery,verification,teardown`; allow explicit zero for truly absent phases, **not** omitted keys. Nonoverlapping phase timers sum no greater than complete external wall time; external wall is the *charged* time, never an unjustified sum of overlapping timers. Require positive measured RSS for **every** run, including rho, BSGS and IC. CT310's current `None` is a hard incomplete-memory outcome, not silently promoted.
3. Compare the mean of the two candidate cold walls with the minimum of retained-lift mean, optimized rho, BSGS and IC wall for **each matched block**. Preserve the paired ratio of aggregate best-baseline wall to aggregate candidate wall and all per-block signs. Do not prefer the slower of two baselines or exclude losses. All phases and teardown remain charged. Only call a candidate computationally cheaper if an **independently reproduced** complete-solve ratio >1 with the registered uncertainty and PCC/CI/validation gates. This checker only computes a **producer-provisional** arithmetic ratio and always says `pcc:unverified`; it never declares a speedup.
4. Require four or more complete blocks, exact seven-run schedule, one exact host per block (plus the experiment's same host across blocks), identical public target and expected verified scalar for each run, and distinct run IDs. Require nonempty binding hashes. A producer assertion `verified=true` is not independent scalar verification; retain a separate independent source group law oracle and signed PCC before scientific admission.
5. Reject mutations: missing phase, zero/missing RSS, missing/extra baseline, altered ABBA sequence, changed target or scalar, contradictory non-overlapping phase/external wall, host mismatch, repeated run ID, malformed SHA. Use synthetic timing-only *positive and negative* controls, no original EKS model, AWS token or paid compute.

## Reproduction and standing

```sh
python3 experiments/chained-transfer-public-target/norm-point-reuse-01/ct315_complete_cold_panel.py --self-test
python3 -O experiments/chained-transfer-public-target/norm-point-reuse-01/ct315_complete_cold_panel.py --self-test
# Actual data only after custody/compute approval:
python3 experiments/chained-transfer-public-target/norm-point-reuse-01/ct315_complete_cold_panel.py --panel /path/to/original-cold-panel.json
```

This is a prerequisite *cost completeness* gate, not a provider or scientific execution proof, not a new mathematical attack, and not a performance result. The original six-S3-object STS/tool approval, independent native original/reuse full parity, measured C169/C13a/C13b/D/N2_actual, real cold solver binaries, A/A drift, uncertainty intervals, RSS and signed PCC remain open. No model, original fixture, Rust evaluator, shared ledger, credential, EKS/Spot budget or protected merge policy is changed. [pcc:unverified]
