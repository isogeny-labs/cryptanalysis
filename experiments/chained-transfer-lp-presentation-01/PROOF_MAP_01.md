# Known identity and conditional projection foundation

PCC-20261115-3d3f9a records both unchanged original proof gates, all ten local statement bindings, 24 native development tests, four complete identity certificates and four false-identity counterexamples. Standing remains unsigned. [pcc:unverified]

| Lean declaration in lean/LPProjection.lean | Scope | Local binding |
| --- | --- | --- |
| even_four_cycle | Alternating four-edge sum is zero | 374c1b |
| odd_triangle | Alternating triangle sum is twice its root | 13cbd3 |
| two_odd_triangles | Subtracting triangles with the same root cancels | ca6c10 |
| half_ground_edge | Twice an edge minus a half-ground leaves twice the other vertex | e3db4f |
| dot_zero | Finite dot product with zero | b58e30 |
| dot_add | Additivity in the vector argument | d0de65 |
| dot_scale | Scalar compatibility in the vector argument | 84566e |
| combine_kernel | Finite combinations preserve a homogeneous kernel | 032fe9 |
| combine_full_kernel | Finite combinations preserve the split LP/FB kernel | afdc2b |
| projected_kernel_iff_of_finite_spans | Equality of the projected full kernel and constraint kernel, with the explicit spans, annihilation and valid-lift hypotheses below | fe357e |

Every row is a local unsigned binding, not CI-signed standing. Both original gates audit these ten substantive declarations plus three generated equations for dot, for 13 total and zero trusted declarations. The Consumer gate is used with Lean4.34.1 and the Root gate with Lean4.35.0; neither gate is edited. [pcc:unverified]

For A=(L|F), the last theorem assumes: a complete span for the FB projection of ker(A); C annihilates every generator in that span; a complete span of ker(C); and a full A-kernel lift of every generator in the latter span. A full-kernel projection is therefore a combination of vectors killed by C. Conversely, a ker(C) vector is a combination of projected generators whose full lifts combine to a full A-kernel vector. The two kernel-combination lemmas prove these closure steps over an arbitrary commutative ring. [pcc:unverified]

The finite numerical certificates must still discharge every span, annihilation, lift, source-binding and completeness obligation. No actual q223 matrix, Picard character, program equivalence, scalar recovery, complexity or novelty follows from this generic theorem. The original known polynomial identities are also checked by the unchanged native identity module over its own modulus2^61-1; its recorded Lean pointer does not itself execute a prover. See evidence/foundation-proof-and-identity-01 for every original output and exact source/runtime hash. [pcc:unverified]

The first missing-hex build and wrong-version auditor invocation remain in 69d18d and f05c67. The frozen full-population protocol and all original scientific bytes remain unchanged. [pcc:unverified]
