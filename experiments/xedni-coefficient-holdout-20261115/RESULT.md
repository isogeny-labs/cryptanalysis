# The frozen 14-vector public search hits at query 35 on every holdout field

The coefficient family fixed in the earlier eight-field training control reaches its first scalar-recovering public relation at **query 35** on each of the eight unseen prime-order fields. The field changes while the fixture scalar remains 17 throughout this panel; this measures cross-field transfer of the frozen vector family for that target law. With the original lexicographic vector order and immediate stop, it performs **452 vector tests** and **3,065 abstract group-add calls** per field. The successful vector is `(1,1)` at offsets `(t₁,t₂)=(0,34)`; the recovered scalar independently multiplies the public generator to the fixture target. The corresponding fixed `(1,2)` public relation occurs at queries 402–756, while the first admitted rational `(1,2)` relation in the parent holdout occurs at queries 4,939–18,987.

| Field `p` | Subgroup `q` | First 14-vector query | Vector tests | Group-add calls | First `(1,2)` public query | First rational `(1,2)` query | Parent membership checks through rational hit |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 773 | 751 | 35 | 452 | 3,065 | 402 | 6,781 | 13,562 |
| 863 | 883 | 35 | 452 | 3,065 | 468 | 11,499 | 11,499 |
| 883 | 883 | 35 | 452 | 3,065 | 468 | 7,969 | 15,938 |
| 983 | 983 | 35 | 452 | 3,065 | 518 | 4,939 | 9,878 |
| 1049 | 1103 | 35 | 452 | 3,065 | 578 | 14,359 | 14,359 |
| 1153 | 1153 | 35 | 452 | 3,065 | 603 | 15,009 | 15,009 |
| 1423 | 1453 | 35 | 452 | 3,065 | 753 | 18,909 | 18,909 |
| 1433 | 1459 | 35 | 452 | 3,065 | 756 | 18,987 | 18,987 |

The direct first-hit work includes the 34 point additions that advance the second public query point from `Q` through `Q−34G`. It also includes every add call made by scalar multiplication and combination for the 452 tested vectors, including non-hits and the three earlier vectors at the successful query. The fixture's `Q=17G` construction and the final scalar replay are separate correctness work. An abstract add call is a reproducible operation count, not a CPU or wall-time estimate. The parent rational search also pays its 40 rank-screen attempts and three generator checks; those setup costs are retained in its own artifacts. Membership lookups, group additions, rank calls, and rational group tests are distinct work units and are not converted into a speedup ratio here.

## Frozen rule and independent checks

`protocol.json` pins the exact SHA-256 of the earlier 14-vector family source and protocol, the holdout fields, ordered query law, admissibility rule, vector order, and immediate stop. The final producer uses public elliptic-curve points and generates `Q−tG` lazily. The first producer computed all `q` query points before stopping; its source, protocol, summary and identical per-field prefix rows are retained. The amended protocol adds lazy generation and explicit add-call accounting without changing the vector family or hit rule.

The independent checked-Sage audit reconstructs the public curve and target in each field, replays every saved vector test through the first hit, checks scalar recovery, verifies the parent fixed-vector first event, and reads the parent compressed status stream through its first rational relation. Its independent operation formula reproduces 452 vector tests and 3,065 add calls in every field. All eight audit rows pass. A checked Sage runtime receipt accompanies this run.

The pinned Lean module `FirstFamilyHit.lean` proves that the listed vector image equals the frozen 14-element family, that `(1,1)` relates at offset 34, and that no admitted offset below 34 relates under any vector for each of the seven distinct subgroup orders in this eight-field panel. The earlier zero-sum vector `(1,-1)` relates at offset zero only when the two public points coincide, which the frozen admission rule excludes. The early-offset theorems explicitly exclude offsets zero and 17, where the pair is duplicate or contains the identity. The Lean project pins `v4.35.0-rc4` and Mathlib `021c46bdd042f67b538b9f9871d556a93713a9a9`; `lake build FirstFamilyHit` passed 3,138 jobs and all nine `#print axioms` outputs contain only standard Lean foundations. `lean4checker --fresh` was unavailable on this host.

The earlier checked `XedniDirectRelation.finite_relation_recovers` theorem supplies the nonzero-coefficient-sum recovery algebra. The present holdout measures an already specified public vector family; it does not establish the cost of discovering new useful vectors after curve selection. A future paired wall-time experiment must freeze the resource tier and charge public query generation, every vector test, rational curve selection, rank work, relation checks, scalar verification, and matched rho on the same target.

Reproduce from the repository root with `python3 experiments/xedni-coefficient-holdout-20261115/run.py`, then `./sage --runtime-info` and `./sage -python experiments/xedni-coefficient-holdout-20261115/audit.py`. Build the pinned module with `(cd experiments/xedni-coefficient-holdout-20261115/formal && lake build FirstFamilyHit)`, then run `python3 experiments/xedni-coefficient-holdout-20261115/verify.py`. The sealed artifact set contains the source, both producer versions, complete first-hit prefixes, Sage audit, Lean build output and runtime receipt.
