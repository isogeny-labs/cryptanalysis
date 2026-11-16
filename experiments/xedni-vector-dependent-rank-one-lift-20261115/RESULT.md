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

Write `U=Q−t₁G` and `V=Q−t₂G` in a group of prime order `q`. After a nonzero-sum public relation `[a]U+[b]V=O` is detected, `b` is invertible modulo `q`. Choose integers `c,d` with `bc+qd=1` and set `T=[c]U`. Since `[q]` kills the subgroup, `[b]T=U`, and the public equation gives `[-a]T=V`. The new Lean theorems prove that the Bézout certificate makes multiplication by `b` bijective on any `q`-torsion additive group, and that the public relation is equivalent to this common rank-one preimage. Center integer representatives `(x,y)` of `T` and put `B=y²−x³+x`. The curve `E_B/ℚ: Y²=X³−X+B` contains the rational point `P=(x,y)` and reduces to `Y²=X³−X−2` modulo `p`. It is nonsingular over `ℚ` for every integer `B`. Set `A=[b]P` and `C=[−a]P`; their reductions are `U,V`, and `[a]A+[b]C=O`. Good reduction at the panel primes and every point reduction were checked in Sage.

The pinned Lean module proves `public_factorization` over a field, the public-group rank-one preimage equivalence, its Bézout specialization to `q`-torsion groups, the rank-one identity in any additive commutative group, its specialization to the rational point type supplied by the imported `AdaptiveInverseLift.lean`, and the compatibility of both constructed multiples and their relation with any additive reduction map. It also proves that the centered generator coordinates satisfy the finite curve equation and identify the selected finite point, conditional on the finite curve being elliptic. The imported module checks curve nonsingularity and reduction of the integer model. The earlier checked `XedniDirectRelation.finite_relation_recovers` supplies scalar recovery from a nonzero-sum public relation. `PROOF_MAP.md` gives the remaining formal bridge: construction of the actual good-reduction homomorphism for the rational elliptic curve and proof that it sends `liftPos` to the named finite point. The independent Sage audit checks the corresponding reductions for every event.

## Frozen experiment and independent replay

`protocol.json` pins the selected family, parent public-relation packet, and imported formal source before the run. The producer first tests all selected vectors on every admissible public pair, then constructs one rational model per actual hit. Each event row retains its query, vector, common point, curve coefficient, rational point digest, recovered scalar, and status. The independent checked-Sage audit enumerates all public relations anew from the fixture equation, replays every rational curve and group relation, verifies both reductions, compares point digests, and checks all **6,136** scalar recoveries. It passes with empty stderr.

The construction manufactures a rational relation after the public relation is available. The next proof step is to construct the concrete good-reduction homomorphism in Lean, prove its value on the named centered finite point, and derive a query-cost lower bound for vector-dependent lifts that require this public preimage.

Reproduce with `./sage --runtime-info`, `./sage -python experiments/xedni-vector-dependent-rank-one-lift-20261115/run_sage.py`, `./sage -python experiments/xedni-vector-dependent-rank-one-lift-20261115/audit_sage.py`, `(cd experiments/xedni-vector-dependent-rank-one-lift-20261115/formal && lake build VectorDependentRankOneLift)`, and `python3 experiments/xedni-vector-dependent-rank-one-lift-20261115/verify.py`. The Lean build passed **3,157** jobs; all twelve `#print axioms` outputs contain standard Lean foundations only.
