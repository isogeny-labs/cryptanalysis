# Seven charts decode all 284 recorded N41 final-pair positives

The exact 41-by-8 binary map of the target-conditioned last-link
resultant admits a seven-chart decoder on the frozen set of 284
source-positive intermediate reciprocals. Each chart uses eight output
coordinates. Rank-eight elimination recovers the unique source code;
checking the remaining coordinates preserves the full equation.

The frozen one-worker search examined 51 canonical pivot charts and
4,096 seeded coordinate subsets, 4,147 distinct charts in total. Its
greedy cover, followed by redundancy deletion, selected seven charts.
Their successive new-row gains were `110, 72, 45, 29, 18, 8, 2`;
the best single chart covered 110 rows. The full ordered coordinates
are in `result.json`.

| Panel | Rows | Selected-chart successes | Full-pivot fallback | Code replay |
| --- | ---: | ---: | ---: | --- |
| Target-translated source positives | 284 | 284 | 0 | 284 exact |
| Fixed field sample | 1,024 | 955 | 69 | agrees with prior image decisions |
| Fixed reachable four-pair sample | 256 | 223 | 33 | agrees with prior image decisions |

The screen completed in **62.135 s** under its frozen 120 s and 4 GiB
limits, with self peak RSS **25,362,432 bytes**. An independent replay
through the repository's checked Sage launcher agreed on all 1,564
rows, selected charts, and fallback counts in **22.319 s** of Sage
arithmetic, with self peak RSS **174,243,840 bytes**. These are component
timings on the current non-isolated host. The primary one-target IC
online interval and same-point rho comparison have not been measured
for this chart component; its `candidate_id` remains `null`.

`python3 -B verify.py` checks source hashes, frozen limits, phase totals,
all positive chart ranks, full equations, panel counts, and the Sage
audit receipt. `lean PivotChart.lean` checks the structural decoder
theorems. The method's next useful test is an exact guarded circuit
extension of the full N41 target-coupled formula: a field-formula root
decoder may avoid selecting and testing several chart matrices at solve
time while retaining a fallback for exceptional coefficients.
