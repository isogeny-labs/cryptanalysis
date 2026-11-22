# Classification, obstruction and certificate trust

These are scoped consequences of established finite-group, abelian-variety
and finite-field theory. They do not classify efficient algorithms or establish
publication novelty. The word "transfer" needs the following distinctions.

## 1. Complete abstract prime-subgroup classification

Let S=<P> have prime order r, and let H be any finite abelian group. Evaluation
at P gives a bijection Hom(S,H) -> H[r]. A homomorphism is injective precisely
when its image of P is nonzero. Therefore an injective homomorphism exists if
and only if r divides |H|.

Proof. A homomorphism must send P to R with rR=0, and is determined by that R.
Conversely [j]P -> [j]R is well defined exactly when rR=0. A nonzero map from
a prime-order group has zero kernel. Lagrange gives necessity of divisibility;
Cauchy's theorem gives an element of order r for sufficiency. These arguments
include r equal to the characteristic: H is the group of rational points, not
a statement about geometric group schemes.

This classifies abstract homomorphisms, not cheaply evaluable maps. Evaluating
the formula above from arbitrary source point coordinates may itself require
the discrete logarithm j. Consequently r dividing a Jacobian order is not an
efficient ECDLP reduction certificate.

## 2. Algebraic transfer classification up to isogeny

Let K=F_(q^N), E/K be an elliptic curve of trace t, W=Res_(K/k)(E), and A/k an
abelian variety, where k=F_q. Write

    P_W(T) = T^(2N) - t T^N + q^N.

Then Hom_k(W,A) tensor Q is nonzero if and only if gcd(P_W,P_A) over Q has
positive degree. This applies to every k-algebraic group homomorphism between
these varieties, without restricting equations, cover degree, or GHS family.
Replacing E by a K-isogenous curve preserves this criterion.

Proof of the obstruction direction. A homomorphism commutes with Frobenius.
By Cayley–Hamilton both characteristic polynomials annihilate its two
Frobenius actions. If the polynomials are coprime, a rational Bezout identity,
cleared of denominators, yields c*f=0 for some nonzero integer c. The image
of f is connected and contained in the finite kernel of [c], so f=0.
Equivalently the Hom group of abelian varieties is torsion free.

For the converse, decompose both varieties up to k-isogeny into simple
factors. Tate's finite-field isogeny theorem identifies common irreducible
Frobenius factors with a common simple isogeny factor. Projection onto and
inclusion from that factor give a nonzero rational homomorphism; clearing
denominators gives an actual nonzero homomorphism. Neither argument constructs
a map, proves nonzero action on S, or verifies that A is a Jacobian.

In particular, if P_W is irreducible, every nonzero algebraic homomorphism
W -> J(C) requires genus(C)>=N. Irreducibility/simplicity must be proved for
the supplied instance; the CLI does not assume it. The implemented spectral
test computes a primitive pseudo-remainder gcd over Q, conditionally on the
supplied target polynomial being its actual Frobenius polynomial. It verifies
reciprocity but does not certify an arbitrary polynomial is a Weil polynomial.

This theorem does not cover every map of the finite groups W(k) -> A(k):
abstract homomorphisms need not extend to homomorphisms of abelian varieties.
It also does not cover base-field enlargement or an unspecified target.

## 3. Uniform obstruction for all genus-bounded targets

Let S be an actual subgroup of order r>1 in E(K), and C/k any smooth,
projective, geometrically connected curve of genus g. An injective group
homomorphism S -> J(C)(k) requires

    r <= #J(C)(k) <= (sqrt(q)+1)^(2g).

Thus if r>floor((sqrt(q)+1)^(2G)), no such transfer exists for any g<=G.
This is independent of the cover family, source curve equation, and route
through its K-isogeny class, for routes that preserve the same order-r
subgroup. A route that kills that subgroup does not preserve its ECDLP.

Proof. An injection supplies r distinct rational Jacobian points. Each of the
2g complex Frobenius eigenvalues has absolute value sqrt(q), so the product
formula for #J bounds each factor |1-alpha| by 1+sqrt(q). Monotonicity in g
gives the uniform result. The same proof applies to abelian varieties of
dimension g, not only Jacobians. It places no solver-cost or rho condition.

Exact integer evaluation uses (q+1+2 sqrt(q))^g=A_g+B_g sqrt(q), with

    (A_0,B_0)=(1,0)
    A_(g+1)=(q+1) A_g+2q B_g
    B_(g+1)=2 A_g+(q+1) B_g.

The required floor is A_g+floor(sqrt(q B_g^2)). There are no floating-point
approximations, including q=2. The CLI evaluates every subfield divisor.

For B-163 the certified prime order is
5846006549323611672814742442876390689256843201587. The exact bounds are

    genus 63: 1697213011467681896483704108875603013010097288197
    genus 64: 9892082352510403757550172975146702122837936996353.

