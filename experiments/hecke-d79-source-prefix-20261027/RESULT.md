# Ascending degree-13 prefixes reach rational rank 40 after 12 and 15 sources

With the verified base-plus-direct support-four matrix fixed at rational rank 39, a fresh ascending-source degree-13 run first reached rational rank 40 after **12 lifted sources at p=8597** and **15 at p=12197**. The stopping rows use respectively one and four signed outside-trace cancellations. Each run independently rebuilt the degree-13 functions, lifted and checked only the visited fibers, and stopped on its own verified rank calculation. The existing full 40-source receipts informed the case choice and serve as consistency checks, so this is an adaptive-policy measurement on previously studied cases.

| p | First rank-40 prefix | Verified cancellations by stop | Signed search trials | Full 40-source trials | Rank over Fq / Q before → after |
| ---: | ---: | ---: | ---: | ---: | --- |
| 8597 | 12 of 40 | 1 | 4,984 | 772,240 | 39 / 39 → 39 / 40 |
| 12197 | 15 of 40 | 4 | 12,965 | 772,240 | 39 / 39 → 39 / 40 |

The p8597 rank-raising row uses source indices `[5,7,10,11]` with signs `[+1,-1,-1,-1]`. At p12197, three verified cancellations among the first 11 sources leave the rational rank at 39; the source-14 row `[0,8,11,14]` with all positive signs raises it to 40. The independently replayed prefix rank path stays below 40 at every earlier source count. The exact trial reductions from the full 40-source exhaustive signed census are 99.35% and 98.32%; these are search-pattern counts, not wall-time ratios.

## Cost and verification boundary

| p | Degree-13 function build | Visited fiber lifts | Signed search | Rank recomputation | Measured source-prefix total |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 8597 | 33,657 ms | 343 ms | 121 ms | 71 ms | 34,232 ms |
| 12197 | 31,874 ms | 508 ms | 269 ms | 68 ms | 32,751 ms |

The measured total also includes 40 ms and 32 ms of baseline row verification, respectively. It begins after Sage startup and input loading. The preexisting degree-2/5 base and direct relation construction are frozen preparation inputs whose costs are retained in the parent five-case receipts, not charged in this prefix total. All timings are single-run exploratory diagnostics on a shared host; a matched full-40 run under the same host envelope was not performed. The degree-13 function build accounts for most of the measured prefix work. `candidate_id` and `target_online_ms` remain null.

The producer hash-checks the source, parent class and analysis; verifies the 14 neighbor lifts, Hecke sum, modular polynomial, Frobenius orbit traces, and exact equality with each processed source entry in the prior full receipt; then checks every candidate as a class-point relation. The versioned pure-Python audit independently re-enumerates each prefix, recomputes every row and rank, verifies the first-hit condition, and matches the candidate set to the full receipt. Both corrected audits have `PASS` status. The first audit attempt failed only at a final comparison of dictionary serializations with different key order; its stderr is retained and [post_inputs.json](post_inputs.json) pins the corrected auditor and both producer results before replay.

The generated Lean modules check the prefix row kernel and invertible-minor certificates with `#print axioms`; [PROOF_MAP.md](PROOF_MAP.md) records the exact hypotheses and remaining structural/curve bridges. The next experiment should reuse the field-independent degree-13 function construction across the two primes, charging its one-time build separately from per-prime fiber lifts and searches, then test a deterministic source priority rule based on data available before lifting.
