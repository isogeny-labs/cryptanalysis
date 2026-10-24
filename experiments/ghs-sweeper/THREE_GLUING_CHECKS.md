# Fixed verification contract: cubic 3-gluing

Date: 2026-10-24. Classification: derived theorem, proof verification and
software unit tests. This is not a curve census, benchmark, natural-yield
estimate or completed DLP attack. Commit this contract, the proof and the
Rust checker before executing its new assertions.

The exact assertion is existence of a Frobenius-stable Lagrangian in the
induced six-dimensional F3 module that intersects each coordinate plane
trivially. The two accepted cases are specified in THREE_GLUING.md. A
negative answer excludes this kernel type only. An affirmative answer is
not publication novelty, an instantiated Jacobian or an evaluated map.

Fixed unit assertions:

1. Check explicit kernels for M=diag(1,2), q=2 mod 3, and for both scalar
   matrices M=I,-I, q=1 mod 3. Check rank, isotropy, Frobenius stability and
   all three coordinate intersections. Reject singular matrices and the
   wrong determinant/multiplier.
2. Independently enumerate reduced-row-echelon 3-subspaces of F3^6 in unit
   code. Check that each of the two weighted symplectic forms has exactly
   (3+1)(3^2+1)(3^3+1)=1120 Lagrangians. For every invertible 2x2 F3 matrix
   (48 matrices, determinant determines q mod 3), existence of a stable
   coordinate-transverse Lagrangian must agree with the theorem. This is
   finite-algebra verification of a fixed statement, not a sampled curve
   experiment or a statistical control.
3. Binary curve controls are fixed before checking: d=3, b=24, a=0 and
   a=1, in the existing deterministic degree-nine power basis. Here
   b=2^4+2^3, so 2 is a root of X^4+X^3+b. Expect two rational roots and
   full absolute degree nine; check by separate raw polynomial arithmetic
   and direct evaluation of all field elements. Do not infer the selected
   Jacobian twist from these two inputs.
4. At d=2, b=2, compare the polynomial-gcd root count with independent
   direct evaluation; its classification is an output, not a prespecified
   positive-family claim. At d=1, b=2, retain the module result but do not
   assert geometric indecomposability. At d=3, b=1, exclude the proper
   subfield coefficient from the geometric corollary. Reject b=0,
   coefficients outside the field, d=0 and unsupported field sizes.

The matrix certificate uses a weighted Weil pairing, with weights 1,q,q^2,
not three identical blocks when q=-1 mod 3. Passing the finite check does
not replace the proof of geometric indecomposability or arithmetic Torelli.
The source-coordinate torsion basis, target equation, obstruction character,
explicit transfer and planted-log replay remain unimplemented. All costs
and subgroup IDs remain null. No weak-curve catalogue promotion is allowed.

Run Cargo formatting, all-target Clippy and release all-target tests. Retain
failures as well as passing output under three-gluing-checks/. No empirical
campaign is authorized by this unit-test contract. The existing 355 pending
jobs and their admission under the canonical experiment-protocol workflow
are unchanged.

## Addendum: closed trace test, before its assertions

After the initial 28 tests passed, the odd-degree polynomial test was
reduced symbolically to Tr(cube_root(b))=0. A literature check identifies
the trace condition as old (Moisio, Theorem 7.3; earlier
Charpin--Helleseth--Zinoviev). Add a separate algebraic certificate: compute
the cube root, the Frobenius-four half-trace and its two division roots;
verify all identities with raw arithmetic. Use only the existing fixed
odd-degree controls (d,b)=(3,24),(1,2),(3,1). Check acceptance against the
already checked polynomial-gcd result. This adds no new curve samples or
priority claim. Commit the addendum and code before running the new test.
