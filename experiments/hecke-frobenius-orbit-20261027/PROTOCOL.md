# D=-79 conductor-2 degree-5 orbit-trace protocol

The frozen class is the 20-point D=-79, conductor-2 record over F_83. Its archived degree-5 fibers are incomplete over F_83. Use the repository's checked Sage launcher and the pinned `X_0(11)` Hecke builder in `inputs.json` to compute the degree-6 neighbor-x polynomial at every class point for `ell=5`.

For each source, retain the complete factor-degree/multiplicity pattern over F_83 and the least splitting degree (the lcm of distinct factor degrees). Cap extension work at degree 12; preserve any larger case as `EXTENSION_CAP`. For a squarefree polynomial within the cap, lift all six roots to F_(83^d), solve the six `T_5(x^k y)` moments by Vandermonde interpolation, and check the curve equation, all moments, the modular polynomial, and the Hecke group sum. Preserve failures as explicit statuses.

Partition the six lifted points into Frobenius orbits, compute each orbit's group trace, and test whether the trace is identity or one of the 20 frozen rational class points. Build a class-only row only when *all* orbit traces pass this closure test; verify its group sum and record its rational rank contribution after the corrected degree-2 rows. Do not replace an outside-class trace by its known scalar or force a row through partial fibers.

The first output is a finite census of these 20 fixed fibers. The extension cap, source order, degree, point set, and row acceptance rule are fixed before output. Retain the checked runtime receipt, producer log, result JSON, and an independent validator.
