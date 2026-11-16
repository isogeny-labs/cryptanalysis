# Full-witness accounting preserves the height result

Including the rational curve coefficients alongside both rational points leaves **all 159 maximum-bit winners unchanged** in the frozen 27-candidate height panel. For the 127 public-relation events, the median full-witness maximum remains 214 bits at the centered baseline and 142 bits after selection, with a 53-bit median paired reduction. A second metric that sums every numerator and denominator bit length has median 860 bits at baseline and 609 bits under its own selected winner, with a 192-bit median paired reduction. Its selected shift differs from the point-score winner for four positive events and six controls.

## Exact accounting boundary

The [protocol](protocol.json) pins the parent [candidate rows](../xedni-lift-height-search-20261116/rows.jsonl), [point-score winners](../xedni-lift-height-search-20261116/winners.jsonl), and [checked-Sage audit](../xedni-lift-height-search-20261116/audit-sage.json) by SHA-256. The latter independently replayed every parent curve, group relation, reduction, and coordinate before this accounting pass. This retrospective pass keeps the same 159 events, 27 candidate attempts each, source order, and both control classes.

For each candidate, the six rational components are `A,B,Px,Py,Rx,Ry`. An integer coefficient has denominator 1. The **full maximum** is the greatest numerator or denominator bit length among those six components. The **full sum** adds their twelve numerator and denominator bit lengths. Both ignore sign bits and record exact arithmetic sizes rather than serialized bytes or runtime. Ties use the frozen lexicographic shift order.

| Positive public-relation events (127) | Centered baseline | Point-score selection | Full-metric optimum |
| --- | ---: | ---: | ---: |
| Median full maximum | 214 bits | 142 bits | 142 bits |
| Median full sum | 860 bits | 609 bits | 609 bits |
| Maximum full maximum | 405 bits | 330 bits | 330 bits |
| Maximum full sum | 2,244 bits | 1,857 bits | 1,857 bits |

The median **paired** reductions under the appropriate full-metric optima are 53 bits for the maximum and 192 bits for the sum. All 159 full-maximum winners coincide with the original point-score winners. The summed-bit optimum differs for 4 of 127 positive events and 6 of 32 nonrelation controls. These equalities concern the stated finite candidate set; they do not assume that the earlier point-only score measures every representation cost.

The [analysis](analyze.py) records per-event baseline, point-score winner, full-maximum winner, and full-sum winner in [events.jsonl](events.jsonl). [result.json](result.json) preserves the counts and complete group summaries. An [independent verifier](verify.py) parses canonical integer and rational strings directly, checks every one of the 4,293 source candidates and all 159 event selections, and recomputes the summaries; [verification.json](verification.json) records `PASS`.

The mathematical curve and relation invariants are the three checked Lean declarations in the parent [HeightSearchInvariant.lean](../xedni-lift-height-search-20261116/formal/HeightSearchInvariant.lean); this pass changes the representation metric and selection arithmetic while preserving those hypotheses. A next measurement can charge encoded storage, curve construction, and relation-search operations together under one frozen height cap and target law.
