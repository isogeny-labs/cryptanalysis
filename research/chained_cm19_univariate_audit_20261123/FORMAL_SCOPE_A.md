# Partial coefficient formalization; actual geometry remains open

The shared crypto-lean library was inspected first: pinned PR34
b0c73236, Lean4.35.0, Mathlibcfc55fc58714a59dc06e6e79edc6d1d95140d3c2;
existing inherited group/hom interfaces and PROOF_MAP were read. Its
local Mathlib imports all failed the frozen2GiB bound, while the Init
control passed. No unchanged import/cache/build retry is planned.
No actual C7/Jacobian/CM19 geometric bridge is claimed from that work.
[pcc:unverified]

The new consumer-local CoefficientLeavesA imports Init only. It checks
closed integer-pair coefficient identities for Sv=u,ell*u=1, the inverse
Gram row/norm4 and3L's pushforward row, plus the two exact mod7 polynomial
coefficient identities used in the new field presentation. These are
arithmetic leaves, not a new reusable ring/group replacement. Source is
prospective; no formal build or axioms audit has run. [pcc:unverified]

| Result | Declaration | Exact remaining bridge |
|---|---|---|
| Split column |splitColumn| Identify coefficient evaluation with actual CM endomorphisms through genuine beta |
| Global integral left inverse |leftInverseCoefficients| Actual Hom compositions, beta/alpha inverse and coefficient homomorphism |
| Norm4 / degree4 cover |inverseGramRow,normFourCoefficients| Actual Rosati/polarization transport, Jacobian universal property and curve push-pull |
| Pushforward numerator |pushforwardNumeratorCoefficients| Actual B/N correspondence and pushforward/adjoint identification |
| New field model |normPolynomialCoefficients,denominatorInverseCoefficients| Polynomial evaluation in an inherited characteristic7 algebra, irreducibility/tower isomorphism and field instance |

No theorem assumes the research conclusion, uses sorry/admit/custom
axioms/native_decide or changes a shared gate. All seven declarations
request #print axioms. Use the existing exact4.35.0 compiler, one worker,
120seconds/2GiB, captured full output, and canonical auditing where the
actual scope is supported. A successful leaf build would leave the
full actual-object theorem partial. [pcc:unverified]
