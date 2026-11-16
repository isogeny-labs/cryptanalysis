# Every detected selected-vector relation has a rank-one rational realization

For each of the **6,136** public relations in the frozen eight-field selected-vector panel, a deterministic vector-dependent construction produced a nonsingular rational curve and rational points with the required reductions and coefficient relation. The construction has **zero failed events**. It begins only after testing the public equation `aU+bV=O`; at that point the same equation already recovers the target scalar when `a+b` is invertible. This is a complete constructive realization for this panel, with the information order made explicit.

| Field `p` | Subgroup `q` | Public relations | Verified rational constructions | Failed constructions |
| ---: | ---: | ---: | ---: | ---: |
| 47 | 43 | 546 | 546 | 0 |
| 101 | 53 | 676 | 676 | 0 |
| 191 | 53 | 676 | 676 | 0 |
| 211 | 79 | 1014 | 1014 | 0 |
| 251 | 61 | 780 | 780 | 0 |
| 281 | 73 | 936 | 936 | 0 |
| 347 | 47 | 598 | 598 | 0 |
| 349 | 71 | 910 | 910 | 0 |

The public phase retains **30,008** ordered queries and **371,592** vector tests. The construction phase performs **6,136** modular inverses, **6,136** public scalar multiplications, **6,136** rational curve constructions, **12,272** rational scalar multiplications, **6,136** rational relation tests, **12,272** reduction checks, and **6,136** independent scalar replays. The runner builds 480 distinct sampled public points, one per offset across the eight fields, and reuses them across ordered pairs. These are stage-operation counts; the package does not convert them into wall time.

## Construction and proof

Write `U=Q−t₁G` and `V=Q−t₂G` in a group of prime order `q`. After a nonzero-sum public relation `[a]U+[b]V=O` is detected, `b` is invertible modulo `q`. Set `T=[b⁻¹]U`. Then `[b]T=U`, and the public equation gives `[-a]T=V`. Center integer representatives `(x,y)` of `T` and put `B=y²−x³+x`. The curve `E_B/ℚ: Y²=X³−X+B` contains the rational point `P=(x,y)` and reduces to `Y²=X³−X−2` modulo `p`. It is nonsingular over `ℚ` for every integer `B`. Set `A=[b]P` and `C=[−a]P`; their reductions are `U,V`, and `[a]A+[b]C=O`. Good reduction at the panel primes and every point reduction were checked in Sage.

The pinned Lean module proves `public_factorization` over a field, the rank-one identity in any additive commutative group, and its specialization to the rational point type supplied by the imported `AdaptiveInverseLift.lean`. The imported module checks curve nonsingularity and reduction of the integer model. The earlier checked `XedniDirectRelation.finite_relation_recovers` supplies scalar recovery from a nonzero-sum public relation. `PROOF_MAP.md` gives the exact hypotheses and the one remaining formal bridge: Lean does not yet show that reducing arbitrary scalar multiples of this rational point agrees with scalar multiplication on the specified finite-field curve. The independent Sage audit checks that bridge for every event.

## Frozen experiment and independent replay

`protocol.json` pins the selected family, parent public-relation packet, and imported formal source before the run. The producer first tests all selected vectors on every admissible public pair, then constructs one rational model per actual hit. Each event row retains its query, vector, common point, curve coefficient, rational point digest, recovered scalar, and status. The independent checked-Sage audit enumerates all public relations anew from the fixture equation, replays every rational curve and group relation, verifies both reductions, compares point digests, and checks all **6,136** scalar recoveries. It passes with empty stderr.

This construction shows how to manufacture a rational relation once the public relation is available. It does not supply the public relation earlier or reduce its search cost. The next proof step is to formalize the reduction-of-multiples bridge and to derive a query-cost lower bound for any vector-dependent lift whose construction requires this public preimage.

Reproduce with `./sage --runtime-info`, `./sage -python experiments/xedni-vector-dependent-rank-one-lift-20261115/run_sage.py`, `./sage -python experiments/xedni-vector-dependent-rank-one-lift-20261115/audit_sage.py`, `(cd experiments/xedni-vector-dependent-rank-one-lift-20261115/formal && lake build VectorDependentRankOneLift)`, and `python3 experiments/xedni-vector-dependent-rank-one-lift-20261115/verify.py`. The Lean build passed **3,157** jobs; all five `#print axioms` outputs contain standard Lean foundations only.
