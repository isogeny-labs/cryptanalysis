# Cofactor-four class routing gives little early pruning on W18 terminal families

The exact mod-four character census found **130 admissible W18 terminal edge pairs** on the frozen N131 public workload. Twelve edge pairs have one attainable cofactor class across their sixteen signed states; the other **118 have two classes of the same parity**. Even if the seven-free-pair sum class were already known, a mod-four router would remove one additional raw-lift choice beyond the existing trace-parity gate for only those twelve edge families. That is **12 of 260 trace-admitted edge/fiber choices, or 4.615%**. The result screens this character as a limited early-pruning direction for the current source law.

## Exact character and input law

The curve is `y²+xy=x³+1` over `GF(2)[t]/(t^131+t^13+t²+t+1)`, with curve ID `EC1N131Ckb1heb5f1998f20b`, subgroup order `r=680564733841876926932320129493409985129`, and `#E=4r`. The rational point `T=(1,0)` has order four. Label a raw point `P` by the unique `c∈{0,1,2,3}` satisfying `[r]P=[c]T`. This is an additive class map. The same construction controls the ordinary N41 relation with subgroup order `549756390943`. The [protocol](protocol.json) pins the frozen W18 terminal pool, the same public workload `cc09e7eb202a`, the previous independent public-residual audit, checked Sage runtime, script hash, one worker, a 300-second bound, and a 4-GiB observation envelope. `candidate_id` remains `null` for this component.

The producer computes `[r]P` for all 48 left and 48 right terminal signed states and the four public raw lifts. It derives all 2,080 admissible terminal joint classes by addition in `Z/4Z`, then directly checks 20 saved public residual points with `[r]`. The raw lifts have class order `(0,2,1,3)`, so a fully signed source sum picks exactly one lift. The [independent checked-Sage audit](audit_result.json) obtains every terminal class from a halftrace halving criterion instead of scalar multiplication, recomputes all 130 edge-pair support sets, and checks the N41 ordinary relation. Its exact field derivation and formalization scope are in the [proof map](PROOF_MAP.md).

| Frozen N131 W18 source statistic | Exact result |
| --- | ---: |
| Terminal signed states, left / right | 48 / 48 |
| Admissible terminal state pairs / edge pairs | 2,080 / 130 |
| Edge pairs with one / two attainable classes | 12 / 118 |
| State pairs belonging to singleton-class edge families | 192 of 2,080 |
| Left class counts `(0,1,2,3)` | `(18,6,18,6)` |
| Right class counts `(0,1,2,3)` | `(18,6,18,6)` |
| Admissible joint class counts `(0,1,2,3)` | `(576,432,640,432)` |
| x buckets with fixed class `0` / fixed `2` / inverse ambiguity `{1,3}` | 18 / 18 / 12 |
| Direct public residual class checks | 20, all matched additive prediction |
| Producer internal wall / peak self RSS | 0.692770 s / 278,773,760 B |

Every admissible edge pair contains all sixteen terminal sign choices; its class set has fixed parity. The earlier target-conditioned trace gate therefore leaves two possible raw classes per edge pair. Granting the free-seven class without charging how it is obtained, the mod-four class cuts that to one raw choice for twelve edge pairs and leaves two for 118. The average falls from `2` to `(12+2×118)/130 = 248/130`. This is an upper bound on extra *pre-sign* routing benefit for these edge families, not a solver-time prediction. The seven free pair outputs are represented by x coordinates and S3 branch bits; for twelve terminal x buckets the two signed points share x but have classes `1` and `3`, so the second class bit cannot generally be read from x alone.

The archived unpinned N41 seven-pair relation passes the same class law: its four raw fibers have classes `(0,2,3,1)`, the five-free-pair sum has class zero, and the two-terminal sum has class zero, selecting raw fiber zero. The N131 class parity matches `Tr(1/x)` on all 96 terminal states, connecting this census to the preceding [trace-parity experiment](../n131_w18_fourfiber_trace_parity_20261017/RESULT.md).

`lean ClassBound.lean` passes under pinned Lean 4.34.1. The inverse-class and two-sign structural theorems have no axioms; the concrete four-label ordering uses only Lean's `propext` and `Quot.sound` in [build output](lean_check.log). The standalone Lean environment did not expose the first draft's group names; [that failed formalization attempt](lean_attempt1.log) is retained.

This preflight does not justify another 600-second public SAT run with only a mod-four class row. The next target-derived constraint needs a nonhomomorphic condition on two or more unresolved source-code families that rejects them before signed point expansion. The exact quotient-algebra inverse and N41 ordinary relation controls in the adjacent experiments provide the next correctness gate; cost must be measured against full family traversal before N131 promotion.
