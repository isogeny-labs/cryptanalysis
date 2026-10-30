# A degree-13 source-prefix rank gate for p68437

The support-five Hecke trace rows complete the 40-column rational relation matrix after 24 priority-ordered sources or 28 ascending sources when added to the frozen support-four rows. With the separately enumerated direct support-five rows already present, the first complete prefix is 20 priority-ordered sources or 16 ascending sources. These are exact first-hit statements for the two frozen orders and row families.

## Instance and method

The field is `F_68437`; the elliptic curve has order 68670, and the recorded largest prime subgroup factor is 109. The class has 40 points. The support-four baseline has 416 rows and rational rank 34. Direct support-five adds 196 verified rows and raises that rank to 39. The degree-13 support-five census contains 87 verified trace rows over all 40 sources. Each source fiber and its class trace were freshly lifted under the checked repository Sage launcher using the pinned `H.build([13])` function artifact. The source order, factorization pattern, relation conventions, source SHA-256 values and artifact identity were frozen in `inputs.json` before either replay.

At each visited prefix, the runner rebuilt the signed pair/triple index for five distinct sources, checked every candidate as an elliptic-curve group relation, and compared the entire candidate set with the independently audited full census. The exact-arithmetic auditor recomputed rational and modulo-109 ranks from the frozen relation rows. The stop rule was the first rational rank 40 for **both** baselines, or 40 sources.

| Source order | Baseline | Previous prefix: rational rank | First rank-40 prefix | Modulo-109 rank there |
| --- | --- | ---: | ---: | ---: |
| Ascending | Support-four | 27 sources: 38 | 28 sources | 39 |
| Ascending | Support-four plus direct support-five | 15 sources: 39 | 16 sources | 39 |
| Priority | Support-four | 23 sources: 37 | 24 sources | 39 |
| Priority | Support-four plus direct support-five | 19 sources: 39 | 20 sources | 39 |

The priority order saves four lifted sources for the support-four baseline. The ascending order reaches the direct-row-assisted gate four sources earlier. Thus the earlier priority ordering is not uniformly best once the row family changes. The modular rank remains 39 at every first rational-rank-40 gate, so the rational completion and subgroup-log linear system remain distinct outcomes.

## Replay and resource record

| Order | Visited sources | Candidate rows at stop | Fiber replay | Repeated index builds | Rank calculations | Total measured run | Peak RSS |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Ascending | 28 | 13 | 1.439 s | 1.765 s | 0.568 s | 3.937 s | 306,905,088 bytes |
| Priority | 24 | 9 | 0.920 s | 0.923 s | 0.407 s | 2.403 s | 299,958,272 bytes |

Times are local exploratory diagnostics, with repeated full-prefix indexing charged to each order. They are not a paired Tier 0 or Tier 1 performance comparison. The run files retain every visited prefix, including zero-yield prefixes, exact ranks, trial counts and component times. `candidate_id` and `target_online_ms` are `null`, because this experiment studies relation rank preparation and contains no frozen single-target IC pipeline. The `./sage --runtime-info` receipt was recorded before the measured runs.

The independent audit reports `PASS` for all 52 visited prefixes. Its input hashes are the pinned parent receipts, and it validates both first-hit counts and each rational/modulo-109 rank. Four Lean modules check integer annihilating vectors at the immediately preceding prefixes and invertible 40-by-40 minors modulo 11 at the first-hit prefixes. `lake build` completed successfully with no `sorry`, `admit`, `sorryAx`, or custom axioms. See `PROOF_MAP.md` for the exact formalization boundary.

## Next experiment

The two row families favor different source orders. A prospective order policy should therefore be frozen from source-only features and evaluated on a new field/curve instance before lifting its degree-13 fibers. A separate experiment must supply the missing modulo-109 rank and complete factor-base-log and single-target recovery stages before any online IC comparison.
