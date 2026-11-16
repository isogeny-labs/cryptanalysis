# Precommitted height selection for two-image rational lifts

Minimum full-model-height selection reduced the median model score from 26 to 23 bits on 512 fresh public queries. It improved 397 queries relative to the centered candidate, with a median paired reduction of 2 bits. The selected models passed all 512 rational group-law controls. Across 6,656 predeclared coefficient tests, 22 public relations occurred and none held on the selected rational lifts. This tests whether smaller rational models help the two-image lift retain public relations under a rule fixed before the coefficient tests.

## Frozen construction and accounting

The immutable [protocol](protocol.json) selects eight prime fields from the parent registry, four SHA-256-derived targets per field (`xedni-height-selected-v1|p|j`), and 16 ordered nonidentity two-image queries per target. It fixes the 13 coefficient vectors by the parent protocol digest. For each of 511 distinct-x queries, the producer centers both finite points, tries every shift in `{-1,0,1}^4` (81 candidates), interpolates the rational curve, and chooses the valid candidate with the smallest maximum numerator/denominator bit length among `A,B,x1,y1,x2,y2`. Lexicographic shift order breaks ties. One equal-x opposite-point query uses the frozen exceptional construction. The curve and lifted points are selected before any coefficient vector is evaluated.

| Recorded stage | Result |
| --- | ---: |
| Distinct-x / equal-x queries | 511 / 1 |
| Candidate constructions | 41,392 |
| Candidate pass / failure | 41,392 / 0 |
| Selected rational curves | 512 |
| Rational `P + (-P) = O` controls | 512 / 512 pass |
| Public coefficient relations / tests | 22 / 6,656 |
| Rational relations among the same tests | 0 / 6,656 |
| Selected model score, median (range) | 23 (13–30) bits |
| Centered model score, median (range) | 26 (13–32) bits |
| Queries improved / median paired score reduction | 397 / 2 bits |

The per-field public-hit counts for `p=313,421,431,547,571,593,617,677` are respectively `1,3,1,6,0,3,6,2`; the rational-hit count is zero in every field. Every candidate, selected query, and vector test is retained in the compressed ledgers identified by [run-result.json](run-result.json). The [independent audit](audit.py) reconstructs the subgroup generators and fresh targets, all candidate curves and scores, the selection decision, the rational controls, and both finite-field and rational group-law outcomes using separate pure-Python arithmetic. Its [receipt](audit.json) is `PASS`.

The initial producer invocation stopped before a completed ledger because Sage rationals expose `denominator` as a method; its [stderr](run-first.stderr) is retained. The producer then handles both callable Sage and property-style rational components and completed under the unchanged protocol. The checked repository Sage launcher and its [runtime receipt](sage-runtime.json) were used. The completed producer reports 5.23 seconds for its script interval on this ordinary host; this is an algorithmic diagnostic, with no paired timing comparison.

## Interpretation and next test

The selected rule demonstrably shrinks the recorded rational model representations, while the 22 public relations do not survive as the same relations on those lifts. This finite panel does not rule out other selection rules or larger lifts. The structural implication proved in the parent [two-image precommit formalization](../xedni-two-image-precommit-20261116/) ensures that a rational relation on compatible lifts reduces to a public relation; the present experiment tests the converse direction for a fixed height rule.

The next discriminating experiment is to choose lift models using a predeclared relation-independent arithmetic invariant that could preserve a selected public relation, then evaluate fresh targets with all construction and vector attempts retained. Any candidate rule needs a positive rational relation on an independently generated public hit before a cost comparison is meaningful.

Reproduce the receipt with `python3 verify.py`. To rerun the producer, save `./sage --runtime-info` and launch `./sage -python experiments/xedni-height-selected-two-image-20261116/run.py` from the repository checkout; the pure-Python audit is `python3 experiments/xedni-height-selected-two-image-20261116/audit.py`.
