# Target-backward linked N41 public-point circuit

**A target-backward terminal chain preserves and independently replays the known linked N41 relation, while its unpinned public search reaches the frozen 180-second cap.** The chain computes the first eight source points forward, then computes `T − P9 − P8` from the selected raw public-target preimage and the last two free source points. Equality to the eight-point subtotal couples the two terminal source states to the public target before a forward total is formed. The complete target-dependent public attempt was 182.523683417 seconds, including circuit construction, serialization, the capped solver interval, and transcript handling.

## Exact instance and method

The curve is `EC1N41Ckb1h7d5e80d3c4d0` over `GF(2)[t]/(t^41+t³+1)`, with equation `y²+xy=x³+1`, subgroup order `549756390943`, and cofactor four. The frozen public point is `(920359962848,755404565011)`. The source has ten signed W8 pair slots with 140 states each. Slots zero and one share one selector across Frobenius rotations, leaving nine free selectors and requiring nine distinct source edges. Four raw target preimages remain available in the unpinned query. The circuit uses seven forward affine additions and two target-backward additions. Every encoded addition requires distinct input x-coordinates, so this result concerns the intersection of those nonexceptional charts.

The [v4 protocol](v4/protocol.json) fixed the code and input hashes, one worker, a 30-second constructed-control cap, a 180-second public cap, and a 4-GiB combined RSS limit before execution. The known linked witness has source IDs `(24,24,129,109,93,123,59,37,50,79)` on raw target preimage 3. It satisfies both backward denominators. The control model passed all 315,326 CNF clauses and 52,406 native-XOR rows. Reconstructed source points, nine additions, the target, and every encoded slope/output agree. The earlier [independent checked-Sage relation audit](../n41_n131_linked_frobenius_pair_20261012/audit_result.json) supplies a separate group-arithmetic check of the same source points.

| v4 arm | Constructed control | Unpinned public query |
| --- | ---: | ---: |
| Solver status | `SAT` | `PARENT_TIME_CAP` |
| Variables | 121,336 | 121,336 |
| CNF clauses | 315,326 | 315,315 |
| Native-XOR rows | 52,406 | 52,406 |
| XCNF bytes | 6,885,587 | 6,885,516 |
| Solver interval, exploratory | 0.222865459 s | 180.028307042 s |
| Sampled peak combined RSS | 186,400,768 B | 327,450,624 B |
| Restarts | 1 | 453 |

The public solver stream has no SAT/UNSAT terminal line. The recorded process status is `PARENT_TIME_CAP`, and its mathematical outcome is `BOUNDED_UNKNOWN` at that cap. The [read-only verifier](verify.py) reconstructs both v4 formulas byte for byte, checks all source and solver hashes, replays the control model and group chain, and checks phase accounting. The [archive](archive_result.json) retains four attempted formulas as byte-replayable gzip files. The proposal has `candidate_id: null` because this is a point-decomposition component, with no complete N131 IC pipeline defined by this experiment. CPU intervals were measured on an unisolated host and are algorithmic diagnostics.

| Charged public phase | Nanoseconds |
| --- | ---: |
| Target-dependent circuit construction | 2,396,356,459 |
| Formula serialization | 97,596,208 |
| Solver, including capped attempt | 180,028,307,042 |
| Transcript handling | 1,423,708 |
| **Total** | **182,523,683,417** |

## Proof and chart scope

In any group, `T − P9 − P8 = U` if and only if `T = (U + P8) + P9`. [BackwardTarget.lean](BackwardTarget.lean) checks this structural equivalence from the group laws with pinned Lean 4.34.1; [lean_check.txt](lean_check.txt) reports no theorem axioms. The concrete binary-curve representation, nonzero denominators, source membership, and model interpretation are executable checks listed in [PROOF_MAP.md](PROOF_MAP.md). The backward chart can exclude forward relations whose backward denominator vanishes, so a complete decomposition method must handle those exceptional branches.

## Versioned producer evidence and next test

The initial runner stopped during construction because it resolved the nonzero helper through the wrong import layer. V2 built a formula but placed a constant-zero literal inside a nonzero clause; the solver rejected it at line 112222. V3 produced a valid formula and SAT control, but its model decoder raised `KeyError: 0` on a constant wire. V4 corrected that decoder without changing the v3 control formula; the archive hashes confirm byte identity. Each failed producer version has a separate frozen failure receipt, protocol, raw solver output where reached, and exact formula archive.

The backward terminal equation alone did not select an unpinned source witness at the declared cap. The next target-conditioned filter must reject **whole families with at least two unresolved partial sums** before enumerating their cross-product, while preserving the linked witness and handling exceptional chart branches. Its N41 promotion gate is an unpinned public relation with independent group and rank replay. Only then should a frozen N131 source-bound projection be charged against one worker, 600 seconds, and 4 GiB.
