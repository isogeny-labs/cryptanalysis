# H110 paired reference harness — canonical p²-lift defect

Status: **preregistered; independent implementation pending** (2026-11-01).

This directory freezes the independent reference role for the canonical H110
experiment in `isogeny-labs/crypto`. H110 tests whether the first formal-layer
defect of a coordinate-fixed Hensel section has uniformly polylogarithmic
scalar-polynomial degree.

Reference obligations:

1. independently implement Hensel lifts and projective arithmetic modulo p²;
2. check reduction, kernel membership, formal coordinates, and section
   linearity for all 9,096 targets;
3. independently calculate all 28 interpolation degrees;
4. reproduce 32 randomized-section/permutation controls;
5. verify coordinate-isomorphic and torsion-lift zero controls;
6. reject any speed claim unless the exact decoder and total cost gate pass.

No correctness, novelty, algorithm, or subexponential claim is made by this
preregistration.
