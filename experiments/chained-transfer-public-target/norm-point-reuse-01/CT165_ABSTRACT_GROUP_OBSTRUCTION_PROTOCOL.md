# CT165 protocol — odd-primary k-rational group transfer obstruction

Date: 2026-11-16. [pcc:unverified]. A preliminary local exploratory gcd/factor computation preceded this written protocol; the source-fixture bind, dual-language replay and mutations below are prospective, and the protocol does **not** claim to have been frozen before initial arithmetic.

## Scientific question

For k=F_223, K=F_(223^3), and each of the actual fixed nu12 endpoints E'/K whose point count is pinned by CT160, let A=Res_(K/k)(E') and let B/k be any abelian variety **k-isogenous** to A, including the nine CT163 order-eight quotients. Does there exist even an abstract *group homomorphism* G -> B(k) with nonzero image of odd prime-order subgroup G <= E(k), for an arbitrary elliptic curve E/k?

This is narrower than excluding every possible computational transfer, but strictly stronger in a different sense than CT161's algebraic Hom_k(E,A)=0: the obstruction must apply without assuming a map comes from an algebraic morphism.

## Pinned original evidence and preconditions

- Read original CT160_FULL_CENSUS.json, schema ct160-fixed-nu12-whole-field-census/v1; source and target orders each 11086844, q=223^3.
- Read original CT160_GENERATOR_AUDIT.json with prime subgroup order 2771711 and group order 11086844.
- Read CT163_RESULT.json (nine Frobenius-stable Lagrangians) and CT164_RESULT.json (nine quotient kernels with rational two-torsion two). Do **not** alter these originals.
- The mathematical conclusion for B requires B be k-isogenous to A, not merely a finite symplectic kernel list or an unconstructed genus-three curve.
- Hasse's theorem gives #E(k) in [q+1-floor(2 sqrt q), q+1+floor(2 sqrt q)]. For k=F_223 this is [195,253]. Lagrange's theorem gives image order dividing gcd(#E(k), #B(k)).

## Predicted bounded checks

1. Fail closed on modified source fields, missing models, unexpected field size/trace, count mismatch, changed CT163/164 kernels or schema. Compute r = #A(k)/4 and certify r is prime by complete trial division, without external CAS.
2. Independently recompute the full Hasse-eligible integer interval, evaluate gcd(m,11086844) for every integer m in the interval, classify maxima and certify the **odd** common factor is always one; avoid assertions disabled by Python -O.
3. Independently implement the same integer theorem check in C++17 or Node using a different algorithm, with negative controls for wrong count, wrong interval, a fake small odd shared prime and an altered quotient order.
4. Make a machine-readable canonical result; do not claim independent signed PCC, native transfer evaluation, or speedup based on elementary finite arithmetic.
5. Explicitly distinguish abstract homomorphisms E(k) -> B(k) from maps into B(k^d), arbitrary encodings that are not subgroup homomorphisms, and general source curves over other fields.

## Decision rule

If gcd's odd part equals 1 for all possible #E(k), the only possible image of an abstract group homomorphism E(k) -> B(k) is 2-primary of order at most four. In particular *no injective scalar-preserving homomorphism exists on any nonzero odd-order prime-field ECDLP subgroup*. Record this as a source-specific negative result; pivot attention to carriers with a matching source-subgroup factor or to non-k-rational representations. Owner-admitted whole native replay and paired C169/C13a/C13b/D plus matched full ECDLP remain separate blocked performance work. No paid execution or protected merge.
