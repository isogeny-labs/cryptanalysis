# Actual odd-source transfer: proof map

Native de87bd and written b9a91f follow prospective e9234b. Six faithful
partial implications pass both unchanged original Lean4.35/4.34.1 gates,
six declarations and zero trusted declarations. Exact original local PCC
bindings pass, all unsigned. The actual geometric interpretation remains
partial. [pcc:unverified]

| Result | Exact declaration / local binding | Scope |
| --- | --- | --- |
| Rational curve equation away from poles | OddSource223.cleared_rational_curve_map / c6dca4 | Universal commutative ring, full cleared equation, y²=S and an actual inverse for D. It does not construct projective extension. [pcc:unverified] |
| Normalized target scaling | normalized_scaling_residual / 796f92 | Universal polynomial identity for (u²x,u³y) and coefficients u⁴a,u⁶b. Actual u=13/nonzero inverse checked in native arithmetic. [pcc:unverified] |
| Scalar recovery | recovery_from_scalar_composition / 7781ea | Derived from actual composite, torsion annihilator, scalar-action multiplication/addition/identity/zero laws and Bezout. It assumes no inverse or injectivity conclusion; actual point-group interpretation remains written. [pcc:unverified] |
| Odd subgroup inverse of13 | thirteen_odd_bezout / ee0e7e | Exact Nat equality639940*13=1+3*2773073. Restricts recovery to the ell subgroup. [pcc:unverified] |
| Whole rational-group inverse of13 | thirteen_full_rational_bezout / 82763b | Exact Nat equality3413013*13=1+4*11092292, conditional on the separately justified rational-group order. [pcc:unverified] |
| Proposed odd inverse of52 | proposed_fiftytwo_odd_bezout / caa2b3 | Exact Nat equality159985*52=1+3*2773073. New Jacobian52 maps have not been constructed. [pcc:unverified] |

All declarations are in odd-source/lean/OddSource.lean, with exact
declaration hashes in evidence/odd-source-bindings-01/claims.json.
The first c6dca4 caller returned not_covered because Lean was absent from
its PATH. The unchanged claim passes after fixing only the caller PATH;
the original verdict is preserved as78ddb7. No theorem statement, proof,
gate, trusted declaration list or keyring was changed. [pcc:unverified]

Remaining bridges: finite-field and elliptic/projective-curve definitions;
whole coefficient certificates as polynomial objects; extension at poles
and infinity; origin-preserving morphisms as homomorphisms; degrees and
separability; actual dual-isogeny interpretation; exact K-point kernels and
finite-group order equality; scalar-action interpretation; Weil restriction
and product polarizations. The native engine executes these maps but is
not a signed execution-proof backend. This partial development does not
replace the full global written result. [pcc:unverified]

The actual different-product j discriminator is native, with the polarized
degree-one-column argument written. New HLP/Picard maps and both52
identities remain a successor task. End-to-end costs, original benchmark
admission and strongest references are unresolved. [pcc:unverified]
