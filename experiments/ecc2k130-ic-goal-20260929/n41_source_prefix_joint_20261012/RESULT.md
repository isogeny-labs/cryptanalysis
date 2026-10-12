# Source-prefix families yield a sixth independent N41 public relation and an exact N131 join gate

## Contribution

An exhaustive target-conditioned group join over frozen N41 source-mask prefix families found a new **eight-column relation** on the saved public point. Independent checked Sage reconstructed its eight diagonal source points, verified the raw and cofactor-four public sums, checked all three nonexceptional reciprocal S3 links, and built its folded relation row. Together with the preceding four rows and the separately discovered bucket row, an exclusive-column certificate raises the verified relation-matrix rank from **five to six**. Five other prefix families were exhaustively searched and had no relation to the selected raw target preimage.

The same 13 prefix families were given to the compact exact N41 XCNF with their remaining mask bits and all pair outputs free. **Every one-worker SAT query reached its 10-second parent cap as `BOUNDED_UNKNOWN`**, including the positive family with all eight masks fixed. The exhaustive join therefore supplies actual relation/miss labels that the tested SAT search did not resolve at that cap. The corresponding N131 literal two-pair hash remains far outside 4 GiB: for the transferred `d3_random3` prefix pattern, exact four-column counting gives **1,158,343,005,909,067,680** left entries, or **144,792,875,738,633,460 bytes** even at one bit per entry. This is a component study with `candidate_id: null`.

## Exact instance and frozen input

The N41 curve is `EC1N41Ckb1h7d5e80d3c4d0` over `GF(2)[t]/(t^41+t³+1)`, with `y²+xy=x³+1`, subgroup order `549756390943`, cofactor four, and frozen public point `(920359962848,755404565011)`. The query fixes raw preimage index one, `(946309826754,403262551014)`. Eight diagonal W8 source masks occupy four signed pair slots at Frobenius rotations `(0,7,14,21)` and must have distinct folded columns. The audited source contains **30,952 signed unordered pair states per slot**. The frozen [source formula](../n131_w18_allseed_fourpair_20261012/RESULT.md) has 14,803 variables, 35,804 clauses, and 2,892 native-XOR rows before prefix units.

The [panel](panel.json) was fixed before any query: positive controls and three independent fixed-seed source-valid families at each high-bit prefix depth 2, 3, and 4, plus the fully fixed positive masks. Every random family has a matching of eight distinct folded columns, so source-column impossibility is not a shortcut. A depth-`d` case fixes exactly `8d` high source-mask bits; all lower bits, pair reciprocals, intermediate reciprocals, and target-conditioned S3 constraints remain free. The [SAT protocol](protocol.json) binds every augmented XCNF, public point, source, solver, one worker, 8-second solver flag, 10-second parent cap, and 4-GiB RSS cap. The [SAT summary](summary.json) preserves all 13 censored rows and raw logs.

| Prefix depth | SAT families | SAT result | Exhaustive raw-target join | Source bits still free |
| ---: | ---: | --- | --- | ---: |
| 2 | 4 | 4 `BOUNDED_UNKNOWN` | Not run | 48 |
| 3 | 4 | 4 `BOUNDED_UNKNOWN` | 2 verified hits, 2 exact misses | 40 |
| 4 | 4 | 4 `BOUNDED_UNKNOWN` | 1 verified hit, 3 exact misses | 32 |
| 8 | 1 | `BOUNDED_UNKNOWN` | Constructed positive control already audited | 0 |

The 13 SAT parent intervals sum to **130.759 s**, with 98,123,776 B maximum sampled combined RSS. Each row was capped independently; the sum is a panel diagnostic, not a one-target online interval. The [terminal verifier](terminal_verification.json) checks every formula's original rows, exact unit literals, frozen hashes, raw terminal status, restart count, and cap. A timeout or `INDETERMINATE` terminal is retained as `BOUNDED_UNKNOWN`.

## Exact family labels and rank

