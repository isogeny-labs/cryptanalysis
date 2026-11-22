# M31 target lifts across auxiliary root sets

This census uses the auxiliary curve (y^2=x^3+x) and the target curve (y^2=x^3+2x+14) at (p=2147483647). The population consists of the x-coordinates of full-order points on the auxiliary curve. Each 32-root set is the x-image of a coset of its order-32 subgroup. Accounting for sign gives 16,777,216 disjoint sets.

Run `node census.js` to enumerate every field element with a 256 MiB square-residue bitmap. The full-order seed criterion requires both x and x²+1 to be nonsquares. A seed lifts on the target if x³+2x+14 is a square. Zero is included in the square table. The target cubic has no field roots here. The exhaustive count is 536,870,912 eligible coordinates, 1,073,752,646 target lifts over the whole field, and 268,414,441 coordinates meeting both conditions. The exact mean per set is 268,414,441 / 16,777,216.

Run `gp -q -f sample.gp </dev/null` for a separate point-addition check on randomly selected classes. PARI's RNG is seeded with 24117. Of 8,300 draws, 8,298 class indices were distinct and 3,589 of those had at least 17 target lifts. These are sample frequencies. The signed point representatives and index-calculus collection time are outside the census.

`Recurrences.lean` proves the field polynomial differences used by the exhaustive loop. It can be checked with Lean 4.28 in a matching Mathlib environment.
