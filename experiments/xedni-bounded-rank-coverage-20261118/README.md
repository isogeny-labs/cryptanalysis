# Bounded coefficient coverage in a fixed-generator xedni lift

**Theorem.** Fix `r` public group elements and allow each integer coefficient in `[-H,H]`. Their bounded linear combinations reach at most `(2H+1)^r` group elements. Hence, in a finite group of order `q>(2H+1)^r`, some elements lie outside that coefficient box. A uniformly drawn group element lies in the image with probability at most `(2H+1)^r/q`. Collisions can make the image smaller. This is a coverage obstruction for **fixed generators and a fixed coefficient bound**; it does not impose a computational lower bound on algorithms that change generators, increase the bound, or use other lift constructions.

For a rank-two lift, the mathematical proof is direct. The coefficient box is the Cartesian product of two integer intervals, each of cardinality `2H+1`. The image of a function has cardinality at most its domain. If `q` exceeds the domain cardinality, the image cannot be the full group. The same argument works for `r` generators. It needs no independence assumption and applies to any finite additive group.

## Exact public subgroup experiment

The [protocol](protocol.json) fixes all 13 eligible hits in the independent fresh panel and `H=2,4,8`. Each hit has prime-order subgroup `q`, public points `U,V`, and a recorded relation `aU+bV=O` with `b` invertible modulo `q`. In the coordinate `R=b⁻¹U`, the generators are `U=bR`, `V=−aR`. The [runner](run.py) enumerates all `(u,v)∈[-H,H]²` and counts distinct residues `bu−av mod q`. Every hit and bound is retained in [the result](result.json).

| H | Box size | Exact reachable points across 13 hits | Exact reachable fraction range | Cases reaching box bound |
| ---: | ---: | ---: | ---: | ---: |
| 2 | 25 | 21–25 | 5.69%–8.53% | 11/13 |
| 4 | 81 | 41–69 | 11.16%–20.82% | 0/13 |
| 8 | 289 | 81–157 | 22.10%–45.39% | 0/13 |

The six subgroup orders are `293, 313, 331, 353, 419, 439`; each exceeds `289`. All 39 rows therefore have positive unreachable counts, and the exact enumeration verifies the theorem's inequality. These are coverage measurements in the public cyclic group. The rational lift's point-level reduction theorem is a separate geometric obligation for transporting this bound through an arbitrary proposed lift.

## Lean proof map

The pinned Lean `v4.35.0-rc4` and Mathlib revision `021c46bdd042f67b538b9f9871d556a93713a9a9` are recorded in [the toolchain](lean-toolchain), [Lake package](lakefile.toml), and [manifest](lake-manifest.json).

| Mathematical step | Lean declaration in [BoundedRankCoverage.lean](BoundedRankCoverage.lean) | Status |
| --- | --- | --- |
| Coefficient box has `(2H+1)^r` elements | `coefficientBox_card` | Checked |
| Any image has at most box cardinality | `image_card_le` | Checked |
| Larger finite group has an unreachable element | `exists_unreachable` | Checked |
| Uniform target reach probability bound | `reachable_fraction_le` | Checked |
| Explicit additive group sum satisfies bound | `group_reachable_card_le` | Checked |
| Explicit additive group sum misses an element when `q` is larger | `group_exists_unreachable` | Checked |

Run `lake build BoundedRankCoverage` in this directory; [build output](build-output.txt) records the actual build and `#print axioms` audit. The module contains no `sorry`, `admit`, `sorryAx`, custom research axiom, or unverified native evaluation. `lean4checker --fresh` is unavailable on this host. The Lean theorem is about a finite additive group and explicit bounded scalar sums. A theorem connecting every rational elliptic point to its reduction remains open in the earlier geometric bridge; the present bound does not assume that missing map.

Run `python3 run.py` to reproduce the exact modular enumeration. This script does not invoke Sage or time arithmetic, so the repository's Sage launcher requirement is not triggered.
