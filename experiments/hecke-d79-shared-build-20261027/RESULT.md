# One degree-13 function build serves both D79 prefix cases

A single checked `H.build([13])` result produced the same verified fibers, source cancellations and rational/Fq rank paths at p8597 and p12197 as two independent builds. The six build invocations across four alternating-order runs all serialized to SHA-256 `ebc29c5c9b4f3de35bc45afa4ac9f3b40db2f1a68c5a9912396a0ab67dca24ea`. The shared implementation executes one field-independent function build for the two-prime workload while the separate control executes two.

| Run | Mode | Prime order | Build calls | Build wall | Two-prime measured wall | Peak RSS |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| shared-a | shared | 8597, 12197 | 1 | 32.07 s | 33.56 s | 1.47 GB |
| separate-b | separate | 12197, 8597 | 2 | 71.44 s | 72.89 s | 2.05 GB |
| separate-a | separate | 8597, 12197 | 2 | 71.31 s | 72.74 s | 2.00 GB |
| shared-b | shared | 12197, 8597 | 1 | 34.05 s | 35.46 s | 1.88 GB |

The observed two-run medians are 34.51 s shared and 72.81 s separate. Their 38.30 s difference is an exploratory reusable-setup measurement on a shared host, with no Tier 0/1 isolation record. The construction is performed before any per-prime source-prefix search; it is preparation work, not a single-target online interval. The per-prime rows, source counts (12 and 15), signed trial counts (4,984 and 12,965), and terminal ranks (39 over Fq, 40 over Q) match the hash-pinned [prefix experiment](../hecke-d79-source-prefix-20261027/RESULT.md) in all four runs. `candidate_id` and `target_online_ms` remain null.

The runner imports the frozen source and prefix lifting implementation by SHA-256, constructs degree-13 functions once or twice according to the frozen mode, and reruns every visited fiber, outside-trace cancellation, group equation and rank decision. It records each build's content digest, per-prime setup/fiber/search/rank phase, total wall, peak RSS and exact stdout/stderr. [verify.py](verify.py) checks all four run receipts, the six build digests, every prefix's operation counts and ranks, and the cross-linked source identities; [summary.json](summary.json) preserves the measured comparison. All four capped checked-Sage commands exited successfully.

The algebraic rank conclusions are the same exact matrices covered by the checked Lean modules in the prefix experiment. This experiment adds an implementation result: reusing the field-independent function object across primes preserves those matrices. The next engineering step is a versioned, content-addressed serialization of the rational function output so separate processes can load the same checked artifact without repeating `H.build([13])`; that step needs its own frozen load/validation and timing protocol.
