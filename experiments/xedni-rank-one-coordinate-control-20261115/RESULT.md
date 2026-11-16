# Rank-one lift coordinates defeat the small-slope premise

On the fixed rational curve `E/Q: y²=x³−x−2`, checked Sage reports rank one,
trivial torsion, and generator `P=(2,2)`. For all eight larger-order fields
selected in PR #1597, the reduction of `P` generates the declared prime
subgroup after multiplying by `m∈{1,2}`. The centered lift rule sends each
sampled subgroup point `(17−t)G` to the rational point
`m·centered(17−t mod q)·P`.

The full offset law was checked at each field: `3,318` offsets total. The
largest absolute generator coordinate is `m(q−1)/2`. For two independently
sampled points and the coefficient box `[-4,4]²`, the exact maximum sum
coordinate is `K=4m(q−1)`, so the least integer slope in `K≤cL` is
`c=m(q−1)`. The frozen admission gate used `c=1`; this explicit rank-one
lift family requires `c` between 292 and 624.

| Field `p` | Subgroup `q` | `m` | Maximum single coordinate | Sum radius `K` at `L=4` | Minimum slope `c` |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 313 | 331 | 1 | 165 | 1320 | 330 |
| 421 | 439 | 1 | 219 | 1752 | 438 |
| 431 | 419 | 1 | 209 | 1672 | 418 |
| 547 | 571 | 1 | 285 | 2280 | 570 |
| 571 | 599 | 1 | 299 | 2392 | 598 |
| 593 | 313 | 2 | 312 | 2496 | 624 |
| 617 | 293 | 1 | 146 | 1168 | 292 |
| 677 | 353 | 1 | 176 | 1408 | 352 |

The rank-gap numerical premise at rank one and one torsion label is
`2c+1<L`. At the measured minimum slope it fails for every field. The Lean
theorem `XedniRankOneCoordinate.no_rank_gap_at_centered_slope` proves the
general arithmetic incompatibility: for `q≥3`, `m≥1`,
`m(q−1)≤c`, and `(4L+1)²−1<q`, the rank-gap inequality cannot hold.
Its `#print axioms` record contains only `propext`, `Classical.choice`, and
`Quot.sound`.

This control explains why a low Mordell–Weil rank alone does not supply the
bounded-coordinate hypothesis. The lift rule deliberately uses subgroup
scalar coordinates to choose rational multiples, so its cost includes the
discrete-log information it encodes. It is a structural control for the
height argument, not a candidate solver. A useful next family must produce
lifts from public point coordinates with measured construction cost and
show a substantially smaller coordinate slope.

`protocol.json` freezes the input result hash, full offset law, lift rule,
and radius. The checked Sage launcher saved `sage-runtime-info.json` before
the run and verified rank, torsion, generator, all subgroup orders, and all
3,318 reductions. `audit.py` independently implements finite-field point
addition and scalar multiplication, then replays every offset and coordinate
maximum. Both runs passed with empty stderr. `verify.py` checks their source
receipts, the pinned Lean build, and its axiom audit; `SEAL.sha256` binds the
artifacts.
