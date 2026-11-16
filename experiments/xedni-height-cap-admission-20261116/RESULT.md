# Fixed-height admission of common-preimage witnesses

At a 128-bit full-witness cap, the centered common-preimage lift admits 25 of the 127 frozen public-relation events; the complete 27-candidate shift search admits 55. The additional 30 events have a matching rational witness within the cap only after a nonzero integral shift. All 4,293 candidate attempts and all nine frozen caps are accounted for. The 32 public nonrelation controls remain nonadmitted at every cap because their rational second points reduce away from the specified `V`.

## Frozen cap and admission rule

The [protocol](protocol.json) pins the parent [candidate rows](../xedni-lift-height-search-20261116/rows.jsonl), [source relation and control events](../xedni-common-preimage-lift-20261116/lifts.jsonl), and full [checked-Sage candidate audit](../xedni-lift-height-search-20261116/audit-sage.json) by SHA-256. It freezes caps at `32,64,96,128,160,192,256,384,512` bits before this pass. The full-witness score is the maximum numerator or denominator bit length among `A,B,Px,Py,Rx,Ry`; integer denominators count as 1. The source panel contains 127 public relations, 32 preselected nonrelation controls, and 27 integral variants per event.

A positive event is admitted at cap `H` when at least one variant scores at most `H` and both rational points reduce to its specified `U,V`. Baseline admission uses only the `(0,0,0)` variant. A control may have small rational coordinates and an exact rational relation between its constructed points, but its second reduction differs from the specified `V`; such a row is counted as a bounded mismatch rather than an admission.

| Cap (bits) | Positive baseline / 127 | Positive any shift / 127 | Added by shift | Positive bounded attempts / 3,429 | Bounded control mismatch events / 32 |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 32 | 8 | 11 | 3 | 75 | 8 |
| 64 | 11 | 18 | 7 | 281 | 10 |
| 96 | 13 | 31 | 18 | 304 | 12 |
| 128 | 25 | 55 | 30 | 409 | 14 |
| 160 | 41 | 70 | 29 | 608 | 18 |
| 192 | 59 | 88 | 29 | 854 | 21 |
| 256 | 82 | 106 | 24 | 1,539 | 26 |
| 384 | 122 | 127 | 5 | 2,691 | 32 |
| 512 | 127 | 127 | 0 | 3,410 | 32 |

There are 3,429 positive candidate attempts and 864 control candidate attempts. At the 128-bit cap, another 228 control attempts fit the numerical cap but none matches the required second public point. [events.jsonl](events.jsonl) retains each event's centered score, minimum score, and counts under every cap. [result.json](result.json) preserves all aggregate counts and hashes.

The [analysis](analyze.py) evaluates the exact rational bit lengths and specified point reductions on every pinned row. An [independent verifier](verify.py) parses canonical integer and rational strings directly, recomputes all nine cap tables and per-event admissions, and checks monotonic candidate eligibility; [verification.json](verification.json) records `PASS`. The parent checked-Sage audit establishes each archived curve equation, group relation, and finite reduction. The parent [Lean invariants](../xedni-lift-height-search-20261116/formal/HeightSearchInvariant.lean) establish the shifted coefficient reduction and common-vector group relation used here.

These counts are deterministic for the frozen fields, target law, selected coefficient family, and 27-lift grid. The cap applies to the constructed witness representation and charges all 27 variants per event; it does not measure public-relation search or single-target online time. A next experiment can freeze a larger prime and subgroup panel, sample new targets independently of this grid, and measure both relation discovery and height-capped lift admission under one resource envelope.
