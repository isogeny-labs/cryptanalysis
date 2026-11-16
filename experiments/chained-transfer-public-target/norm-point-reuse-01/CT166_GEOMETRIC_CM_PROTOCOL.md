# CT166 — geometric CM obstruction: prospective repository audit protocol

Date 2026-11-16. [pcc:unverified]. Preliminary human-guided factorization and geometric CM idea preceded this protocol; do not call the mathematical finding blindly preregistered. Repository fixture binding, dual-language test implementation, and directed mutations are prospective.

## Scope and inputs
Read the immutable CT160_FULL_CENSUS.json at Git blob 9a8fb44420385a67eda841e68c4c70c13aedcdb8. Both actual fixed-nu12 endpoint models over K=F_(223^3) have reported group order N=11086844. Verify whole-file content, schema, field size, all coordinate counts, unchanged flag and group order.

Mathematical target: prove that no elliptic E/F223 can have a nonzero **geometric algebraic homomorphism** to either fixed-nu12 endpoint E'/K, or to any F223-isogenous quotient B of Res_(K/F223)(E'), even after arbitrary finite scalar extension. Do not conflate this with an obstruction to abstract group maps, nonadditive encodings, or different targets.

## Checks
1. Independently reconstruct q=223^3, T=q+1-N=2724 and D=T^2-4q=-36938092, and verify T mod 223 is nonzero (target ordinary).
2. Factor -D/4 by complete trial division: 9234523=23*311*1291, with 23,311,1291 distinct primes. The squarefree target CM radicand is -9234523.
3. Enumerate all 59 Hasse-admissible traces t=-29..29 for E/F223. For t=0 E is supersingular; for every other t E is ordinary with endomorphism field Q(sqrt(t^2-892)). The squarefree radicand magnitude is at most |t^2-892| <=892, strictly less than 9234523. This proves CM mismatch for **every** E/F223.
4. A nonzero geometric hom between elliptic curves is an isogeny preserving rational endomorphism algebra. The Weil restriction over the algebraic closure splits into three Frobenius-conjugate E' factors, all geometrically isogenous. A target quotient geometrically isogenous to it therefore also has zero geometric Hom from E. Explicitly state that this requires algebraicity and target binding.
5. Provide a pure Python checker and separately implemented Node checker, compare canonical outputs and both Python -O / normal execution, with false-input controls covering altered source counts, boolean values, duplicate JSON keys, nonfinite numbers, and a deliberate CM-collision positive boundary showing that the check is not tautological.
6. No inherited evidence changes, native Rust edits, ledger changes, unapproved compute or auto-merge. Produce source-only report and scope-limited CI if feasible; independent signed PCC remains absent. This is not an end-to-end ECDLP comparison.

## Next experiment
The existing 695/701-record genuine Jacobian parity and owner-admitted C169,C13a,C13b,D native pricing remain highest-priority performance work, but characterize cubic-extension sources rather than an achieved arbitrary prime-field transfer. For prime-field ECDLP, require a new target isogeny class with source-matching geometric CM and explicit injective scalar-blind map before full cold matched rho/BSGS/IC comparison. [pcc:unverified]
