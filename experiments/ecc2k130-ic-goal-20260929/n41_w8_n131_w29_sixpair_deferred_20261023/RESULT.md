# Six-pair source-gate deferral on the N41 public point

The balanced six-pair XCNF encoding satisfies every clause and native XOR row on the independently audited N41 public relation. Deferring source validity from three slots to all six reduces the formula by 861 AND gates, 2,712 clauses, 405 XOR rows, and 1,389 variables. Neither one-worker public-point search returned a solver model within its frozen wall cap. The gates removed here therefore did not yield a usable public-point relation at these caps.

| Control | Exact source slots | Variables | AND gates | Clauses | XOR rows | Parent cap | Observed wall | Sampled combined peak RSS | Status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Three exact | 0, 1, 2 | 21,246 | 17,712 | 55,652 | 2,959 | 180 s | 180.013 s | 592,887,808 B | `BOUNDED_UNKNOWN` |
| All deferred | none | 19,857 | 16,851 | 52,940 | 2,554 | 120 s | 120.013 s | 430,161,920 B | `BOUNDED_UNKNOWN` |

The point is `(344545435656, 924092594889)` on `EC1N41Ckb1h7d5e80d3c4d0`. Each query used one CryptoMiniSat worker with a 4 GiB combined-RSS cap. The 180-second and 120-second caps differ, so the table establishes formula-size and bounded-status facts, rather than a runtime ordering. `candidate_id` remains null: the two encodings are point-decomposition diagnostics, not complete IC pipelines.

## Construction and correctness

The source variable is a seven-bit fixed-seed product code. The quadratic `C z² + p z + H = 0` constrains each source pair reciprocal. Five reciprocal `S3` links form a balanced tree and constrain its root to the public target reciprocal. The three-exact variant also applies the source trace and inverse checks in slots 0–2. The fully deferred variant applies none. Both retain six distinct raw codes and nonzero pair and intermediate reciprocals.

An independent source census accepts 40 of 128 raw codes and matches the prior geometric point set. The constructed relation uses six distinct codes `[121,100,93,2,108,28]`; independent group addition replays all six rotated source pairs to the public point. Binding those codes and intermediate reciprocals, then completing the circuit assignment, satisfies all 55,652 clauses and 2,959 XOR rows in the first formula and all 52,940 clauses and 2,554 XOR rows in the second. This is a positive correctness control. The unpinned solver searches are recorded separately in the query results.

The next design step is an early exact constraint on two or more partial sums that prunes whole code families before the five `S3` links become a large search. The source-validity-gate reduction alone did not provide that pruning. Keep the N131 transfer behind an unpinned, independently verified N41 relation from this encoding; the N131 W29 source space has a much larger code count and a formula-size reduction here does not establish search scaling.

## Reproduction and proof map

The four `*_protocol.json` files freeze inputs, source and solver hashes, runtime receipt, point, worker count and caps before their corresponding runs. The `*_result.json`, `.xcnf`, `.stdout`, and `.stderr` files retain outputs and status. Check the archive with `python3 verify.py` from this directory. New local Sage jobs must use `/Volumes/SSD990/cryptanalysis/sage -python`; the saved `sage_runtime_info.json` was captured before the builds.

This run introduces no new abstract mathematical theorem. The reciprocal `S3` polynomial is defined in [`FourPreimage.lean`](../n41_fourpreimage_s3_join_20261016/FourPreimage.lean), where `FourPreimage.s3_quadratic` proves its quadratic form under characteristic two. [`InverseOutput.lean`](../n41_n131_w29_inverse_output_20261017/InverseOutput.lean) formalizes the fixed-seed reciprocal pair equation. [`SixPairSum.lean`](../n41_w8_sixpair_sat_20261016/SixPairSum.lean) proves that the balanced group-addition topology equals the ordinary sum under explicit group assumptions. These declarations support the algebraic construction; they do not turn a solver model into a curve relation without a source-point and group-law audit. The new claims here are exact circuit-assignment checks and measured, bounded solver outcomes, with full scripts and receipts retained.
