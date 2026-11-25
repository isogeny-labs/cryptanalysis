# Exact W33 collision geometry and bounded N131 public query

**The W33 source has 8,331 exact source-valid cross-code folded-orbit
collisions, and the resulting all-aligned five-pair circuit passes a
constructed N131 group replay.** The one-worker ordinary query on the
frozen public point reached `BOUNDED_UNKNOWN` at its 600-second wall cap.
The experiment tests source widening after the W29 resultant and norm
circuits remained bounded. It retains `candidate_id: null`.

## Geometry and controls

The field is `GF(2)[u]/(u^131+u^13+u²+u+1)`, the curve is
`y²+xy=x³+1`, and the prime subgroup order is
`680564733841876926932320129493409985129`. W33 has 32 canonical
source-code bits after removing the highest bit of the fixed seed mask
`898618`; the paired parameter is `a+s`, with `s=1797236`. All five
pair outputs use rotation zero and strict code order. The exact
source-validity and folded-column checks follow the same laws as the W29
source; the original W29 constructed relation is a valid W33 subset.

The [affine audit](collision_result.json) solved all 524 Frobenius-power
and endpoint-choice systems, then the [source filter](filter_result.json)
enumerated all 132,492 nonzero-distance code-pair occurrences. It retained
16,662 valid occurrences, or 8,331 unordered collision pairs. An
independent [Sage replay](verification_result.json) recomputed all 524
ranks and feasibility decisions and the complete valid collision-pair set.
The [proof map](PROOF_MAP.md) identifies the reused Lean implication and
the concrete finite-field certificate boundary.

The previously archived [N41 W11 ordinary relation](../n41_n131_all_aligned_20261019/n41_audit_result.json)
is an unpinned, independently group-replayed control for this fixed-seed
five-pair source family. The W33 N131 constructed circuit satisfied all
328,422 clauses and 41,480 native XOR rows. The independent
[group replay](control_replay.json) rebuilt the five source pairs, found
ten distinct folded orbit IDs, and summed to the constructed raw target.
The first builder invocation stopped at a leftover W29 collision-count
assertion before circuit construction; its [failure receipt](build_first_attempt_failure.json)
and v1 protocol remain beside the corrected frozen build.

## W33 source density and public query

The frozen [validity sample](sample_result.json) drew 131,072 uniform
canonical codes with replacement at each width. W29 returned 32,823
valid draws (`0.25042 ± 0.00235`, approximate 95% sampling interval),
consistent with its exact full census fraction `0.2500036`. W33 returned
33,004 valid draws (`0.25180 ± 0.00235`). Under a separate uniform
independent group-sum heuristic, using four signed pair states per valid
code, `binom(V,5)·4⁵/(4r)` gives about **4.27** unordered five-pair
witnesses at exact W29 and **4.64 million** at the W33 sample point
(sampling interval about 4.42–4.86 million). This is a search-density
prediction, not a measured relation yield; the actual W33 usable base
size and sum distribution have not been enumerated.

| Same frozen N131 public point | W29 all-aligned | W33 all-aligned |
| --- | ---: | ---: |
| Clauses / native XOR rows | 254,348 / 40,647 | 328,422 / 41,480 |
| Formula bytes | 13,825,116 | 37,835,046 |
| Exact valid collision pairs | 2,093 | 8,331 |
| Constructed assignment and group replay | passed | passed |
| Ordinary-query status | `BOUNDED_UNKNOWN` | `BOUNDED_UNKNOWN` |
| Parent query wall | 600.059 s | 600.068 s |
| Sampled peak combined RSS | 738,902,016 B | 987,906,048 B |

Both public queries used one CryptoMiniSat worker and a 4 GiB sampled RSS
stop. The W33 [build](build_result.json), [frozen query](query_protocol.json),
[query receipt](query_result.json), and [terminal audit](terminal_audit.json)
pin the point, source, solver, formula and output hashes, limits, and
observed status. The generated formula is hash-verified locally and can be
rebuilt from the committed source. The source-validity sampling and the
solver conflicts are diagnostics, not solved-time comparisons.

The earlier [W11 SAT diagnostic](../n41_w11_n131_w33_density_20261018/RESULT.md)
did not pass its ordinary-query gate; it found that S3 middle variables
remained unresolved even when all five pair outputs were fixed, whereas
direct S3 resolution on those outputs completed in milliseconds. This W33
run is an exploratory public-point test with the later native N41 relation
as a source-family control; it does not promote the W33 SAT method through
that earlier same-method gate. The next algorithmic experiment is an exact
functional S3-middle encoding or hybrid theory propagation tested first on
the unpinned N41 query, with exceptional coefficient cases retained.
