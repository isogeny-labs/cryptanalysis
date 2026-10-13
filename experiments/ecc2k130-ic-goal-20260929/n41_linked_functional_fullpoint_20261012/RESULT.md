# Linked-source functional full-point N41 control

**The nine-free-state linked-source circuit closed its known positive N41 public-point control in 0.593348166 seconds, with every model row and all nine group additions replayed.** Its unpinned query on the same point searched until the frozen 180-second parent cap, recording `PARENT_TIME_CAP`, 205 restarts, and no terminal SAT/UNSAT line. This isolates source-state selection as the remaining obstacle in this formulation: the known linked relation satisfies the circuit, but an ordinary public search did not find it within the cap.

## Frozen instance and method

The field is `GF(2)[t]/(t^41+t³+1)`, the curve is `y²+xy=x³+1`, and the subgroup is `EC1N41Ckb1h7d5e80d3c4d0` of order `549756390943` and cofactor four. The public point is `[920359962848,755404565011]`, queried through all four raw preimages. Each signed W8 pair-state list has 140 states. Positions 0 and 1 share one selector across Frobenius rotations 0 and 7; the other eight positions have independent selectors. Their nine source edges must differ. Each of the nine nonexceptional full-point addition links functionally computes its slope and output. The [known relation](../n41_n131_linked_frobenius_pair_20261012/audit_result.json), independently replayed earlier through checked Sage, provides the positive witness on raw preimage 3 with state IDs `(24,24,129,109,93,123,59,37,50,79)`.

The [v3 protocol](v3/protocol.json) froze source, solver, public input, one-worker policy, 30-second control cap, 180-second public cap, and 4-GiB combined RSS before the final run. The [full evidence verifier](verify.py) checks frozen hashes, formula profiles, model and group receipts, raw solver logs, and byte replay from all five compressed XCNFs.

| Final v3 arm | Positive control | Unpinned public query |
| --- | ---: | ---: |
| Variables | 121,257 | 121,257 |
| CNF clauses | 315,326 | 315,315 |
| Native XOR rows | 52,327 | 52,327 |
| XCNF bytes | 6,883,688 | 6,883,616 |
| Solver status | `SAT` | `PARENT_TIME_CAP` |
| Solver wall, exploratory | 0.593348166 s | 180.053678875 s |
| Peak sampled combined RSS | 140,623,872 B | 199,229,440 B |
| Replay | all 315,326 CNF and 52,327 XOR rows; nine group links; nine distinct edges | 205 restarts, no terminal line |

## Versioned producer evidence

The first [protocol](protocol.json) and outputs are preserved. A known-zero field bit was emitted as literal `0` inside a nonzero CNF clause, so CryptoMiniSat rejected both formulas with exit 255 before search. The [failure audit](failure_audit_result.json) classifies both as `PRODUCER_FAILURE_XCNF_ZERO_LITERAL`, not bounded mathematical outcomes.

In v2, the clause was encoded correctly and the pinned solver returned SAT, but the producer's model decoder tried to index constant wire `0` and stopped before writing its control receipt. A separately frozen [recovery](v2/recover_result.json) checked every CNF and XOR row from the saved model and reconstructed the known relation. V3 corrected the decoder without changing the mathematical source and ran both arms to terminal status. The [archive](archive_result.json) retains byte-identical compressed formulas for every attempted arm; restore a raw `.xcnf` from its `.gz` file when rerunning a historical source that requires the raw path.

The linked restriction reduced the public formula by 10,387 clauses relative to the prior ten-free-state functional-slope N41 circuit, while retaining a complete positive witness. Both unpinned circuits reached their 180-second caps. These shared-host wall measurements are exploratory; this test establishes a correctness and search-status boundary, not a controlled CPU speedup.

## Next experiment

The next candidate must derive a constraint from the public target that rejects **families of at least two unresolved partial sums before enumerating their source combinations**. On this N41 source, freeze a complete family partition, count the exact rejected and surviving families and all construction/query work, retain the known linked relation, and require an unpinned row with independent signed group and rank replay. Only a source-bound N131 projection that fits the one-worker 600-second/4-GiB envelope should advance to another frozen public query.
