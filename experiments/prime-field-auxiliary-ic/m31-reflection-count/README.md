# Can reflected coordinates share a lift label?

Consider the public curve with right-hand side f(x) = x³ + 2x + 14 over p = 2³¹ − 1. Folding the coordinate to min(x,p−x) makes a two-element bucket for every nonzero pair. A single common label per bucket incurs at least 536,844,426 errors across the field. This bound is attainable by labeling each unmixed bucket correctly and choosing either bit in each mixed bucket. It applies to a bare shared label. Storing orientation or additional information changes the representation.

## Exact count by elliptic point counting

Let χ be the quadratic character with χ(0) = 0. PARI verifies that f has no root in this field, so all lift signs are ±1. The correlation sum S = Σ χ(f(x)f(−x)) assigns +1 to agreement and −1 to disagreement. Each mixed bucket accounts for two disagreements, hence S = p − 4m where m is the number of mixed buckets.

Put u = x² and g(u) = 196 − u(u+2)². Then f(x)f(−x) = g(x²). Since u has 1+χ(u) square roots, S splits into Σχ(g(u)) + Σχ(u g(u)). In the first sum, substituting u = −v gives the monic cubic v³ − 4v² + 4v + 196. In the second, the u = 0 term vanishes. At u ≠ 0, multiplication by the square u⁻⁴ and substitution t = 1/u gives 196t³ − 4t² − 4t − 1. Extending to t = 0 requires subtracting χ(−1). Scaling the ordinate by 196 and setting v = 196t then gives the monic cubic v³ − 4v² − 784v − 38416. Both curves are nonsingular at M31.

Each cubic character sum equals the corresponding elliptic cardinality minus p+1. The two differences are 68,941 and 37,001. Since χ(−1) = −1 this gives S = 105,943. The zero coordinate is a singleton and contributes +1.

## Replay

Run `gp -fq count.gp` in this directory. It first checks the transformation by direct summation at good primes between 11 and 251. For an independent computation from square membership, compile `cc -O3 -std=c11 verify.c -o /tmp/m31-reflect` and run the binary. It visits one representative of every nonzero reflection pair. Both methods output m = 536,844,426. Replay `lake env lean experiments/prime-field-auxiliary-ic/m31-reflection-count/ReflectionErrors.lean` at the repository root. Lean verifies the per-pair error identity and the exact consequence of the measured correlation and field size. The elliptic cardinalities are computational inputs.
