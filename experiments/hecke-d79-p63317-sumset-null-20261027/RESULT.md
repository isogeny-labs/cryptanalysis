# The p63317 class sumset is ordinary under a matched sign-orbit null

The 40 projected class logs cover 2503 of 2531 subgroup scalars with signed, distinct-index triples. In 256 frozen random controls with the same anchor, 20 sign orbits, 40 nonzero distinct logs and negation closure, the median triple coverage is 2501; 122 controls cover at least as many points as the observed base. The observed fixed `−B₀` fourth-source translate adds the remaining 28 points. That completion occurs in 198 of the 256 controls.

| Statistic | Observed class base | Matched controls |
| --- | ---: | ---: |
| Signed triple patterns per base | 79,040 | 79,040 each |
| Triple coverage | 2503 | min 2359; Q1 2489; median 2501; Q3 2511; max 2527 |
| Triple coverage upper empirical tail | — | `(1+122)/257 = 123/257` |
| Triple coverage lower empirical tail | — | `(1+143)/257 = 144/257` |
| Additional points from fixed `−B₀` translate | 28 | min 4; median 30; max 170 |
| Complete coverage after fixed translate | yes | 198/256 controls |

The frozen producer and independent audit each evaluated all 256 control rows. The audit reproduced the Python random sample stream, recomputed signed triples by a separate pair-plus-third enumeration, and matched every row and aggregate. The parent checked-Sage audit anchors the observed class logs to actual p63317 curve points. Every control draw and input hash is retained.

This comparison tests additive coverage after projecting the class points into the cyclic subgroup. It does not test whether the original Hecke construction supplies those logs or relations at comparable cost. The observed coverage and fixed-translation completion give no unusual signal under this matched additive null. The next useful test should retain the designated Hecke relation provenance and compare the cost of obtaining usable logs or rank, rather than only the final sumset geometry.
