# Direct parity preserves the seven-pair N41 relation and bounds unpinned search

A direct-parity N41 W8 circuit derives each of seven fixed-seed pair selectors from its output and inverse coordinates, enforces exact permitted pair codes and all 14 distinct folded columns, and preserves the frozen public-point relation. Its complete constructed assignment passes **105,787 CNF clauses and 4,456 native XOR rows**. Independent checked Sage rebuilt all seven signed raw-point pairs, their rotated sums, the raw target, and the public cofactor-four point.

The frozen curve is `EC1N41Ckb1h7d5e80d3c4d0` over `GF(2)[t]/(t^41+t^3+1)`. The source is the existing W8 seven-rotation fixed-sum geometry at seed code 56, with 125 rational source masks, 40 permitted canonical pair codes, product-map rank seven, and rotations `(0,6,12,18,24,30,36)`. The public subgroup point is `(1654986373106,1310318707590)` and the raw target is `(2026560328086,1928332930914)`. The seven saved source pairs are a correctness control; no source code or pair-output wire was pinned in the public query.

For each unrotated pair output reciprocal `a` and inverse `b`, the circuit imposes `ab=1` and the exact fixed-seed product-image syndrome of `P(s)=(1+h²)a+h²b`. Its seven decoded selector bits are XOR functions of `a,b`. A 7-bit clause table forbids every canonical pair code outside the 40 permitted pairs; 966 cross-slot clauses forbid folded-column collisions. Six S3 links then couple all seven rotated outputs to the raw public target. The [preflight](preflight.json) checks the 125-mask rationality support against the frozen geometry and exhausts all 128 selector codes through the decoder and projector. The constructed [assignment check](control_result.json) verifies every XCNF row.

| Frozen run | Status | Parent wall | Sampled combined RSS |
| --- | --- | ---: | ---: |
| Formula construction and full assignment check | `EXIT_0` | 6.246 s | 61,980,672 B |
| One-worker unpinned public query | `BOUNDED_UNKNOWN` | 185.145 s | 58,638,336 B |
| Independent checked-Sage seven-pair replay | `EXIT_0` | 28.603 s | 285,114,368 B |

The public solver had a 180 s internal limit and a frozen 185 s parent cap with 4 GiB RSS. Its log shows **1,006 restarts** and no terminal SAT/UNSAT line; the parent ended it at the cap. The run is censored search evidence, while the constructed assignment and Sage replay establish satisfiability and the saved relation's group law. The first Sage audit incorrectly added diagonal points instead of the source's signed raw points; its frozen `EXIT_ERROR` receipt and stderr are retained. The version-two Sage audit follows the source producer's raw-point law and passes. `python3 -B verify.py` checks all four run protocols, source hashes, raw outputs, statuses, and public-point agreement.

This N41 result keeps the N131 direct-parity circuit at a component stage with `candidate_id: null`. The next change should expose more target information earlier in the seven-pair S3 topology or propagate jointly across unresolved pair outputs, then beat this same-point unpinned control with exact model replay. The 600 s N131 ordinary-relation gate remains reserved for a version that passes that control and a full source-bound work projection.
