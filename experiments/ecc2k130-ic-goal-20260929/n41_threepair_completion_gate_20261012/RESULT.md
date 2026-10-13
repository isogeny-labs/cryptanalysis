# Exact three-pair completion rejects N41 target-conditioned families

**A target-conditioned three-pair completion oracle fully rejected 22,304 public-point outer families while leaving two pair domains indexed and unresolved.** Its 1,583,568-entry exact two-pair group index represented the remaining family implicitly; each outer family scanned one free pair and looked up the required two-pair sum. In 160.067 seconds of worker query time, it tested **29,568,392** inner candidates on the frozen N41 public point. Twelve exact group-point matches all violated the ten-distinct-column rule. A constructed five-pair target passed the same frozen binary in its first family and first inner probe; independent checked Sage reconstructed its ten signed source atoms and group sum. The public search stopped at its declared cap with mathematical outcome **`BOUNDED_UNKNOWN`**.

## Source, oracle, and exact observations

The source is all 1,956 signed slot-zero W8 diagonal pair states whose two masks lie below 64, projected by four into the prime-order subgroup of `EC1N41Ckb1h7d5e80d3c4d0`. The field is `GF(2)[t]/(t^41+t^3+1)`, the curve is `y²+xy=x³+1`, the subgroup order is `549756390943`, and the frozen public point is `(920359962848,755404565011)`. The prior checked common-Frobenius transformation supplies `Q′=(1099765887764,1148205618145)`.

The worker builds an exact hash index of every unordered two-pair state with four distinct folded columns. For each outer two-pair state `A` in a fixed shuffled order, it scans source pair state `C`, computes the target-derived residual `R=Q′−A−C`, and asks whether `R` equals an indexed two-pair sum `B`. All five source pairs remain signed source states, and the final gate requires ten distinct folded columns and replays `A+C+B=Q′`. A rejected outer `A` therefore rules out its entire three-pair completion family under this exact source and index. The [query protocol](protocol.json) froze the binary and source hashes, order seed, one worker, 100,000-family and 160-second worker query limits, 180-second parent limit, and 4-GiB combined RSS ceiling before the public run.

| Frozen public query measure | Result |
| --- | ---: |
| Signed pair states / exact two-pair index entries | 1,956 / 1,583,568 |
| Outer families fully tested / indexed outer families | 22,304 / 1,583,568 |
| Inner candidates with disjoint outer columns | 29,568,392 |
| Exact group-point matches / ten-column rejects | 12 / 12 |
| Source and index preparation in worker | 7.73178 s |
| Target-conditioned worker query | 160.067 s |
| Whole parent process wall | 168.837143625 s |
| Sampled combined RSS peak | 195,985,408 B |
| Independently checked public relation rows in this run | 0 |

The native worker writes `EXHAUSTED` on any loop exit, including its time cap. Here only 22,304 of 1,583,568 indexed outer families were tested, and the elapsed worker query exceeded the 160-second limit by polling latency. The [frozen terminal audit](terminal_audit.json) therefore records `WORKER_QUERY_CAP` and `BOUNDED_UNKNOWN`; it does not interpret the producer's label as an exhaustive source result. The prior checked computation of `Q′` was outside this interval, so a complete target-dependent online total is unknown. The local wall measurements are algorithmic diagnostics without a host-isolation receipt.

## Constructed positive control

The [control fixture](fixture.json) deterministically takes the first shuffled outer two-pair family, selects three more source states with disjoint columns, and constructs their projected sum through the checked repository Sage launcher. It selects subset state IDs `(1051,1410,0,344,564)`. The same binary, bound by the [control protocol](control_protocol.json), returned these five IDs at outer family 1 and inner probe 1, with sampled combined RSS below 4 GiB and 8.971 seconds of parent wall including index setup. The [independent checked-Sage audit](control_audit_result.json) rebuilt every diagonal point from the W8 factor-base geometry, applied all ten signs and fourfold projections, verified ten distinct folded columns, checked the projected target, and checked the common-Frobenius image. This is a correctness control for the oracle, not an ordinary public-point yield measurement.

## N131 transfer test and next mechanism

The [exact W18 source census](projection.json) gives `S=34,482,792,912` signed pair states on `EC1N131Ckb1heb5f1998f20b`, with subgroup order `r=680564733841876926932320129493409985129`. A literal unordered two-pair index would have **594,531,503,488,697,323,416 entries**: even one byte per entry is about **595 exabytes**, far beyond 4 GiB. If an outer-family residual is uniform in the subgroup, at most `S³/r ≈ 6.025×10⁻⁸` of outer families have any three-pair completion, before column filtering. One expected hit then needs at least **16.60 million** tested outer families under that model. The count bounds the literal indexed implementation and uniform-residual proposal law; it does not bound a correlated target-derived generator or a compressed algebraic triple-image predicate.

The next falsifiable method change is an **implicit three-pair image test**: on the existing N41 W6 source, reproduce the positive control and reject a frozen sample of the 22,304 public negative families without storing the two-pair Cartesian index or scanning all 1,956 inner states per family. Only a source-bound implementation and its measured family rejection rate can justify an N131 public query. The active ECC2K-130 ordinary-relation, factor-log, one-target scalar, and matched-rho gates remain unchanged; this component has `candidate_id: null`.

## Formalization

[`TripleImageBound.lean`](TripleImageBound.lean) proves that deduplicating an enumerated triple-output list cannot increase its length and, under the explicit hypothesis that the source list has at most `S³` entries, its distinct image has at most `S³` entries. It builds under pinned Lean 4.34.1; [`lean_check.txt`](lean_check.txt) shows only standard `propext` and `Quot.sound` in `#print axioms`. The first two failed compilation attempts are preserved. The [proof map](PROOF_MAP.md) distinguishes that structural theorem from the concrete W18 source census, subgroup order, and conditional uniform-residual calculation.
