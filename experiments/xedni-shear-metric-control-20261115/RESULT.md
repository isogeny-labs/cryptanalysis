# Exact shear control for the xedni counting bridge

The frozen integer-lattice control shows how the metric-cover bound stays fixed while a coordinate-box bound deteriorates under a change of integral basis. For `P1=(1,0)`, `P2=(0,1)`, `P3=(1,1)` in `ℤ²`, all 27 ordered coefficient triples in `[-1,1]³` produce 19 distinct sums. The relation `(1,1,-1)` is an independently checked positive control. An ambient square of 25 radius-zero centers contains every sum, so the metric count satisfies `25 < 27` for every shear.

The inverse shear coordinates are `(x-Ny,y)`. The smallest symmetric coordinate square containing the 19 distinct sums grows with `N`, while the values and ambient cover stay fixed:

| Shear `N` | Coordinate radius `K` | Coordinate-cover count `(2K+1)²` | Metric-cover count | Strict count below 27? coordinate / metric |
| ---: | ---: | ---: | ---: | --- |
| 0 | 2 | 25 | 25 | yes / yes |
| 1 | 2 | 25 | 25 | yes / yes |
| 2 | 4 | 81 | 25 | no / yes |
| 5 | 10 | 441 | 25 | no / yes |
| 10 | 20 | 1,681 | 25 | no / yes |
| 100 | 200 | 160,801 | 25 | no / yes |

The input law, instance, count boundaries, predicted control relation, and shear panel were fixed in `protocol.json` before running `run.py`. The run exhaustively enumerated the coefficient box and checked the known relation and an independently found collision. `audit.py` replayed the distinct-value set through the separate membership condition `∃c∈[-1,1]: |x-c|≤1 ∧ |y-c|≤1`; it recovered all 19 values and all six row counts. Both scripts passed. `SEAL.sha256` binds the protocol, code, raw result, audit, and this report.

This exact `ℤ²` control tests the counting mechanism formalized by the metric-cover Lean theorem in PR #1565 and the basis-conditioning example in PR #1561. The next geometric experiment is to construct a comparable finite cover from the canonical-height pairing of a selected rational elliptic-curve lift, with torsion fibers counted explicitly. A cover that remains at or above the coefficient-box count under those arithmetic inputs would falsify this route as a useful bound for that lift family.
