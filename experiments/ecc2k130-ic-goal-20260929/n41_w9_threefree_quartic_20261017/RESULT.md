# Three-free-pair target-conditioned quartic search

With only slots 0 and 4 fixed, a target-conditioned two-product eliminant searched the remaining **284 × 71 = 20,164 specialized N41 quartics** and found both signed forms of the archived ordinary relation. An independent group-sum index audited the entire 284-state by 284-state pair domain and found exactly the same two witnesses. The new search completed in 232.34 s and 248 MB peak RSS. For this N41 instance, the direct group index completed its full build and query in 7.66 s; this is a negative performance gate for the current Sage quartic implementation, even though the eliminant is a compact exact constraint.

## Instance, input law, and algorithm

The field is `GF(2)[u]/(u^41+u³+1)` and the curve is `y²+xy=x³+1`, ID `EC1N41Ckb1h7d5e80d3c4d0`. The frozen aligned W9 source has 71 canonical valid codes and 284 signed states per slot, with rotations `(0,0,12,12,24)`. The public target uses orientation 6. State IDs 105 and 111 in slots 0 and 4 were chosen **retrospectively** from the archived ordinary relation. Slots 1, 2, and 3 were searched without fixing their code or signed state. The exact source and checked Sage runtime are SHA-256 pinned in [protocol.json](protocol.json).

For each of the 284 slot-1 states, the search forms the public residual `T=Q-P₀-P₄-P₁`. Slots 2 and 3 share Frobenius rotation 12, so their source-product maps lie in the same 8-dimensional binary subspace. The [previous two-product eliminant](../n41_w9_two_product_eliminant_20261017/RESULT.md) gives `H_T(p,q)=0`, a bidegree-(4,4) necessary condition for their point sum to equal `T`. Each of the 71 left products specializes `H_T` to a quartic in the right product. Modular evaluation of the 9-coefficient linearized subspace annihilator, a polynomial GCD, and deterministic trace splitting find right-subspace roots without enumerating all 256 subspace elements. Valid right codes are mapped back to four signed states, and every surviving point sum and ten-column condition is checked directly. All 284 residuals were in the nonexceptional S3 chart; the exception count is recorded as zero.

## Results and independent audit

| Stage | Work | Measured time | Peak RSS / result |
| --- | --- | ---: | --- |
| Target-specific eliminant builds | 284 residuals | 0.439 s | Included in quartic process |
| Quartic subspace roots | 20,164 specializations | 231.522 s | Total GCD degree 2 |
| Exact replay | Two code hits, four signed states per code | 0.003 s | Two valid witnesses |
| Complete quartic search | One checked Sage process, 600 s wall cap | **232.344 s** | 248,463,360 B peak RSS |
| Independent pair-sum index | All 284² = 80,656 signed slot-2/3 pairs | 7.638 s | 40,329 distinct point-sum keys |
| Independent outer queries | All 284 slot-1 states | 0.024 s | Two raw and two column-valid hits |
| Complete indexed audit | Index build plus queries | **7.662 s** | 247,185,408 B peak RSS |

The algebraic hits were `(outer state, left code, right code) = (244,11,16)` and `(244,16,11)`. The independently replayed state tuples were `(105,244,47,66,111)` and `(105,244,66,47,111)`. The pair-sum audit did not use the eliminant to generate candidates: it indexed every signed point sum for slots 2 and 3, queried the public residual for every slot-1 state, checked all ten folded columns, and compared its final witness set with the producer. Its raw group-hit count was exactly two.

The timings exclude checked-Sage startup, input loading, and fixture construction. They are exploratory readings on a shared host. The full indexed build is about **30.3 times faster** than the quartic path here; its separate 0.024 s query interval uses the reusable 80,656-entry table. Both methods were run as one process each; the 4 GiB envelope was observed through RSS but not enforced by the OS. This workload retains `candidate_id: null`: its two fixed states were selected from a known relation, and it has no unseen single-target IC/rho comparison.

## Cost boundary and next discriminator

The N41 index wins because the two free signed point sets each contain only 284 states. The audited N131 W29 sample already has 16,677 valid source pairs, or 66,708 signed states if each yields four states. A direct all-pairs table for **that sample alone** would require 4,449,957,264 pair entries before duplicate folding; even an ideal 8-byte entry would require about 35.6 GB, above the 4 GiB goal envelope. This is a lower-bound calculation for the sampled table representation, not a measured N131 run. The N131 full-source population projection is much larger.

The quartic method keeps the right source subspace implicit, but its 20,164 N41 specializations already consumed 231.5 s. Scaling to N131 by simply enumerating an outer signed state and all valid left codes is therefore not promoted. The next algorithmic step is a **joint constraint on three unresolved source products** that rejects outer families before generating all their signed states, followed by a frozen native GF(2^131) operation-cost gate. The immediate falsifier is whether this constraint has a compact source-code evaluation whose measured query count and throughput can fit one worker, 600 s, and 4 GiB on the public N131 point. The central quadratic-resultant implication is Lean checked in the [prior theorem module](../n41_w9_two_product_eliminant_20261017/TwoProductEliminant.lean); this run adds a complete finite-domain search and independent group audit rather than a new structural theorem.
