# Height growth forces long relations on a fixed rank-one curve

The checked theorem `XedniHeightGrowthObstruction.group_pair_relation_lower_bound` states that, for any infinite-order point `P`, every nontrivial integer relation `aP+b(nP)=0` has `|a|≥n`. The bound is attained by `−nP+(nP)=0`. Thus rank deficiency by itself supplies no coefficient bound uniform in the selected point heights, even while the rational curve and its rank stay fixed.

For the full coefficient box `|a|,|b|≤K`, `integer_pair_box_collision_iff` checks that a collision exists exactly when `n≤2K` for `K>0`. The paired finite-packing estimate uses `r=2`, `d=T=1`, a norm cap `B=nδ`, and the inequality `1+4nK<(2K+1)²`. `packing_criterion_iff` checks that this strict estimate holds exactly when `K≥n` for `K>0`. The packing certificate therefore follows the optimal collision radius within a factor of two: the first actual box collision is `K=⌈n/2⌉`, while the sufficient packing test first holds at `K=n`.

On a rank-one elliptic curve with generator `P`, canonical-height quadraticity gives `ĥ(nP)=n²ĥ(P)`. The ratio `B/δ=n` grows with the selected multiple. Any use of the finite-packing relation theorem with a uniform `K` must therefore control selected point heights relative to the minimum positive height. This is a precise falsifier for a rank-only bounded-witness premise in the xedni lift argument; it leaves the selected-lift height/discriminant condition as the arithmetic step to test.

## Proof map

| Result | Lean declaration | Exact hypotheses |
| --- | --- | --- |
| Integer coefficient lower bound | `integer_pair_relation_lower_bound` | `a+bn=0`, nontrivial integer pair |
| Group coefficient lower bound | `group_pair_relation_lower_bound` | Additive group, `P` of infinite order, relation among `P,nP` |
| Attaining relation | `group_pair_relation_attained` | Any additive group and natural `n` |
| Packing threshold | `packing_criterion_iff` | Positive `K`; `(1+4nK)<(2K+1)²` iff `n≤K` |
| Exclusion below half radius | `no_relation_below_half` | Infinite-order `P`, relation coefficient `|a|≤2K`, `2K<n` |
| Exact coefficient-box collision | `integer_pair_box_collision_iff` | Positive `K`; four coefficients inside `[-K,K]` and equal scalar images |
| Selected elliptic-lift height condition | Open | Uniform bound on selected lift point heights relative to the minimum positive height |

The formal project pins Lean `v4.35.0-rc4` and Mathlib `021c46bdd042f67b538b9f9871d556a93713a9a9`. `lake build HeightGrowthObstruction` completed 9040 jobs. The six new `#print axioms` records contain only `propext`, `Classical.choice`, and `Quot.sound` as applicable. `lean4checker --fresh` was unavailable on this host.

## Fixed-curve panel and execution record

The frozen curve is `E/ℚ: y²=x³−x−2`, with `P=(2,2)`. The checked Sage launcher reports rank one, trivial torsion, and `P` as its generator up to sign. The panel uses `(P,nP)` for the eight prespecified `n` values below and retains every `K=0,…,n`. Sage's default normalised Néron–Tate height gives the displayed ratios; the exact sum counts are integer scalar-image counts transported through the checked infinite-order premise. The independent audit recomputed every count by interval union and rechecked the curve premises and boundary group identities.

| `n` | Displayed `ĥ(nP)/ĥ(P)` | First box collision `K` | First packing certificate `K` |
| ---: | ---: | ---: | ---: |
| 1 | 1 | 1 | 1 |
| 2 | 4 | 1 | 2 |
| 3 | 9 | 2 | 3 |
| 5 | 25 | 3 | 5 |
| 8 | 64 | 4 | 8 |
| 13 | 169 | 7 | 13 |
| 21 | 441 | 11 | 21 |
| 34 | 1156 | 17 | 34 |

The first source attempted to multiply every rational point in every coefficient box. It remained live at 100% CPU after an observed 104 seconds, produced no result rows, and was interrupted; its traceback and empty stdout are retained. `AMENDMENT.md` and `PROTOCOL-v2.json` preserve that censored status and explain the switch to exact scalar-image enumeration. The amended run and independent audit passed all 95 retained cells with empty stderr. Both Sage runtime receipts are saved. The panel varies selected points on one fixed curve and tests the height-growth mechanism directly; applying it to the original selected lift policy requires that policy's point-height law.

The next experiment should freeze an actual selected-lift family and measure or bound `max_i ĥ(P_i) / μ` under its admission rule, retaining every failed curve search and reduction status.
