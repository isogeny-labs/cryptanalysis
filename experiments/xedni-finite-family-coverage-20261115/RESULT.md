# A frozen 13-vector family covers at most 13 targets per tested offset

For a prime-order group with generator `G`, public target `Q=dG`, and public query points `R₁=Q`, `R₂=Q−tG`, an effective coefficient pair `(a,b)` gives a relation precisely when `(a+b)d=bt (mod q)`. If `a+b≠0 (mod q)`, this equation selects exactly one target scalar for a fixed offset. Therefore a fixed family of `B` effective vectors tested at `L` offsets covers at most `B·L` target scalars. Under a uniform nonzero target law, its success probability is at most `min(1,B·L/(q−1))`. The frozen 14-vector family has 13 effective vectors; its `(1,−1)` vector has zero coefficient sum. For the first `L` lexicographic queries, offset zero is inadmissible, giving the bound `min(q−1,13(L−1))` covered nonzero scalars.

The exact exhaustive counts below show substantial overlap among those candidate scalar values. For the first 35 queries, 268 nonzero targets are covered in each field, versus the 442-target union bound. The target fraction ranges from `268/750` on the `q=751` field to `268/1458` on the `q=1459` field.

| Field `p` | Order `q` | Targets by query 35 | By 64 | By 128 | By 256 | Total nonzero targets |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 773 | 751 | 268 | 485 | 698 | 743 | 750 |
| 863 | 883 | 268 | 492 | 794 | 863 | 882 |
| 883 | 883 | 268 | 492 | 794 | 863 | 882 |
| 983 | 983 | 268 | 497 | 845 | 954 | 982 |
| 1049 | 1103 | 268 | 497 | 900 | 1062 | 1102 |
| 1153 | 1153 | 268 | 497 | 923 | 1107 | 1152 |
| 1423 | 1453 | 268 | 497 | 965 | 1356 | 1452 |
| 1433 | 1459 | 268 | 497 | 966 | 1362 | 1458 |

## Proof and methods

Let `C` be a finite family of effective coefficient pairs and `T` a finite offset set. The checked Lean theorem `relation_eq_candidate` proves the unique scalar identity `d=bt/(a+b)` from the reduced public relation equation. `relation_mem_winners` carries every such relation into the finite image of `C×T`. `card_winners_le` proves its cardinality is at most `|C||T|`; `card_winners_le_cap` transports explicit family and offset caps. `effective_integer_family_card` checks that the frozen integer family has 13 nonzero-sum vectors. The Lean statements hold for a general field; the report’s prime-order group bridge uses the standard order-`q` identity and is checked on every target by the Sage audit.

The producer inverts the modular relation for each effective vector and each nonzero offset, preserving the earliest query and vector for every nonzero scalar. The independent audit instead scans offsets in query order for each scalar, checks all earlier relation tests, confirms `#E(F_p)=ord(G)=q`, and replays the first relation with Sage elliptic-curve points. It covers all `q−1` nonzero targets in each of the eight fields and reproduces every cap count. The full row reaches every nonzero scalar, as the `(1,1)` vector relates at offset `2d (mod q)`. The curve and factor-family hashes are pinned in `protocol.json`.

The theorem is conditional on a family and offset set fixed independently of the target. Adaptive coefficient discovery, additional query rows, and costs of choosing rational curve models require separate accounting. The counts here are exact finite-field coverage, not measured wall time. A next experiment can freeze a larger target panel and charge adaptive family construction, all public queries and relation checks, scalar replay, and matched rho on the same target.

Reproduce with `python3 experiments/xedni-finite-family-coverage-20261115/run.py`, `./sage --runtime-info`, `./sage -python experiments/xedni-finite-family-coverage-20261115/audit.py`, `(cd experiments/xedni-finite-family-coverage-20261115/formal && lake build FiniteFamilyCoverage)`, and `python3 experiments/xedni-finite-family-coverage-20261115/verify.py`. The Lean build passed 3,138 jobs and all five `#print axioms` checks use only standard Lean foundations. `lean4checker --fresh` was unavailable on this host.
