# Overlapping S3 target paths on the N41 fixed-seed source

**A second, overlapping S3 summation tree introduces no exceptional reciprocal chart across the frozen N41 source-valid assignments and preserves the independently replayed public relation; the unpinned one-worker search reached its 600-second cap with status `BOUNDED_UNKNOWN`.** The new tree couples source pairs `(0,3)`, `(1,4)`, `(2,5)` to the same public target used by the original `(0,1)`, `(2,3)`, `(4,5)` tree. It adds 15,129 AND gates to the compact direct-bilinear-leaf circuit. The experiment tests whether redundant but differently grouped target equations improve SAT propagation; the observed cap supplies no verified search-time gain.

## Frozen method and exactness

The source is the fixed-seed W8 six-slot policy on `EC1N41Ckb1h7d5e80d3c4d0`, over `GF(2)[t]/(t^41+t³+1)` with `y²+xy=x³+1`. Each slot has 40 admissible source codes and four signed pair states per code; rotations are `(0,6,12,18,24,30)`. The raw public point is `Q=(2026560328086,1928332930914)`. The [protocol](protocol.json) binds the prior direct-leaf implementation, geometry, archived relation, checked-Sage runtime and both association trees. All six code masks and pair-output coordinates remain solver variables. A fresh [formula audit](formula_audit_result.json) rebuilt the XCNF byte for byte and found no unit clause on its 42 explicit source-code variables.

The first tree sums `((P₀+P₁)+(P₂+P₃))+(P₄+P₅)`. The second sums `((P₀+P₃)+(P₁+P₄))+(P₂+P₅)`. [`DualTree.same_sum`](DualTree.lean) proves their equality for any commutative group; Lean 4.34.1 checked it with only `propext` in `#print axioms`. The builder checked every clause and native XOR row on the archived state tuple `(12,122,116,47,128,34)`. An [independent checked-Sage audit](audit_result.json) reconstructed its source points and verified both five-link trees reach `Q` with twelve distinct folded columns.

Each internal reciprocal coordinate requires a nonidentity point with nonzero `x`. The [chart audit](chart_audit_result.json) exhaustively checked **24,864** valid signed-state combinations for each of the alternate tree's three first-level pairs and used an exact point-key join for its four-source node. It found zero identity or zero-`x` intermediates under the frozen N41 distinct-column rule. Thus this added tree does not remove a source-valid assignment through those exceptional charts on this source. The [proof map](PROOF_MAP.md) records the remaining curve-to-circuit formalization boundary.

| Frozen public N41 circuit | Single target tree | Two overlapping target trees |
| --- | ---: | ---: |
| AND gates | 16,851 | **31,980** |
| Variables | 20,283 | **37,288** |
| Ordinary clauses | 52,243 | **97,844** |
| Native XOR rows | 2,975 | **4,682** |
| Public query status | `BOUNDED_UNKNOWN` | `BOUNDED_UNKNOWN` |
| Parent query cap / observed wall | 550 s / 550.025 s | 600 s / **600.063 s** |
| Sampled peak combined RSS | 522,272,768 B | **524,828,672 B** |

Both queries use the same hashed CryptoMiniSat binary, one worker, the same public point and 4-GiB RSS boundary on the ordinary local host. The dual query used an internal 590-second limit and a 600-second parent cap; its parent stopped the solver with exit `−15` after no terminal result. The baseline used a different 550-second cap, so these censored rows do not rank solver speed. The dual [query protocol](query_protocol_v2.json), [raw stdout](solver_v2.stdout), [raw stderr](solver_v2.stderr), [monitor result](query_v2_result.json) and [terminal readback](verification.json) preserve the exact outcome. The experiment has `candidate_id: null`.

The first build reached the assignment checker but its wrapper expected a nonexistent `satisfied` key in the checker's successful count result; its [failure receipt](build_v1_failure.json), earlier protocol and raw stderr remain preserved. A plain system-Python monitor invocation then failed before starting a worker because `psutil` was unavailable; its [failure receipt](query_launch_v1_failure.json) and raw replay are separate from the checked-Sage-launched measured query.

## Decision and next gate

The overlapping tree is a sound, fully checked N41 source constraint, yet doubling target paths left this unpinned CryptoMiniSat query bounded at 600 seconds. The next solver experiment should keep the **16,851-AND direct bilinear leaves** and add a selector for the **41 Frobenius conjugates** of the same raw public point. The archived native orbit join independently verified one relation per conjugate, so that change supplies many valid assignments while retaining a compact source law. Freeze one-tree-plus-orbit first to isolate the selector effect; test a second tree only if the first query benefits. Any SAT output needs source-state extraction and independent group replay, followed by a source-bound N131 construction under the one-worker, 600-second, 4-GiB gate. The one-target online IC/rho comparison remains downstream of verified relation collection, rank and target descent.
