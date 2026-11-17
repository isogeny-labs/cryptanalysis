# CT186 prospective first-four-slot same-route sham control

2026-11-17 · [pcc:unverified] · tracking PR #1718 · source-only control, not a benchmark.

## Prior evidence and question

Merged CT185 #1715 constructed a sequence-locked 1.5x null under the actual CT182 balanced scorer: two native routes had identical synthetic intrinsic cost and trailing A/A control was zero. This shows fixed ABBA/BAAB plus A/A alone does not establish a causal transfer speedup. Relevant designs: Kalibera–Jones, *Rigorous Benchmarking in Reasonable Time* (ISMM 2013, DOI 10.1145/2491894.2464160) and CT181–185 repo source. Shared research-KB MCP and native toolchain are unavailable in this runtime.

Can a frozen first-four-slot placebo estimator detect *assignment-correlated* timing bias when all four processes execute the **same** public route? This will be tested on deterministic synthetic data before any native sampler or EKS request.

## Prospective source-only contract

- Separate new schema `ct186-first-four-same-route-sham/v1`. Never change/relabel CT182/183 v2 or original 48-vector Git blob `9ac741668dd1ffa9632ff0d58e6f4dd9f2dd18c3`.
- 48 packet indices × 8 blocks × 4 positions = **1536** planned *additional* fresh-process observations; actual physical arm is **direct_composite on every position**. The logical labels A/B are **diagnostic placebo assignments only**, not arguments passed to the native executable. This tool contains **no native process runner**.
- Every packet receives four ABBA and four BAAB blocks; select four ABBA blocks via a private-independent-from-CT183, reproducible seed `20261118 + packet` and block-order shuffle (use Python `random.Random`, record seed and SHA256 of exact ordered roster). The schedule is not the CT183 deterministic parity sequence.
- Source-only samples are exact dictionaries with `block`, `packet_index`, `position`, `label`, `physical_arm`, `wall_ns` (strict positive Python int); adjudication refuses missing/duplicate/extra/misordered records, bool-valued durations, wrong arm/label, missing blocks and incompatible schemas.
- For each packet-block: log(sum(wall[A-labelled]) / sum(wall[B-labelled])); packet-level estimand is median across eight blocks; evaluate **48 packet-level logs**, rather than treating 1536 processes as independent. Report per-packet diagnostics and global descriptive median only: **no CI or ECDLP superiority inference** until independent original 16-stratum packet labels and authentic execution/custody are joined.
- Synthetic controls: stationary-slot 3,2,2,3 gives packet median 0 on all 48; CT185-style assignment/order-locked 3,2,2,3 under ABBA and 2,3,3,2 under BAAB gives log(1.5) in each packet despite identical physical arm; harmless all-equal case gives 0. A genuine 5:4 **physical route** effect is not estimable from this all-A sham and must not be fabricated.
- Any nonzero sham effect is a reason to withhold attributing a native A/B effect to route differences pending further randomized/carryover controls. Zero sham is **not** proof of absent A↔B carryover: with all physical calls A, it cannot test arm-transition effects. Labels must be hidden from native child to prevent artificial treatment.
- To use on real cold processes later, implement separate admitted producer, exact executable/host/affinity/binary hashes, original 695/701 custody and native parity, bounded 1536-child aggregate deadline and output capture, and identical source/output verification for each physical A call. No execution permission is granted by this plan.

The scientific target remains a fully measured and independently verified cold single-target ECDLP advantage versus the strongest matched rho/BSGS/IC, counting setup, transfer, inversion, linear algebra, memory and uncertainty. No native benchmark, signed PCC, or paid compute in CT186 source work.
