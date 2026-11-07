# Exact norm powers expose a large quartic-collision prime

Both saved √2 conjugate-pair resultant norm numerators are **exact integer cubes**. Their cube roots have 72 and 335 decimal digits, versus 214 and 1,005 digits for the original norm numerators. The base-factorization unit norm numerator is the sixth power `3^828=(3^138)^6`. Taking an integer cube leaves its set of prime divisors unchanged, so the smaller roots are the exact inputs for exceptional-prime factor search.

The **quartic** cube root factors completely:

`2^21 · 3^7 · 7^2 · 11^6 · 23^4 · 131 · 4196094289 · 669968600281 · 4335978784654674076339691`.

Checked Sage verified this product and proved every listed factor prime. The last factor is `p=4335978784654674076339691 ≡ 11 (mod 24)`, a new exceptional prime far beyond the earlier ten-million cap. It divides the quartic pair-resultant norm numerator and none of the other five gate norm numerators or the coefficient denominator LCM.

At this prime, the original source-`j=1728` equation has **two rational C points**. One yields a single rational `x_E` root of the quartic factor and two E points; the other yields no rational resolvent root. Both C–E pairs have **zero inverse B-branch numerator and denominator**. The new local polynomial-gcd gate independently counts the two pairs using 373 polynomial multiplications across the two source fibers. The exact coordinates and equation checks are in [`large_prime_result.json`](large_prime_result.json) and [`large_prime_audit.json`](large_prime_audit.json).

## Exact certificates and registered replay

[`protocol.json`](protocol.json) pins the prior norm, field, source-j, resolvent, branch, and fast-gate sources by SHA-256. It records the read-only factor discovery before the persisted run. [`power_certificate.py`](power_certificate.py) recomputes all three exact integer roots, checks their defining powers and the complete quartic factor product, and trial-divides the octic root by every prime below ten million. The octic root still has a **230-digit unfactored cofactor** after those divisions; [`power_certificate.json`](power_certificate.json) retains it exactly. [`audit_power_sage.py`](audit_power_sage.py) independently repeats the power identities and product in Sage and proves primality of the nine quartic-root factors; [`power_audit.json`](power_audit.json) is the receipt.

[`audit_protocol.json`](audit_protocol.json) froze the new large prime and the observed pair count before the registered Sage replay. This is a replay of an exploratory read-only finding, not a prospective holdout. [`classify_large_sage.py`](classify_large_sage.py) recomputes the source-j equation on `C:y²+y=x³−7`, checks its degree-36 y-resultant against the square of the degree-18 field polynomial, enumerates the rational source points and specialized C–E roots, verifies `E:y²=x³+432`, and evaluates both inverse B-branch polynomials. [`audit_large.py`](audit_large.py) independently reconstructs the source points with SymPy, uses the preceding polynomial-gcd kernel for the E-fiber counts, and rechecks every saved curve, source-j, resolvent, factor-membership, and branch equation with integer modular arithmetic. It locates the rational root in the base **quartic** factor and confirms the octic factor is nonzero there. [`validation.json`](validation.json) binds the successful receipts and hashes. All new local Sage jobs used the repository's checked launcher; [`sage-runtime-info.txt`](sage-runtime-info.txt) identifies the accepted build.

## Proof map

| Result | Checked declaration or receipt | Status |
| --- | --- | --- |
| Base-unit norm is a sixth power; quartic and octic norm numerators are cubes | `J1728NormPowers.base_unit_sixth_power`, `quartic_resultant_norm_cube`, `octic_resultant_norm_cube` in [`NormPowers.lean`](formal/NormPowers.lean) | Lean checked, exact full integers |
| Cubing preserves natural prime divisors | `J1728NormPowers.prime_divides_cube_iff` | Lean checked |
| Complete quartic cube-root factorization and primality of nine factors | [`power_audit.json`](power_audit.json) | Exact product and Sage proof-grade primality |
| Large-prime source, C–E, and inverse-branch classification | [`large_prime_result.json`](large_prime_result.json), [`large_prime_audit.json`](large_prime_audit.json) | Checked-Sage and independent Python equation replay |

The Lean build and `#print axioms` output are in [`formal/lean-check.txt`](formal/lean-check.txt), with toolchain and mathlib revision pinned. The degree-18 field coefficient arrays, the prime-factor proofs, and the large-prime curve equations are executable certificates rather than Lean-encoded results; formalization of that full algebraic bridge remains partial. The observation that these particular norms are powers is exact, while a general field-theoretic explanation for the exponent three remains open. The next arithmetic step is a bounded ECM or other factor search on the octic root's 230-digit residual, followed by the fast local C–E gate at any newly certified prime divisor.
