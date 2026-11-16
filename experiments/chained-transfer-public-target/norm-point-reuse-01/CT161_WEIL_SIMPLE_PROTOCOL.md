# CT161 — exact Weil-restriction simplicity obstruction (prospective protocol)

2026-11-16 · [pcc:unverified]. Existing cryptanalysis PR #1589, root crypto #3877. This protocol precedes CT161's new checker and its source-only execution. CT160's **already published** original fixed-nu12 point counts and earlier SymPy exploratory factorization motivated the hypothesis; no blind discovery claim.

## Frozen input and specific claim

Use only CT160's exact fixed source/target models over K=F_(223^3): both have verified-in-producer-census order 11,086,844 and trace T=2724. Their F_223 Weil restriction A=Res_(K/F_223)(E) has predicted degree-six Weil polynomial F(X)=X^6-2724 X^3+223^3. Prove irreducibility over Q via reduction modulo 5, explicitly checking Rabin's criterion for degree 6: X^(5^6)=X mod f; gcd(f,X^(5^3)-X)=gcd(f,X^(5^2)-X)=1. Do not rely on a CAS irreducibility flag in the committed checker.

If successful, the conditional mathematical deduction is that A is F_223-simple of dimension 3, so Hom over F_223 between A and any abelian variety B of dimension 1 or 2 is zero, in both directions. This precludes a homomorphism transfer **through an elliptic or abelian-surface carrier defined over F_223** into this exact fixed Weil restriction. It does not prohibit genus-3-plus Jacobians, maps over F_(223^3), a different model, or nonhomomorphic/nonalgebraic attacks. Distinguish F_223-simple from geometrically simple: A becomes E times conjugates over K.

## Acceptance and sabotage controls

Implement pure-Python finite-field polynomials (no SymPy dependency) and print canonical JSON containing f coefficients, prime 5, the three checked power residues and the two gcd values. Reject at least three mutations: wrong trace, corrupted constant term, and a reducible degree-six polynomial. Independently check the result locally using a different algebra package, but retain independent-signed PCC as outstanding. Run in normal and -O Python and require matching output; a bounded source-only workflow may exercise it without EKS, native Jacobian or paid pricing.

## Sources and boundary

Prior project: CT151/CT160, crypto #3877, crypto #4425, cryptanalysis #1533/#1589/#1647, owner #3904, AGENTS.md and dated session log. General theory: Tate finite-field isogeny/Hom criterion and Poincare complete reducibility (e.g. F. Oort, *Abelian varieties over finite fields*, §5.3-5.4). KB/Conductor not loaded in this runtime; source-limited search is not a novelty claim.

No 695/701 original/reuse native parity, C169/C13a/C13b/D pricing, complete cold ECDLP benefit, signature, paid compute or protected merge is implied. Preserve those owner-controlled gates.
