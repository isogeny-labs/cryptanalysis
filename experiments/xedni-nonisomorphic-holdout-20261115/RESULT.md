# Three qualified nonisomorphic lifts in a frozen eight-field holdout

The deterministic holdout screen found **three** additional rank-one rational curves among the 32 nonbase centered lifts attempted on eight previously unseen prime-order fields. Each selected point passed a separate checked-Sage signed-generator proof. Adding these curves expands the radius-four ordered-pair image from 81 to 137 at `p=773` and `p=883`, and from 81 to 153 at `p=983`. Three pinned Lean theorems prove those exact pair-union counts.

The complete public-point replay covers **9,875,576 ordered target queries**. It records 44 per-model rational `(1,2)` relations on 40 distinct query pairs, with all 44 checked again on their exact rational curves and against the public target in Sage. In every field, the first directly testable reduced-group relation occurs earlier in the same frozen query order than the first admitted rational relation.

## Frozen field and curve selection

Before any rank call, `protocol.json` fixed the rule: scan prime `p>677` upward and take the first eight for which `#E(F_p)` is prime, for `E:y²=x³−x−2`. `select_fields.py` uses exact finite-field point counts and trial-division primality. The resulting `(p,q)` pairs are `(773,751)`, `(863,883)`, `(883,883)`, `(983,983)`, `(1049,1103)`, `(1153,1153)`, `(1423,1453)`, and `(1433,1459)`. Each field screens `u=1,2,3,4,5` using the same centered lift `B=y²−x³+x` and a 12-second checked-Sage rank cap, with at most two concurrent workers.

| Screen status | Cells |
| --- | ---: |
| Exact rank proved, including eight base cells | 30 |
| Exact rank unresolved | 3 |
| Reached 12-second cap | 7 |

Among the 30 completed cells, 11 have proved rank one: eight base cells and three nonbase cells. The other completed ranks are 14 at rank two, four at rank three, and one at rank five. The three qualified nonbase curves are:

| Field `p` | Subgroup `q` | `u` | Rational `B` | Centered generator | Pair union |
| ---: | ---: | ---: | ---: | --- | ---: |
| 773 | 751 | 2 | 13,494,259 | `(-238,-115)` | 137 |
| 883 | 883 | 2 | 4,439,722 | `(-162,-434)` | 137 |
| 983 | 983 | 3 | −21,566,039 | `(279,-389)` | 153 |

Sage proves rank one, trivial rational torsion, good reduction at the field prime, and generator completeness for these three curves; their exact `j` invariants differ from the base. Unresolved and timed-out cells remain in the raw screen records and are not promoted. This holdout is deterministic and conditioned on prime group order. The observed three qualified nonbase curves are a finite-panel result, with ten censored rank outcomes, rather than an unseen-prime probability estimate.

## Complete relation and direct-control replay

For each field, the fixture target is `Q=17G`. The producer constructs `Q` once, forms public points `R(t)=Q−tG` by elliptic-curve arithmetic, and evaluates every ordered pair `(t₁,t₂)∈[0,q)²`. It tests membership in each qualified curve's radius-four reduction image and then checks the rational `(1,2)` relation on admitted distinct nonidentity pairs. The direct control tests `R₁+2R₂=O` on the same public query order. The fixed scalar is used afterward for correctness replay.

| `p` | Qualified `u` | Pair union | Distinct rational-relation queries | First direct query | First rational query |
| ---: | --- | ---: | ---: | ---: | ---: |
| 773 | 1, 2 | 137 | 6 | 402 | 6,781 |
| 863 | 1 | 81 | 4 | 468 | 11,499 |
| 883 | 1, 2 | 137 | 6 | 468 | 7,969 |
| 983 | 1, 3 | 153 | 8 | 518 | 4,939 |
| 1049 | 1 | 81 | 4 | 578 | 14,359 |
| 1153 | 1 | 81 | 4 | 603 | 15,009 |
| 1423 | 1 | 81 | 4 | 753 | 18,909 |
| 1433 | 1 | 81 | 4 | 756 | 18,987 |

The full replay charges 12,185,555 per-model pair-membership checks and 616 admitted rational relation tests. It retains 9,849,588 admissible direct public tests across the complete scans. The 44 per-model rational relations reduce to 40 distinct public query pairs because the two `u=2` models share two positive pairs with their bases in each corresponding field. These counts include the complete query scans; the 40 rank attempts and three generator checks are separately retained setup work. Query positions and operation counts are not wall-time or rho speed measurements.

## Proof map and verification

| Result | Proof or independent check | Scope |
| --- | --- | --- |
| Pair union 137 at subgroup orders 751 and 883 | `XedniNonisomorphicHoldout.pair_union_card_751`, `pair_union_card_883` | Radius-four images of generators reducing to `G` and `2G` |
| Pair union 153 at subgroup order 983 | `XedniNonisomorphicHoldout.pair_union_card_983` | Radius-four images of generators reducing to `G` and `3G` |
| Field orders, all 9,875,576 query statuses, first direct and rational events | Independent `audit.py` with a separate finite-field group implementation | Exact frozen eight-field panel and public query law |
| Three generator proofs, 44 rational group equations, and eight first-direct scalar replays | Checked-Sage `sage_audit.py` plus retained generator workers | Exact selected rational curves and public targets |

The Lean project pins `v4.35.0-rc4` and Mathlib `021c46bdd042f67b538b9f9871d556a93713a9a9`. `lake build HoldoutUnion` passed 3,138 jobs; all three `#print axioms` reports list only `propext`, `Classical.choice`, and `Quot.sound`. The formal theorem proves the exact finite-set counts. Rational curve ranks, generator completeness, and point reduction are independently checked in Sage; a full Lean formalization of those elliptic-curve facts remains open. `lean4checker --fresh` was unavailable on this host.

The first screen launch failed before any rank cell because `select.py` shadowed Python's standard module. A second launch failed because the protocol omitted the runner's explicit `u_values`; the saved `protocol-initial.json` and both stderr files preserve these setup attempts. The corrected selector and protocol were fixed before the 40-cell rank run. The first Sage relation audit failed by converting rational point coordinates with `int`; its source and stderr are retained. The corrected audit maps exact rational coordinates into `GF(p)` and passes. A scalar-index diagnostic producer preceded the final public-point producer; both summaries and all eight compressed raw-row hashes match exactly. Only the public-point producer supports the reported query-work accounting.

## Reproduce

From the repository root, run `select_fields.py`, save `./sage --runtime-info`, run `screen.py`, `generator_screen.py`, and `relation.py`, then run `audit.py` and `./sage -python experiments/xedni-nonisomorphic-holdout-20261115/sage_audit.py`. Every screen and generator child invokes the checked `/Volumes/SSD990/cryptanalysis/sage` launcher. Build the Lean theorem with `(cd experiments/xedni-nonisomorphic-holdout-20261115/formal && lake build HoldoutUnion)`, then run `python3 experiments/xedni-nonisomorphic-holdout-20261115/verify.py`. The compressed row streams, per-cell stdout/stderr, runtime receipt, build output, and SHA-256 seal accompany this report.
