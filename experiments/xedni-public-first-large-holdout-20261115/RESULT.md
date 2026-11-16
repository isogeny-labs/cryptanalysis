# Larger-order public-first rank-one holdout: 142 verified rational constructions

On the frozen eight-field panel with subgroup orders 293–599, the selected 13-vector family produced **142 public relations** in 4,096 scheduled ordered queries. Every relation yielded a verified rank-one rational construction on the same public pair. The producer charged **52,936** actual finite-curve vector tests before construction; 24 queries were filtered because one point was identity or the pair coincided. The query schedule was fixed by SHA-256 and 512 indices per field before execution.

| Field `p` | Subgroup `q` | Admitted queries | Public vector tests | Public relations | Verified rational constructions | First hit query |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 313 | 331 | 507 | 6,591 | 20 | 20 | 7 |
| 421 | 439 | 512 | 6,656 | 18 | 18 | 14 |
| 431 | 419 | 510 | 6,630 | 20 | 20 | 14 |
| 547 | 571 | 507 | 6,591 | 15 | 15 | 44 |
| 571 | 599 | 511 | 6,643 | 10 | 10 | 19 |
| 593 | 313 | 505 | 6,565 | 21 | 21 | 8 |
| 617 | 293 | 510 | 6,630 | 22 | 22 | 21 |
| 677 | 353 | 510 | 6,630 | 16 | 16 | 7 |

## Construction and accounting

The fixed curve is `Y²=X³−X−2`. For each field, `G` is the pinned subgroup multiple of the reduction of `(2,2)` and `Q=17G`. The known scalar constructs the fixture outside the public test stage. At query `(t₁,t₂)`, the producer forms `U=Q−t₁G` and `V=Q−t₂G`, tests all 13 vectors with finite-curve group operations, and constructs a rational model only for a public zero relation. For a hit `(a,b)`, it computes `T=[b⁻¹]U`, centers its coordinates `(x,y)`, and sets `B=y²−x³+x`. On `E_B/ℚ`, the points `[b](x,y)` and `[−a](x,y)` satisfy the rational relation and reduce to `U,V`.

The construction stage performed 142 modular inverses, 142 public scalar multiplications, 142 rational curve constructions, 284 rational scalar multiplications, 142 rational relation tests, 284 reduction checks, and 142 scalar replays. These are stage-operation counts. The deterministic query census does not estimate a random-input rate or a wall-time speedup.

The pinned Lean proof in `../xedni-vector-dependent-rank-one-lift-20261115/formal/VectorDependentRankOneLift.lean` proves the public-group rank-one preimage equivalence, the Bézout inverse on a `q`-torsion group, the rational rank-one relation, and the fixed finite model's ellipticity at every prime not dividing `1664`. Every prime in this larger panel meets that condition. Its exact source hash is frozen in `protocol.json`. The producer and independent Sage audit each checked finite-curve and rational-curve nonsingularity, point reductions, the group relation, and scalar replay. The formal good-reduction point map remains the next proof bridge.

## Independent replay and amendment

The independent checked-Sage audit regenerated all 4,096 SHA-256 scheduled pairs, used the scalar equation to identify every public relation, checked that equation against finite-curve group arithmetic, and reconstructed every saved rational point and reduction. It passed with empty stderr. The initial audit exited on a sparse-count reporting error in the `p=421` row: zero filtered queries omitted `filtered_queries` from the producer's count map. Its empty output and traceback are retained as `audit-v1.json` and `audit-v1.stderr`. `audit-amendment.json` pins that failure, the unchanged producer result, and the v2 audit source, which reads a missing count as zero. No query, vector, event, or mathematical check changed in the amendment.

Reproduce from the repository root with `./sage --runtime-info`, `./sage -python experiments/xedni-public-first-large-holdout-20261115/run_sage.py`, `./sage -python experiments/xedni-public-first-large-holdout-20261115/audit_sage_v2.py`, and `python3 experiments/xedni-public-first-large-holdout-20261115/verify.py`. `SEAL.sha256` binds the protocol, both audit attempts, raw events, source, results, runtime receipt, and this report.
