# Exact whole-field joint lift census at M31

For each of the 2,147,483,647 field elements x, the census records the quadratic characters of f=x³+x and g=x³+2x+14, in that order. A positive character corresponds to two ordinates. A negative character corresponds to two ordinates on the quadratic twist written in the same x-coordinate as d y²=g(x), for a fixed nonsquare d.

| Auxiliary character | Target positive | Target negative | Target zero |
|---|---:|---:|---:|
| Positive | 536,867,632 | 536,874,191 | 0 |
| Negative | 536,885,014 | 536,856,809 | 0 |
| Zero | 0 | 1 | 0 |

The nonzero-square auxiliary row gives 49.99969457% target lifts. The whole field gives 50.00050396%. The difference is about minus 8.09 target lifts per million coordinates. The unrestricted auxiliary-coordinate condition therefore provides a slight global disadvantage for target lifts. Individual translated cosets can differ from the aggregate.

The mixed character sum is −34,764. The marginal sums are 0 and 21,645. Adding p+1 to each marginal reproduces independent PARI/GP elliptic-curve counts 2,147,483,648 and 2,147,505,293. These marginal checks do not certify the mixed sum independently.

The enumerator marks the nonzero square residues using representatives 1 through (p−1)/2. It traverses every x with finite differences and verifies the cubic values and both characters by direct modular exponentiation at every 524,287th coordinate. It performs that direct check on every coordinate at p=31, 127 and 8191 first. Recurrence.lean proves the finite-difference identities over any commutative ring. The counts come from the C++ enumeration.

Reproduce with `c++ -std=c++17 -O3 census.cpp -o /tmp/m31-joint-lift-census && /tmp/m31-joint-lift-census` and compare stdout with counts.csv. The M31 table uses 256 MiB. Replay Recurrence.lean with mathlib and Lean 4.34.1. For the independent marginal check in PARI/GP, evaluate `p=2^31-1; [ellcard(ellinit([1,0],p)),ellcard(ellinit([2,14],p))]`.
