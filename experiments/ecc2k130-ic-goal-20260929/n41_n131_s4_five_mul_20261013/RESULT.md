# Shared-product S4 target circuit

For a fixed target reciprocal `t`, sharing the product `abc` reduces the direct reciprocal S4 arithmetic core by one full field multiplication. The N41 source-constrained public formula falls from **8,049 to 7,107 AND gates** while retaining the same 125-mask W8 source and eliminating the same 41-bit intermediate. The refactored formula preserves a checked three-pair group control, then reaches `BOUNDED_UNKNOWN` at the frozen 120-second unpinned public query cap.

## Identity and exact circuit effect

Let `a,b,c` be reciprocal-x coordinates of three pair sums, and put `p=ab`, `u=pc`, `v=c(a+b)`. With the target `t` fixed,

```
e1 = a+b+c+t
e3 = u+t(v+p) = abc+abt+act+bct
e4 = tu = abct.
```

Use the established six-term S4 equation with `X=e1²`, `Y=e3²`, `Z=e4`:

```
S4 = Y² + X² + Y + Z(X+Y+XZ).
```

The circuit computes `p,u,v` in three full variable-variable products and the final `XZ`, `Z(X+Y+XZ)` in two more. Multiplication by the frozen target is a linear map over `GF(2)`, so it adds no Boolean AND gates. [FiveMulIdentity.lean](FiveMulIdentity.lean) checks the coefficient identity. Independent checked Sage confirms equality to the prior 24-monomial resultant in `GF(2)[a,b,c,t]` and evaluates all four signed-sum roots from each frozen N41 and N131 group control. The [proof map](PROOF_MAP.md) records the formal field bridge precisely.

| Arithmetic core with fixed target | N41 AND gates | N41 variables | N131 AND gates | N131 variables | Free intermediate bits |
| --- | ---: | ---: | ---: | ---: | ---: |
| Two adjacent S3 links | 2,826 | 5,429 | 17,451 | 33,542 | 41 / 131 |
| Prior direct S4 | 5,652 | 9,799 | 34,902 | 61,519 | 0 |
| Shared-product S4 | **4,710** | **8,816** | **29,085** | **55,477** | 0 |

The [core receipt](core_result.json) fixes the same constructed target in each field and hashes the prior circuit and group audit. These are circuit measurements, not solver outcomes.

## Paired N41 source gate

The [formula protocol](formula_protocol.json) reuses the frozen previous builder, exact 125 usable W8 masks, six distinct masks, folded-column collision shield, zero Frobenius rotations, and public point `(920359962848, 755404565011)`. Only the S4 arithmetic function changes. The source prefix remains 2,397 AND gates in both direct S4 formulas.

| Formula on same public point | Total AND gates | Variables | Clauses | XOR rows | Bytes | Query status |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Prior S4 | 8,049 | 13,580 | 24,695 | 5,360 | 548,451 | `BOUNDED_UNKNOWN` at 120 s |
| Shared-product S4 | **7,107** | **12,568** | **21,869** | **5,290** | **495,551** | `BOUNDED_UNKNOWN` at 120 s |

The one-worker CryptoMiniSat 5.14.7 [run protocol](run_protocol.json) fixes the solver binary, flags, source/formula hashes, 4 GiB sampled parent-plus-solver RSS cap, a 30-second control cap, and a 120-second public cap. The constructed three-pair control uses the independently checked N41 group sum from the prior experiment; it returned SAT in 0.168 seconds, and an independent complete-model check verified all **22,040 clauses and 5,321 XOR rows**. The ordinary public query was stopped by its 120.050-second parent wall cap with no terminal SAT or UNSAT line; sampled peak parent-plus-solver RSS was **208,437,248 bytes**. The raw logs and statuses are bound by [run_result.json](run_result.json).

These wall times are exploratory on a shared host without an isolation receipt. The public row's 27.58 child user seconds during 120.05 wall seconds also shows substantial contention. Since both public rows are censored, the smaller circuit does not establish a solved-query speedup. `candidate_id` remains `null`; complete relation collection, matrix rank, target descent, and paired rho stages are outside this component gate.

## Decision and replay

The one-product saving is retained as a reusable arithmetic improvement. The frozen N41 public gate did not justify an N131 ordinary-query promotion. A next target-conditioned filter should act on source-mask or pair-output families before all S4 multiplications are instantiated; the two capped N41 formulas provide the exact source-law comparator. A proposed filter must preserve the constructed group control, reject ordinary families measurably, and then recover and independently replay an unpinned public relation before spending the N131 600-second/4-GiB gate.

Replay the read-only bindings with `python3 -B experiments/ecc2k130-ic-goal-20260929/n41_n131_s4_five_mul_20261013/verify.py`. The checked Sage job used `/Volumes/SSD990/cryptanalysis/sage -python` after saving its runtime receipt. All phase costs and raw capped statuses remain in the referenced machine-readable receipts.
