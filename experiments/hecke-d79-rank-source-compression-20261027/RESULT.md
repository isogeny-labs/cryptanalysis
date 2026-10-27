# Five degree-13 sources certify the p63317 Hecke rank increment

For the frozen p63317 D79 class, the 20 base rows and 220 direct candidates have rank 37 over (F_{2531}). Two Hecke candidates, catalog indices 221 and 226, raise the rank to 39 and touch only source indices `{17,18,23,33,36}`. Adding the anchored log row raises it to 40, and the compressed system reproduces all 40 logs in the pinned full-pool solution. The full 237-row Hecke pool also reaches rank 39.

| Prime | Base + direct rank | All-Hecke rank | Selected Hecke rows | Selected source IDs | Rank deficit after full pool |
| --- | ---: | ---: | --- | --- | ---: |
| 63317, (q=2531) | 37 | 39 | 221, 226 | 17, 18, 23, 33, 36 | 1, fixed by the anchor |
| 68437, (q=109) | 33 | 34 | 0 | 0, 1, 5, 31 | 6 |

The exhaustive p63317 search tested all `C(237,2)=27,966` Hecke-row pairs; 983 pairs supplied both missing rank directions. The selected pair has the smallest source union under the frozen ordering. Every candidate uses four distinct sorted source IDs, and no two candidates share the same four-source support. Thus a four-source budget can expose at most one catalog row and cannot supply a two-rank gain. Five is the minimum source count **within this frozen candidate catalog**. The p68437 search tested all 196 single rows; six raised rank by one, and the full pool remained at rank 34.

The p63317 baseline row-reduction pivots at columns 0–36. The selected rows reduce to quotient coordinates `(1620,922)` and `(2304,2320)` at columns 37–38; their determinant is `1617 mod 2531`, which is nonzero. This is a compact rank-increment certificate. The independent checked-Sage audit rebuilt both matrices, verified the selected rows as curve-group relations, confirmed both rank tables, and recovered the pinned p63317 logs from the compressed matrix and anchor.

The five selected p63317 source lifts have a recorded sum of 198,730,292 ns; the 40 source receipts sum to 1,772,592,789 ns. Selection was retrospective after the full pool had been produced, and direct-row enumeration was also already paid. These sums are component accounting, not an observed runtime reduction or a prospective source schedule. A useful next experiment is to freeze a source-selection rule using only information available before degree-13 lifts, then test it on a new prime without searching the full pool first.
