# Blockwise source norm covers the constructed N131 two-pair panel

**Thirty-three exact target-conditioned block GCDs covered all 132,045
valid W20 second codes and retained the independently verified
constructed pair `(3,16722)`.** The constructed row completed in
**410.315 seconds** of target-dependent worker time, with one worker
and 258,621,440 B maximum worker RSS. The complete two-row attempt
reached its 600-second parent cap after 20 of 33 public blocks;
those completed public blocks were degree zero. A separate
public-only 600-second run completed six blocks and also capped.
Both public attempts are `BOUNDED_UNKNOWN` for the unvisited source.

## Exact partition and frozen inputs

The field, curve, 132,045-code source, seed, rotations, constructed
two-pair point and paired public raw point are the exact inputs in
[`coefficients.tsv`](coefficients.tsv) and the [source support](../n131_w20_sevenpair_gate_20261010/support_w20.tsv).
The public raw point is a two-pair residual control, distinct from the
full frozen challenge point in `fresh_target_public.json`.

The worker builds a reusable degree-132,045 first-product vanisher.
It partitions the ordered valid second codes into 32 blocks of 4,096
and a final block of 973. For each target point and block it forms
the product of the block's exact quartic resultants, computes its
GCD with the first-product vanisher, localizes roots to source codes,
and checks the corresponding quartics. This detects all valid
two-code resultant zeros if all 33 blocks complete. The
[Lean proof map](PROOF_MAP.md) covers the exact block-union implication
and the source-specific computational bridge. `candidate_id` is null.

| Frozen run | Completed constructed blocks | Constructed result | Completed public blocks | Parent wall | Sampled combined peak RSS | Status |
| --- | ---: | --- | ---: | ---: | ---: | --- |
| 4,096-code gate, blocks of 1,024 | 4/4 | `(3,16722)` | 4/4, all degree zero | 6.893 s | 57,294,848 B | complete |
| Full source, both rows | **33/33** | `(3,16722)` | 20/33, degree zero on visited blocks | 600.036 s | 293,142,528 B | `BOUNDED_UNKNOWN` for public row |
| Full source, public only | — | — | 6/33, degree zero on visited blocks | 600.256 s | 176,013,312 B | `BOUNDED_UNKNOWN` |

The two full-source runs used the same exact source and 4,096-code
block size, each with one worker, 600 seconds, and 4 GiB. The first
run completed the positive row after 33 block markers: 32 full blocks
plus one 973-code block, with one GCD-degree-one hit in block index 1
and degree-zero GCDs elsewhere. The positive row's phase totals were
0.472 s quartic construction, 13.101 s balanced products, and
396.662 s block GCDs plus localization. Its reusable source
vanisher took 6.921 s. The intact parent monitor recorded
`WALL_CAP` during public block 20 after 20 complete degree-zero
blocks. The second public-only run had much slower observed block
times, 45.1–136.9 seconds for its six completed blocks, and an
intact `WALL_CAP` receipt. These are ordinary-host stage measurements,
not an isolated same-point IC/rho comparison.

The 4,096-code block gate matched the [single dense NTL
norm](../n131_w20_ntl_global_norm_20261018/RESULT.md) and an
independent exhaustive native scan of all 4,096² code pairs per
point. [`verify.py`](verify.py) checks source, library, binary and
protocol hashes; block ordering and coverage; exact hit location;
the completed row; the two partial public statuses; and the Lean
proof log. The first complete two-row full-source attempt and the
separate public retry remain separate frozen receipts.

## Consequence for the active relation search

This method replaces a dense norm that capped before one target row
with exact full-source coverage on the constructed two-pair point.
At **410.315 seconds per completed residual row** in this run, a
serial application to many target-derived residuals cannot meet the
one-worker 600-second ordinary-relation gate. The public two-pair
residual itself remains partially classified. The next algorithmic
change must share GCD work across residuals or reject larger
target-conditioned partial-sum families before calling this oracle.
The frozen full challenge point still needs an independently replayed
ordinary factor-base relation before rank, factor logs and the
matched single-target rho comparison can proceed.
