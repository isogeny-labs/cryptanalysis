# Requested scope

The request is to finish the open work identified in the 2026-11-19 status
review of the NIST genus-three `(3,3,3)` isogeny lead.

| Requirement | Acceptance evidence |
|---|---|
| Reproduce the NIST mod-3 eligibility claim | Exact NIST parameters, Frobenius action on `E[3]`, exhaustive Lagrangian enumeration, and negative controls for the other NIST prime curves |
| Produce explicit P-224 and P-256 kernels | Torsion-field definitions, exact 3-torsion basis points, three kernel generators, 27-element/rank/isotropy/transversality checks, and Frobenius-stability checks |
| Establish subgroup preservation | Proof that the prime-order NIST subgroup has trivial intersection with a 3-primary kernel and a conditional dual-isogeny recovery certificate |
| Construct the genus-3 quotient and explicit point map | Plane-quartic equation over the working field, executable `(3,3,3)` isogeny, homomorphism tests, dual-composition test, and exceptional-point accounting |
| Audit the repeated-product specialization | Complete scalar-diagonal subgroup census, stronger candidate selection where available, bounded complex-fiber theta controls, and an explicit statement of the remaining `End(E)`-linear/finite-field gap |
| Assess computational advantage | Pollard-rho comparison, Tian destination-cost model, construction/transfer/recovery accounting, and explicit separation of measured from modeled evidence |
| Preserve a reproducible handoff | Commands, inputs, outputs, tests, source links, environment manifest, obligation table, and every remaining blocker |

No production key-recovery or discrete-logarithm campaign is in scope. Public
curve structure, bounded algebraic checks, and cost modeling are in scope.