The [join protocol](join_protocol.json) froze a separate native group enumerator, its binary, the audited source table, eight selected depth-3/4 families, one worker, 30-second per-case cap, and 4-GiB RSS limit. For each family, the enumerator hashes **every** admissible slot-0/slot-1 pair sum, probes **every** admissible slot-2/slot-3 pair sum against raw preimage one, and checks all eight columns before accepting a hit. An `EXHAUSTED` terminal is an exact miss for that declared source family and raw preimage; it is not an absence claim about the complete factor base or the other raw preimages. The eight parent intervals sum to **38.796 s**, and the maximum sampled combined RSS is 87,425,024 B. Local wall intervals are exploratory without a host-isolation receipt.

| Family | Exhaustive result | Parent wall | Checked-Sage rank after insertion with four earlier rows |
| --- | --- | ---: | ---: |
| `d3_positive` | Relation | 9.355 s | 4 → 4 |
| `d3_random1`, `d3_random2` | Exact miss in both | 9.243 s, 9.928 s | — |
| `d3_random3` | **New relation** | **5.050 s** | **4 → 5** |
| `d4_positive` | Relation | 0.870 s | 5 → 5 |
| `d4_random1`–`d4_random3` | Exact miss in all three | 1.789 s, 0.908 s, 1.652 s | — |

The [independent checked-Sage audit](sage_audit_result.json) reconstructed all three hits from rational source points and signed Frobenius transports, verified the exact group sums and eight distinct folded columns, and formed their subgroup relation rows. Its [S3 chart audit](chart_audit_result.json) checked nonidentity/nonzero-`x` pair and intermediate sums and all three reciprocal identities, so the new hit lies inside the tested Boolean chart. The [combined modular rank](rank_union_result.json) is **six** after inserting the earlier [bucket relation](../n131_w18_bucketed_public_20261012/RESULT.md) and these hits. The [pivot certificate](pivot_certificate.json) extracts six columns `(27,18,7,15,87,46)` that form a diagonal six-by-six minor with diagonal entries `(500675087208,148692722092,49081303735,513703398366,369491428954,36052992577)` modulo the subgroup order. Every diagonal entry is coprime to that modulus, so any linear combination vanishing at these columns has all six coefficients zero.

## N131 transfer and next method

The [source-count replay](analysis.json) counts the signed ordered pair states in each N41 and N131 prefix domain. A separate [15-partition inclusion-exclusion calculation](memory_projection_result.json) counts literal two-pair left entries with all four folded columns distinct; its N41 counts match every exhaustive join's observed `LEFT_DONE` entry count. For the `d3_random3` N131 transfer, the one-bit-per-entry minimum is **33,712,218 times the 4-GiB cap**. For a depth-2 positive-pattern family it is **1,182,236,519,599,054,920 bytes**. These are literal-table memory gates, including neither hash overhead nor witness indices. The N131 compact Boolean four-pair circuit has a different representation and fits the construction cap; this calculation does not bound every possible symbolic method.

Let `w_j(c)` count allowed source masks in role `j` with folded column `c`. The number of ordered four-mask choices with distinct columns is exactly

`Σ_{π partition of {0,1,2,3}} μ(π) ∏_{B∈π} (Σ_c ∏_{j∈B} w_j(c))`, where `μ(π)=∏_{B∈π} (−1)^(|B|−1)(|B|−1)!`.

Multiplication by 16 gives four independent source signs; an orientation quotient of two applies for each equal-prefix pair slot because the source table stores each unordered edge once. The N41 native left-list counts independently check the resulting integers.

The next algorithm must compute a target-conditioned constraint on **compact source-mask or pair-product families** without expanding these enormous two-pair tables. The cheapest promotion test is an unpinned N41 public solve where the new constraint rejects whole families while at least two pair outputs remain free, followed by a frozen N131 construction and full 600-second/4-GiB work projection. The verified rank-six row strengthens the positive and negative controls for that test; it does not replace the required ordinary N131 relation, factor-log stages, or unseen single-target online comparison.
