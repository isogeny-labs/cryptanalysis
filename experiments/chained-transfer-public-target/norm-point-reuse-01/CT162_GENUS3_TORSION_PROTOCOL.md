# CT162 — prospective genus-3 hyperelliptic carrier filter

Date: 2026-11-16. Standing: [pcc:unverified]. Parent: CT160 full q223 census and CT161 Weil-simple certificate on cryptanalysis #1589; root crypto #3877.

## Objective / hypotheses
Test whether the **actual fixed nu12** F223-simple threefold isogeny class can be ruled out as a hyperelliptic genus-3 Jacobian using the published necessary mod-2 Weil-polynomial criterion, and, conditionally on an **odd-degree** k-isogeny, whether its exact k-rational 2-torsion further filters possible Weierstrass Frobenius orbit structures.

Input fixed by CT160_FULL_CENSUS.json (unmodified): k=F223, K=F_(223^3), source and target both #E(K)=11,086,844, and each has exactly three rational x-roots of x^3+Ax+B (the census `zeros` count). CT161 fixes F(X)=X^6-2724X^3+223^3, irreducible over Q. For a hypothetical genus-3 hyperelliptic Jacobian over k with this F, W consists of 8 geometric Weierstrass points; Frobenius orbit sizes form an unordered partition d of 8. The necessary polynomial congruence is
`F(X) mod 2 = (prod_i (X^(d_i)-1))/(X-1)^2 mod 2`.

The representation on J[2] is the even-sum F2-subspace on W modulo the all-ones vector. Enumerate its 64 classes; compute rational J[2] as exactly Frobenius-fixed classes, not by assuming a semisimple mod-2 representation. **Only if** an isogeny from Res(E) to J has degree odd does it induce an isomorphism on 2-torsion Galois modules, hence force #J(k)[2]=#E(K)[2]=4. For an even-degree isogeny no such rank inference is allowed.

## Protocol frozen before new checker
1. Parse CT160_FULL_CENSUS.json with strict unique-key and finite-token requirements; assert source and target field size/order/census counts/accepted status. Pin its SHA256 from CT161 as `58af5c02d3a5afc722e1662e2fb5ade0534e65f824a29c97abc51dab827d08c8`; do not mutate or replace original evidence.
2. Enumerate every integer partition of 8 (22 expected) using only Python standard library. Implement GF2 polynomial multiplication and exact division by (X+1)^2; compare quotient to F mod 2 derived from CT160.
3. Independently generate the Frobenius permutation on 8 Weierstrass positions for each partition, enumerate all even 8-bit vectors modulo complement (64 classes), and count fixed classes. Cross-check that counts are powers of two; enumerate the exact permitted partitions and the odd-isogeny subcase.
4. Reject at least five mutations: wrong trace parity, incorrect field cardinality, counterfeit zero RHS count, noncanonical/duplicate JSON keys, and deliberately wrong polynomial partition. Check Python normal and `-O` output identity. Never infer nonexistence from mere failure of the necessary-condition screen.
5. Produce a source-only report, exact reproducibility commands and small scoped CI; do not run native Jacobian pricing, paid EKS/Spot, nor PCC ledger mutation in this isolated continuation. Complete solver objective remains owner-gated 695/701 real native parity plus C169/C13a/C13b/D and matched cold single-target rho/BSGS/IC including all setup and memory.

## Literature checked
E. Costa, R. Donepudi, R. Fernando, V. Karemaker, C. Springer, M. West, *Restrictions on Weil polynomials of Jacobians of hyperelliptic curves* (2020), Proposition 2.4/Theorem 2.8, https://arxiv.org/pdf/2002.02067. The criterion is only necessary for hyperelliptic Jacobians; it does not cover nonhyperelliptic plane quartics.

Internal sources reviewed: CT160_FULL_CENSUS.json, CT161_WEIL_SIMPLE_REPORT.md, cryptanalysis #1533 (CT125 native reuse), cryptanalysis #1562 (admitted pricing), root crypto #3877, crypto #4215 and GPU IC #4178. Shared research-KB and Conductor interfaces are not loaded here; lead atlas in crypto-autoresearcher was enumerated but individual YAML reads failed in this runtime. This is a pre-existing published parity criterion, not a novelty claim.
