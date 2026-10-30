# D=-79 conductor-2 degree-13 repeated-x source protocol

The frozen source is index 19 in the 20-point D=-79, conductor-2 class over F_83. The previous degree-13 panel measured its neighbor-x factor pattern as `(1)^2(12)` and retained it as `REPEATED_X_UNLIFTED`. `inputs.json` pins that panel, the corrected degree-2 matrix, the degree-5 rows, and the Hecke builder before this lift.

Use the checked repository Sage launcher with a 600-second wall cap. Build degree-13 Hecke functions, extend to F_(83^12), and solve the fourteen `T_13(x^k y)` moments for the thirteen distinct x-roots. The unknown at the doubled x-root is the sum of two y-coordinates. Enumerate unordered pairs, with repetition allowed, from the curve lifts of that x-root. Accept only candidates satisfying the y-sum, every moment, the curve equation, every modular-polynomial root, and the complete Hecke group sum. Preserve zero or multiple candidates, and do not choose arbitrarily.

For a unique accepted neighbor multiset, partition it into Frobenius orbits with multiplicity. Compute and save each rational group trace. Insert an individual class row only if every trace is identity or one of the 20 frozen class points. Test exact-coordinate equality against the saved degree-5 and degree-13 outside trace points as a diagnostic; do not turn a match into a row without an exact cancellation certificate.

Report the rational and F_5 ranks of the previously verified matrix (expected 17) and after any new individually closed row. Save the runtime, producer status, result, and independent F_83 group/rank validation. The extension, source, acceptance rule, and cap are fixed before producer output.
