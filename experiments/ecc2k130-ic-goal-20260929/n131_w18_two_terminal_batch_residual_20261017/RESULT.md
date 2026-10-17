# Batched terminal residuals add 108.83 seconds of same-formula N131 search

**Two batch inversions reproduce all 2,080 N131 public terminal residuals and all 2,080 constructed-control residuals exactly, replacing 4,160 individual inversions per panel.** On matched public inputs and the same host, residual generation fell from **20.318 s to 0.551 s**. A fresh bounded query then regenerated the **identical** 17,545,002-byte public XCNF and spent **596.019 s** in solver search, compared with 487.189 s in the prior frozen attempt. Its full target-dependent interval was 598.036 s under the one-worker, 600-second, 4-GiB envelope. The solver ended `BOUNDED_UNKNOWN` at the parent cap; the exact outcome, transcript, phase costs, and source identity are retained.

The curve is `EC1N131Ckb1heb5f1998f20b` over `GF(2)[t]/(t^131+t^13+t^2+t+1)`, with public workload `cc09e7eb202a`. Seven W18 fixed-seed free pair slots and the same two 48-state terminal pools yield 2,080 admissible joint terminal sums. The pre-existing [N41 ordinary-point control](../n41_w8_fixedseed_ordinary_join_20261013/RESULT.md) independently verifies a fixed-seed seven-pair relation and novel row on its archived public point. This iteration changes the N131 residual arithmetic and search allowance while keeping the public point, source, and emitted Boolean constraints fixed.

For each terminal sum `S`, the raw residual is `T−S`, followed by the standard reciprocal of its x-coordinate. [batch.py](batch.py) first gathers the nonzero denominators in the binary-curve addition formulas, inverts their product once, and recovers each denominator inverse in reverse prefix order. It repeats the procedure on the 2,080 resulting nonexceptional x-coordinates. The producer checks every recovered inverse by multiplication. The pinned [Lean theorem](BatchInverse.lean) checks the algebraic reverse-step invariant; [PROOF_MAP.md](PROOF_MAP.md) records its scope and the remaining concrete loop bridge.

| Frozen residual panel | Rows checked | Batch inversions | Batch wall | Matched scalar-inversion wall |
| --- | ---: | ---: | ---: | ---: |
| Public point | 2,080 | 2 | **0.551153 s** | **20.317993 s** |
| Constructed control | 2,080 | 2 | **0.481030 s** | archived scalar output checked exactly |

The [batch protocol](protocol.json) hashes the exact input pool, prior query/control rows, arithmetic source, and both routes before measurement. [run.py](run.py) compared every ordered public batch row with a fresh scalar-inversion row and compared both batch panels with the frozen rows. [verify.py](verify.py) repeated the batch calculation, checked an eight-value inversion control, and bound the earlier independent checked-Sage audit of **all 4,160** control/public residual rows. The [verification receipt](verification.json) passed. These local wall intervals are algorithmic stage diagnostics, not isolated hardware speedups.

## Frozen same-point query

The self-contained [version-two query package](query_v2/protocol.json) pins the accepted [Sage runtime receipt](query_v2/sage_runtime_info.json), source hashes, batch verifier, original public input, one worker, 600-second parent wall cap, 4-GiB sampled RSS cap, and a 590-second CryptoMiniSat time flag. Its [preflight](query_v2/preflight_result.json) reproduced every public residual and the original XCNF SHA-256 `98f570f8afbe5826ae541548c24b2308da77f9a2650e54f0ae4a5d459f179f34`. The [terminal audit](query_v2/audit_result.json) checks the same byte hash in the query formula, every residual, transcript hashes, phases, caps, target, and workload.

| Exclusive target-dependent phase | Prior scalar route | Batch route |
| --- | ---: | ---: |
| Generate terminal residuals | 104.504426 s | **0.337394 s** |
| Construct formula | 6.241123 s | 1.665280 s |
| Serialize formula | 0.101666 s | 0.013722 s |
| Solver launch/search/stop | 487.189143 s | **596.018850 s** |
| Parse terminal output | 0.012122 s | 0.000766 s |
| **Target-dependent phase sum** | **598.048480 s** | **598.036013 s** |

The matched 20.318-to-0.551-second arithmetic comparison isolates the algorithmic change on the current host. The prior and new 600-second query phases were recorded on a shared host at different times, so the phase table describes the two actual attempts rather than an isolated wall-time speedup. The new [query receipt](query_v2/query_result.json) records `BOUNDED_UNKNOWN`, `TARGET_DEPENDENT_TIMEOUT`, 2,553 restart rows, and 716,963,840 bytes sampled peak combined RSS. The raw solver stdout and stderr remain in the same directory. All 394,248 variables, 171,508 AND gates, 518,734 clauses, and 220,947 native XOR rows match the prior XCNF exactly.

The [version-one preflight receipts](query_v1/) retain two setup failures: system Python lacked `psutil`, then the checked Sage interpreter correctly found a missing copied source file during hash validation. Version two copies that file during its freeze step and passed preflight before the bounded query. The selected terminal source has a [0.554579433463 labeled-tuple mean upper ceiling](../n131_w18_two_terminal_coverage_20261015/RESULT.md) for one uniformly chosen raw point. The complete 598.036-second attempt is a censored search result; it does not resolve source coverage or relation yield for this fixed point. The next solver experiment must change the target-conditioned search constraints or source support while preserving the same public-point, N41-control, and full-cost gates. `candidate_id` remains `null` until a complete IC pipeline is specified.
