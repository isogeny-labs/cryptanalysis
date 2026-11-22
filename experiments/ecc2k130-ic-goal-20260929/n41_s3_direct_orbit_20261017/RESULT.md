# Compact direct leaves with a free N41 public-target orbit selector

**The compact bilinear-leaf circuit represents all 41 Frobenius conjugates of one public raw point with 18,491 AND gates, and all 41 archived ordinary relation assignments satisfy its exact XCNF.** The unpinned one-worker query reached its 600-second parent cap with status `BOUNDED_UNKNOWN` and no SAT or UNSAT terminal line. This isolates target-orbit multiplicity from source-leaf size: the selector adds 1,640 AND gates to the 16,851-gate direct-leaf circuit, yet the resulting solver run does not clear the ordinary N41 relation gate.

## Construction and input

The fixed N41 source is `EC1N41Ckb1h7d5e80d3c4d0`, with field `GF(2)[t]/(t^41+t³+1)`, curve `y²+xy=x³+1`, fixed seed code 56, six source rotations `(0,6,12,18,24,30)`, and 40 legal pair codes per slot. The raw public point is `U=(2026560328086,1928332930914)`; the same subgroup point is obtained from every `Frob^j(U)` after inverse transport and cofactor-four projection. The [frozen protocol](protocol.json) binds this source, the 41-position [native orbit join](../n41_sixpair_target_orbit_20261016/RESULT.md), the direct-bilinear-leaf code, the repository Sage runtime, and the target input law.

The circuit leaves all six code masks and reciprocal pair outputs free. A one-hot selector chooses `Frob^j(1/x(U))` for `j=0,…,40` as the final S3 target coordinate. Frobenius acts by squaring on reciprocal coordinates, so this is the reciprocal of the selected conjugate's `x` coordinate. The [formula readback](formula_audit_result.json) rebuilt the public XCNF byte for byte, verified all 820 pair exclusions, found 41 distinct target coordinates, and found no unit clause on the 42 source-code or 41 target-selector variables. The [builder](build_result.json) checked every CNF clause and native XOR row on each of the 41 source-state tuples from the archived orbit join. Its independently checked-Sage [group audit](../n41_sixpair_target_orbit_20261016/join_audit.json) records 41 valid relations and rank 41 for those rows.

| Same N41 source and public subgroup point | Direct leaves, one raw target | Earlier orbit circuit | Direct leaves, 41-target orbit |
| --- | ---: | ---: | ---: |
| AND gates | 16,851 | 28,577 | **18,491** |
| Variables | 20,283 | 33,351 | **22,101** |
| Ordinary clauses | 52,243 | 88,698 | **57,984** |
| Native XOR rows | 2,975 | 3,826 | **3,112** |
| Checked orbit relation assignments | 1 | 41 | **41** |
| Unpinned solver status | `BOUNDED_UNKNOWN` | `BOUNDED_UNKNOWN` | **`BOUNDED_UNKNOWN`** |
| Parent cap / observed query wall | 550 s / 550.025 s | 185 s / 185.111 s | **600 s / 600.030 s** |
| Sampled peak combined RSS | 522,272,768 B | 337,379,328 B | **390,070,272 B** |

The new [query protocol](query_protocol_v2.json) pins the same CryptoMiniSat binary, one worker, `--maxtime=590`, a 600-second parent cap and a 4-GiB RSS boundary. The parent stopped the worker at the cap with exit `−15`; [raw stdout](solver_v2.stdout) has no terminal solver result, and [raw stderr](solver_v2.stderr) is empty. These are ordinary-host stage diagnostics with different prior caps, so the three bounded rows do not support a solver-speed ordering. The [terminal readback](verification.json) checks hashes, every archived control ID, the formula, Lean output, resource envelope and censored status. This remains a design proposal with `candidate_id: null`.

## Proof map and failure ledger

The byte-identical [Lean theorem](OrbitTransport.lean) from the earlier orbit study proves conditional pullback of a relation through inverse additive Frobenius when the base is closed and `cofactor(U)=Q`. Lean 4.34.1 checked `SixPairTargetOrbit.relation_pullback`; `#print axioms` lists only `propext, Quot.sound`. The concrete curve/base bridge is supported by the archived independent Sage orbit, closure and group audits. The direct leaf inherits the prior 960-state source audit; the [proof map](PROOF_MAP.md) keeps the curve-to-circuit formal bridge explicit. `lean4checker --fresh` was unavailable locally.

The first freeze attempt expected a different passing status string from the archived orbit audit. Its [failure receipt](freeze_v1_failure.json), exact source, stdout and stderr remain frozen; the corrected source uses the observed `PASS_N41_FROBENIUS_TARGET_ORBIT` status. A conditional [Sage model-replay program](replay_sat_sage.py) is retained for any later SAT run; it was not invoked on this bounded query.

## Next experiment

The direct-leaf reduction and 41-way orbit selector increase the number of verified assignments while keeping the formula smaller than the earlier orbit circuit. Their unpinned search still reaches the cap. The next method must derive a **nonlinear, target-dependent exclusion on still-free source-code families** before the S3 internal variables are expanded. A concrete gate is to factor the seven-point Riemann–Roch determinant into its 35 three-row minor products, keep each fixed-seed pair family's quadratic source law symbolic, and test whether the resulting block predicate rejects N41 code-prefix regions without enumerating signed states. Freeze an unpinned public N41 query and compare complete target-dependent work against the same-point native join; carry a successful source-bound rule to the frozen N131 one-worker, 600-second, 4-GiB relation gate. Rank, factor logs, an unseen target descent, and the matched isolated rho interval remain parts of the active goal.
