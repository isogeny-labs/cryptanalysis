# Signed smooth M31 coordinate census

For each bound B, enumerate positive integers x < p with all prime factors at most B. The integer 1 is included. A separate paired comparison takes every such x up to (p−1)/2 and includes both x and −x. The signed domain contains no duplicate field coordinates. The prime-factor bound is applied before reduction; the rotation-orbit predicate is a different experiment.

The target is y²=x³+2x+14 and the auxiliary curve is y²=x³+x. Exactly one auxiliary sign in each pair lifts because the auxiliary cubic is odd, it is nonzero on these coordinates, and −1 is a nonsquare. The target values at opposite signs add to 28. The Lean file verifies the polynomial identities and the exclusion of simultaneous square values for opposite signs when −1 is nonsquare.

| B | Signed coordinates | Target lifts, all signs (%) | Target lifts, auxiliary sign (%) |
|---:|---:|---:|---:|
|7|10,518|49.47709|49.28694|
|13|55,654|49.75024|49.67478|
|23|272,780|49.92668|49.80864|
|47|1,513,390|49.96082|49.93505|
|97|6,097,648|50.03555|50.04513|
|211|22,819,080|50.00628|50.00727|

At bound 211 the selected signs contain 5,705,600 target lifts in 11,409,540 coordinates. All signs contain 11,410,972 in 22,819,080. Selecting the auxiliary sign yields 114 more lifts than half the full signed count, about 10 extra lifts per million retained coordinates. At bounds through 47, selection lowers the fraction. These finite counts measure density alone.

The canonical domain is reported separately in counts.csv, including all positive smooth representatives below p. Unique factorization makes nondecreasing prime-factor sequences an exhaustive enumeration without duplicates. All cubic evaluations were nonzero. An independent Cartesian product of prime powers and direct Python modular exponentiation reproduced the complete bound-7 row in each domain.

Compile with `c++ -O3 -std=c++17 census.cpp -o /tmp/m31-signed-smooth` and compare stdout with counts.csv. Replay Signed.lean in the Lean 4.34.1 mathlib environment with warnings treated as errors.
