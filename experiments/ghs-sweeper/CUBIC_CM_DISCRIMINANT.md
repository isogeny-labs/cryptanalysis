---
title: "A CM discriminant test for indecomposable cubic gluing"
date: 2026-10-25
geometry: margin=0.85in
fontsize: 10pt
---

This note derives a sufficient polarization test beyond the earlier
small-isogeny bound. Its example is the F512 source trace pair +/-35,
with geometric endomorphism field $K=\mathbb Q(\sqrt{-823})$.
Publication priority and an evaluated attack remain unresolved. The written
geometric proof and the partially formalized integer core are distinct.

## Criterion

Let $A=\operatorname{Res}_{k_3/k} E$ be simple over the finite base field k,
with E ordinary. Suppose the geometric elliptic factors have CM field
$\mathbb Q(\sqrt{-\delta})$, delta positive and squarefree. Let S contain
every degree of a geometric isogeny between distinct factors. For a prime
$\ell\ne\operatorname{char} k$, suppose a rational transverse maximal
isotropic subgroup $L\subset A[\ell]$ has been constructed.

If there is no sorted positive triple $a\le b\le c$, $a+b+c=\ell$, such
that $ab,ac,bc\in S$ and

$$H=2\ell abc-(ab)^2-(ac)^2-(bc)^2\ge0,\qquad \delta\mid H,$$

then the principally polarized quotient $A/L$ is geometrically indecomposable.
The stronger necessary condition is $H=\delta z^2$, $z\in\mathbb Z$;
divisibility alone suffices for the example below.

**Proof.** In a hypothetical geometric polarized splitting, simplicity over k
forces Frobenius to permute three elliptic factors transitively. Restrict the
polarized dual of the quotient to one factor. The component degrees sum to
ell. Single-component support contradicts transversality. Two-component
support gives a single nonzero isogeny in an off-diagonal polarized product
with its Frobenius conjugate, contradicting orthogonality. Thus all three
degrees a,b,c are positive. Compositions with dual components give isogenies
between source factors of degrees ab,ac,bc.

The same off-diagonal orthogonality gives $h_1+h_2+h_3=0$ in a CM Hom-space,
with degrees $n_1,n_2,n_3=ab,bc,ca$. Choose a nonzero quasi-isogeny to identify
this rational Hom-space with K. Its degree form is a positive rational
multiple s of the field norm. If $h_i$ corresponds to $\alpha_i$, then

$$ (n_3-n_1-n_2)^2-4n_1n_2
   =s^2(\alpha_1\bar\alpha_2-\bar\alpha_1\alpha_2)^2
   =-\delta r^2,\quad r\in\mathbb Q.$$

The left side is -H. Since delta is squarefree and H is integral, rational
r must be integral: its reduced denominator squared divides delta. Therefore
$H=\delta z^2\ge0$. This yields the necessary conditions and contradiction.
The argument does not assume that the CM Hom-space basis has been explicitly
computed. The case H=0 is allowed by the test.

## Source simplicity and possible component degrees

For $E/\mathbb F_{512}$ of trace $t=\pm35$, the Frobenius discriminant is
$t^2-4\cdot512=-823$, fundamental and squarefree. Thus the geometric
endomorphism ring is the maximal order of K. The restriction polynomial is
$T^6-tT^3+512$. It is irreducible over the rationals: otherwise the cubic
polynomial $X^3-\pi$ over K would have a root beta in K. Such a root is an
algebraic integer, of norm eight. Its integer trace u lies in [-5,5] and
would satisfy $u^3-24u=t$, which none of those integers does. Hence A is
simple over F8.

Consider the relative Frobenius $F:E_i\to E_{i+1}$ of degree eight and a
geometric map $g:E_i\to E_{i+1}$ of degree n. Set $\eta=\widehat Fg$.
On the rank-one etale 2-adic Tate module, F is invertible and
$\widehat F=8F^{-1}$, so eta acts by a multiple of eight. In the maximal
order write $\eta=(u+v\sqrt{-823})/2$. Its norm is 8n. The 2-adic square
root of -823 is congruent to 3 or -3 modulo 16 (its square is 9 modulo 32),
and eta's divisibility gives $u=16x\pm3v$. It follows that

$$ n=8x^2\pm3xv+26v^2. $$

Changing the sign of v gives the same represented set. Duality handles the
opposite direction, so all three unordered source-factor pairs obey the
necessary degree form $N(x,y)=8x^2+3xy+26y^2$. This proves the degree input
used by the integer screen; the converse representation is not required.
The ordinary elliptic endomorphism/degree and Tate-module facts are standard
inputs, as in Waterhouse's finite-field endomorphism theory; they are not
proved by the integer program.

## Fixed ell=53 exclusion

The source discriminant is a nonzero square modulo 53, so the earlier cubic
module theorem constructs a stable transverse maximal isotropic 53-kernel
for either source twist. For a+b+c=53 and all entries positive, pair products
are at most 676. The identity

$$32N(x,y)=(16x+3y)^2+823y^2$$

bounds all witnesses by $|y|\le5$, $|x|\le10$. Complete enumeration gives
only these degree-feasible triples:

| a,b,c | Triangle condition | H | Remaining test |
|---|---|---:|---|
| 1,26,26 | fails | negative | rejected |
| 8,8,37 | passes | 71,680 | not divisible by 823 |
| 8,13,32 | passes | 103,360 | not divisible by 823 |

Thus every such 53-quotient is geometrically indecomposable. Arithmetic
Torelli gives a genus-three Jacobian over F8 for one source twist, with
isogeny degree $53^3$. Its kernel meets no prime subgroup of order other
than 53, including the respective primes 137 and 239 in the source orders.
The theorem does not select the arithmetic twist or reconstruct the quotient.
The explicit quartics found independently by the O3 census have not been
identified with either particular 53-quotient.

The earlier prime scan covered only $\ell\equiv2\pmod3$ up to 53.
It does not prove that 53 is the first possible prime gluing degree over all
congruence classes. For example, (8,13,16), of sum 37, has $H=823\cdot64$;
the divisibility test allows it. No minimal-degree claim is made.

## Evidence and proof limits

The v1 Rust output that retained two triangle-feasible triples remains
frozen at source commit `214ebc91`. The v2 check and its prospective contract
add the CM discriminant condition without discarding those earlier outcomes.
The new Lean project checks the finite exclusion, sorted-degree bounds and
the natural-number lift using ordinary kernel reduction. Its proof map names
all missing bridges: unbounded integer norm witness bounds, the elliptic
2-adic divisibility argument, CM Hom-space degree forms, polarized splitting,
the ordinary restriction and arithmetic Torelli. Full geometric formalization
remains unfinished; no geometric conclusion is a custom Lean axiom.

This is a derived sufficient recognition test. The full Tian 2023 priority
comparison is unfinished, and there is no evaluated log-preserving isogeny.
It supplies neither an attack-cost measurement nor an asymptotic claim.
