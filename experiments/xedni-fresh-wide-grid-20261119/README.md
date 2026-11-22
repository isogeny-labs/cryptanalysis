# Fresh precommitted five-shift lift panel

The precommitted five-shift rule produced **14 public relations in 6,656 fixed-vector tests** on a fresh deterministic panel. Across all 8,750 frozen rational candidate models for those relations, exact group arithmetic found **zero rational relations**. The rule selected a height-minimizing model before each query's coefficient tests. An independent replay passed every field, public query, candidate, selection, and relation check.

## Frozen experiment

[The protocol](protocol.json) fixes the eight prime fields and prime-order subgroups from the hashed registry, the 13-vector family, the offset pair law, and a new target seed label `xedni-wide-grid-v1|p|j`. It creates four targets and 16 public queries per field: 512 queries and 6,656 vector tests. For a distinct-x pair, it precommits to all `5^4 = 625` shifts in `{-2,-1,0,1,2}^4`, interpolates a rational short Weierstrass model through the two shifted points, and selects the valid candidate minimizing the maximum bit length of the model coefficients and point coordinates. Ties use lexicographic shift order. An equal-x opposite pair uses one specified centered construction.

The runner records every candidate attempt, including invalid models, then screens the vectors. On a public relation hit, it tests **all** valid candidates in that query's frozen grid with the exact rational elliptic group law. The separate selected-lift relation result remains tied to the height rule. The input points, candidate construction, and scalar fixtures are outside any timing comparison.

| Field `p` | Subgroup `q` | Public hits / 832 tests | Hit-candidate checks | Rational relations |
| ---: | ---: | ---: | ---: | ---: |
| 313 | 331 | 0 | 0 | 0 |
| 421 | 439 | 0 | 0 | 0 |
| 431 | 419 | 2 | 1,250 | 0 |
| 547 | 571 | 0 | 0 | 0 |
| 571 | 599 | 4 | 2,500 | 0 |
| 593 | 313 | 3 | 1,875 | 0 |
| 617 | 293 | 2 | 1,250 | 0 |
| 677 | 353 | 3 | 1,875 | 0 |
| **Total** | | **14 / 6,656** | **8,750** | **0** |

All 316,880 candidate constructions passed, across 507 distinct-x queries and five equal-x exception queries. No equal-x query had a public relation hit. All 512 selected rational curves passed, and selected rational relations were zero. A secondary score calculation from the retained candidate ledger shows that allowing shifts of magnitude two reduced the minimum full-model score compared with the nested magnitude-one grid on 256 queries; the paired median scores were 23 and 22 bits. This measures model representation size, not relation probability.

This result covers the finite shift grid, fixed vector family, and deterministic panel specified in the protocol. The relation-dependent construction recorded in `xedni-known-relation-lifts-20261118` gives rational witnesses when coefficients are already supplied; the fresh precommitted grid did not contain such a witness for any of its 14 public hits. A next proof step is to bound which rational point dependencies can occur under a public-only model-selection rule. A next experiment can enlarge the grid again with a new target law, retaining the full attempt count and selected rule.

## Reproduce and verify

```sh
python3 experiments/xedni-fresh-wide-grid-20261119/run.py
python3 experiments/xedni-fresh-wide-grid-20261119/audit.py
```

`run.py` writes `result.json`, the complete hashed `queries.jsonl.gz`, `vectors.jsonl.gz`, `hit-candidates.jsonl.gz`, and 32 `candidates.partNN.jsonl.gz` ledger chunks. `audit.py` verifies their compressed and raw digests, checks curve orders and generators, replays the frozen query law, recomputes every candidate and selector, and uses repeated addition to check all relation outcomes. Its receipt is [audit-result.json](audit-result.json). The producer's elapsed wall interval was 5.672 seconds on this host; this is a local script diagnostic without host isolation or paired same-target timing. No Sage job is used.
