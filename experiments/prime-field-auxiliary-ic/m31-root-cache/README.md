# M31 reflected point-list construction

At p = 2³¹−1 the candidate root v^(2²⁹) squares to v precisely when v has a square root, including zero. For f(x) = x³+2x+14 one also has f(−x) = 28−f(x). Root.lean checks both statements with Mathlib.

Run panel.gp with PARI/GP. For each of 1536 distinct seeded auxiliary fibers the script verifies full equality of three selected point lists, including order and the smaller canonical ordinate. Arm 0 scores both lists using the quadratic character and calls ellordinate for the selected list. Arm 1 builds both point lists with the exponent-and-check method before choosing. Arm 2 also obtains the second cubic value by subtraction. Coordinate generation and equality checks precede timing. Each of the 24 blocks contains 64 fibers, with 12 repetitions per arm. All six orders occur four times. The raw CSV has columns block, position, arm, elapsed milliseconds.

On one shared Apple M4 Pro with PARI/GP 2.17.3, aggregate times for arms 0, 1 and 2 were 997, 1786 and 1466 ms. Arm 0 was faster than both others in all 24 blocks. The median paired arm-0/arm-2 time ratio was 0.667. This measures the GP implementations, including eager construction and interpreter overhead. The interval covers selection and point construction with coordinates supplied. These observations provide no timing for compiled field kernels or full collection.