Therefore every target over F2 of genus at most 63 is excluded. Genus 64
passes this necessary size test, which establishes no curve, map or attack.
Same-field genus-three covers over F_(2^163) are unaffected by this F2 bound.

## 4. Finite classification and coverage trust theorem

Every ordinary elliptic curve over a binary finite field is isomorphic to
y²+xy=x³+a*x²+b, b!=0. Its j-invariant is 1/b. For a fixed b, transformations
y -> y+s*x identify a modulo s²+s. The image of s -> s²+s is exactly the
trace-zero subspace: its kernel has two elements, its image has codimension
one and lies in that subspace. Thus a=0 and any fixed trace-one a give exactly
the two twists for each b. An isomorphism preserves j, and the standard
normal-form change with a1=1,a3=a4=0 reduces to the stated a equivalence, so
these models exhaust ordinary Fq-isomorphism classes without duplicates.
Two such elliptic curves are Fq-isogenous exactly when their orders/traces
agree, by the elliptic case of Tate's theorem.

The CLI implements this complete enumeration only for degree<=8. Orders are
counted by the Artin–Schreier trace criterion, with separate exhaustive x,y
point-count controls through degree four. It does not manufacture paths
between all equal-trace models. Frobenius coefficient orbits have evaluated
paths, but do not exhaust a general isogeny class.

Trust theorem. For a declared finite universe U, enumeration V and rejection
predicate R, suppose (a) U is contained in V, (b) the rejection test is sound
for the precise transfer property claimed, and (c) every element of V is
rejected. Then no element of U has that property. Proof: any purported
element of U is in V by (a), rejected by (c), and excluded by (b).

The key obligations are (a) and (b), not the mere existence of a completed
search log. The certificate verifier recomputes the canonical enumeration
and its results. It cannot extend U to unimplemented transfer families or
replace an unknown result with rejection. Hashes identify the implementation;
they do not prove its correctness or authenticate the certificate's author.

## Proof map and trusted boundaries

| Claim | Lean coverage | Remaining bridge |
|---|---|---|
| Abstract Hom(S,H) classification | written proof only | finite abelian groups, Cauchy and efficient evaluation distinction |
| Frobenius algebraic classification | written proof only; exact gcd tested in Rust | abelian varieties, Frobenius, Tate and actual target polynomial |
| Uniform size obstruction | `size_obstruction`, `divisibility_obstruction` | injection/cardinality and geometric Weil bound |
| Exact B-163 integer threshold | `weilPair`, `sqrt_upper/lower`, `pair63/64`, `b163_genus63/64_bound`, `b163_obstruction` | identification with the geometric bound above; prime/order checked separately in Rust |
| Finite coverage implication | `closed_coverage` | enumerator completeness, rejection soundness and Rust/Lean refinement |
| Class-invariant transport | `invariant_transport` | trace-isogeny theorem and preservation of the chosen subgroup |

Lean 4.34.1 checks eleven named theorems and one generated equation theorem
transitively. Allowed foundations are propext, Classical.choice and Quot.sound;
no custom axiom, sorry, native_decide, or kernel bypass is used. The complete
mathematical/geometric classification is **not fully formalized**. This table
retains the full statements and names the exact gaps rather than presenting
the arithmetic lemmas as complete geometric proofs.

## Sources and prior art

- Tate, *Endomorphisms of abelian varieties over finite fields*, Inventiones
  Mathematicae 2 (1966), 134–144, doi:10.1007/BF01404549;
  [primary text](https://pazuki.perso.math.cnrs.fr/index_fichiers/Tate66.pdf).
- Menezes–Qu, *Analysis of the Weil descent attack of Gaudry, Hess and Smart*,
  CT-RSA 2001, doi:10.1007/3-540-45353-9_23, Corollary 9 and Table 2:
  M(163)=163, M(233)=30. This is a classical GHS statement, not a generalized
  obstruction to arbitrary covers.
- [SEC 2 v2, section 3.2.3](https://www.secg.org/sec2-v2.pdf), B-163/sect163r2
  field, coefficients, generator, prime order and cofactor.
- [Magma Weil descent documentation](https://magma.maths.usyd.edu.au/magma/handbook/text/1561)
  describes GHS construction and divisor maps; parameter c changes the target.
- The existing native same-field genus-three construction is documented in
  `suite/src/binary_ecc/cover_transfer.rs` and
  `.agents/skills/ecdlp-surfaces/references/higher-genus.md`. This audit reuses it.
- Pocklington's n−1 criterion: the checked prime factors supply F|n−1,
  F²>n and the Fermat/gcd witnesses. For every prime l|n the witnesses force
  F|l−1, hence l>sqrt(n); n is therefore prime. This explains the verifier's
  exact certificate obligations independently of a probable-prime test.
