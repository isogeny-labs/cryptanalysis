# Does a target lift predict its reciprocal partner?

For the field and curves in README.md, the 268,435,456 unordered reciprocal pairs split as follows.

| Target lifts in the pair | Pairs |
| --- | ---: |
| Both | 67,097,271 |
| One | 134,219,899 |
| Neither | 67,118,286 |

Choose a coordinate uniformly among the 536,870,912 eligible coordinates. Its marginal lift rate is 49.996086%. Conditional on that coordinate lifting, its partner lifts with probability 134,194,542 / 268,414,441 = 49.995277%. Thus the reciprocal edge changes this probability by −0.000809 percentage points. In both partner states, failure is the majority outcome. For equal-cost binary prediction, seeing the partner bit therefore gives zero improvement over always predicting failure. This measures only the reciprocal edge, for this specific curve pair. It supplies no collector timing.

## Why one field scan counts each edge once

Write t = x + 1/x. For eligible x, both x and x² + 1 are nonsquares. Since xt = x² + 1, t is a nonzero square. Also x(t ± 2) = (x ± 1)², so both t ± 2 are nonsquares. Neither x = 1 nor x = −1 is eligible here, since 1 and 2 are squares. Conversely, when these three character conditions hold, (t − 2)(t + 2) is a nonzero square. The roots of X² − tX + 1 are distinct field elements with product one. The same identities show that each root x and its x² + 1 are nonsquares. This gives exactly one t for every eligible pair.

For f(x) = x³ + 2x + 14, the product f(x)f(1/x) is 14t³ + 2t² − 14t + 197. Its character is negative exactly on mixed edges. The scan counts mixed edges and checks that the product never vanishes on an eligible pair. The count of pairs with two lifts equals half the difference between the eligible lift count from census.js and the mixed count.

## Local replay

Run `node reciprocal.js` for the pair and mixed counts, and `node census.js` for the eligible lift count. Each uses a 256 MiB bitmap. Run `gp -q -f reciprocal-sample.gp </dev/null` for a seeded independent check using inversions and direct cubic evaluations. Of 100,000 draws, 25,282 were eligible and 12,772 were mixed.

With Lean 4.28.0 and matching Mathlib, run `lake env lean /absolute/path/to/Reciprocal.lean`. The proofs cover the product identity, selector identities, recovery of the reciprocal roots from the discriminant, polynomial differences, and the conditional probability bound given the census totals. The counts come from executable enumeration.
