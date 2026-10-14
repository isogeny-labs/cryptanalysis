# An ordinary N41 point has a verified fixed-seed seven-pair relation and rank-one row

**A 3+4 native join found a seven-pair relation on the archived independently sampled N41 public point in 29.985 seconds under one worker and 4 GiB.** Checked Sage independently rebuilt all fourteen source leaves, their seven raw pair sums, and the final public point. A second checked-Sage audit derived fourteen nonzero signed-Frobenius coefficients against the 77 folded columns and verified **one novel row from an empty relation matrix**. This supplies an ordinary-point, same-source control for the fixed-seed W8 algebraic search.

## Frozen source and point

The curve is `EC1N41Ckb1h7d5e80d3c4d0` over `GF(2)[t]/(t^41+t³+1)`, with `y²+xy=x³+1`, subgroup order `549756390943`, and cofactor four. The archived ordinary input law sampled one scalar using `random.Random(202609291700)` and supplied the resulting public point `Q=(1458168294740,1672312028033)`. Fixture generation is outside the timed join and Sage replay. The fixed W8 seed is 56; seven slots use rotations `(0,6,12,18,24,30,36)`, each with 40 permitted source edges and 160 signed pair states. The seven-window factor base has 1,120 actual usable points and 77 folded columns. The [input protocol](protocol.json) binds the earlier geometry and public-point receipts, all 1,120 exported states, the subgroup raw preimage, and 128 independent group-addition checks before search. The checked [Sage runtime receipt](sage_runtime_info.json) was saved first.

| Stage | Frozen result |
| --- | --- |
| Native 3+4 join, one worker | 3,750,144 indexed valid left triples; first accepted hit after 231,031 right probes |
| Parent wall / sampled combined peak RSS | 29.985 s / 236,486,656 bytes; 180 s / 4 GiB caps |
| Hit state IDs | `(97,151,42,0,14,109,51)` |
| Independent checked-Sage group replay | Exact raw sum `(1970584690684,115750356512)` and `[4]` projection to `Q`; fourteen distinct folded columns |
| Independent signed-Frobenius row audit | Fourteen nonzero entries, row sum `Q`, rank one from empty matrix |
| Ordinary-point functional-root SAT control | 30,537 variables, 67,329 clauses, 8,440 native XOR rows; known relation satisfies every row |
| Unpinned CryptoMiniSat search, same point | `BOUNDED_UNKNOWN` at 185.391 s parent cap, sampled combined peak 82,444,288 bytes, no terminal status |

The native [query receipt](query_result.json) and raw stdout record the exact first hit and probe count. The [Sage group audit](audit_result.json) reconstructs each leaf from the frozen field polynomial and source masks. The [row audit](row_result.json) derives the Frobenius eigenvalue modulo the subgroup order, matches each observed leaf to one canonical folded-column representative, and checks the entire linear relation on the curve. [PROOF_MAP.md](PROOF_MAP.md) records the finite certificate and its curve-specific Lean formalization boundary. The [functional-root build](build_result.json) uses the same frozen source and this public target, leaving all seven source codes and root choices free in the formula. Its witness assignment is a correctness check; the independent [SAT run](sat_result.json) records the bounded ordinary search. Both local CPU wall times are algorithmic diagnostics on an unisolated host. The stage has `candidate_id: null` because factor logs, target scalar recovery, and a matched rho comparison are not supplied by this source control.

The first plain-Python input-preparation attempt failed at `psutil` import before any search; [prepare_failure.json](prepare_failure.json) retains that status. The corrected preparation and both group audits used `/Volumes/SSD990/cryptanalysis/sage -python`. [verify.py](verify.py) checks source hashes, frozen caps, raw outputs, group and row receipts, formula satisfaction, and the SAT terminal classification.

## Transfer and next algorithm test

The [exact W20 projection](projection_result.json) has `528180^3 = 147348546687432000` unfiltered left triples for a literal N131 3+4 join. Even one bit per enumerated entry is 18,418,568,335,929,000 bytes; these are representation counts for the literal unfiltered method, with source collisions and column restrictions requiring separate treatment. The native join therefore serves as an ordinary-point witness oracle and coverage control for the N41 source, while the N131 route requires an **implicit target-conditioned constraint on several free product families**.

The next experiment should bind this ordinary N41 point and its verified witness to a three-block product-family predicate, measure whole-family rejection before pair-state expansion, and compare its exact search work with the functional-root formula. A source-bound projection must fit one worker, 600 seconds, and 4 GiB before an ordinary N131 run. The first N131 acceptance gate is an independently replayed relation on its frozen public point, followed by useful rank, factor logs, unseen-target scalar recovery, and a matched isolated rho interval.
