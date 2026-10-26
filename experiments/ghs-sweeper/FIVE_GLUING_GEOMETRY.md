---
title: "From a five-torsion screen to genus-three existence"
date: 2026-10-25
geometry: margin=0.85in
fontsize: 10pt
---

This is a derived sufficient genus-three existence criterion. It extends the
module theorem in `CUBIC_GLUING.md`; it does not reconstruct a curve or
establish publication novelty. The exact check is frozen separately in
`FIVE_GLUING_GEOMETRY_CHECKS.md`.

## Indecomposability lemma

Let $A=E_0\times E_1\times E_2$ with its product principal polarization
over an algebraically closed field of characteristic different from five.
Let $L\subset A[5]$ be a maximal isotropic subgroup transverse to each
coordinate elliptic curve. Suppose no geometric isogeny of degree at most
six joins distinct $E_i$. Then the principally polarized quotient $B=A/L$
is geometrically indecomposable.

**Proof.** Write $\phi:A\to B$ for the quotient. If B were decomposable,
a principally polarized threefold has a principally polarized elliptic
factor D. Restrict the polarized dual $\phi^\dagger:B\to A$ to D,
and write its components $f_i:D\to E_i$. Since
$(\phi^\dagger)^*\lambda_A=5\lambda_B$, the nonzero component degrees
$d_i=\deg f_i$ sum to five. If two components are nonzero, composing
$f_j\widehat f_i:E_i\to E_j$ gives an isogeny of degree
$d_i d_j\le\lfloor25/4\rfloor=6$, a contradiction. If only one
component is nonzero, its degree is five. The identity
$\phi\phi^\dagger=[5]$ on D then implies that $\phi|_{E_i}$ has degree
five as well, since $\deg[5]_D=25$. This contradicts
$L\cap E_i=0$. Thus B is indecomposable.

The degree-six hypothesis is sufficient, not asserted necessary. This is
the same polarization-degree argument as the earlier three-gluing lemma,
with the extra degree partitions accounted for explicitly.

## Binary cubic criterion

Let $K=\mathbb F_{2^{3d}}$, $k=\mathbb F_{2^d}$, $d\ge3$, and
$E_a/K:y^2+xy=x^3+a x^2+b$, with b of full absolute degree $3d$.
Let t be its K-trace and $q=2^d$. Assume:

1. $t^2-4q^3$ is a nonzero square modulo five.
2. For $j=1/b$ and $y=j^q$, all four values
   $\Phi_3(j,y),\Phi_5(j,y),\Phi_3(j^2,y),\Phi_3(j,y^2)$ are nonzero.

Then one of E and its nontrivial quadratic twist admits, through its Weil
restriction, a k-rational $(5,5,5)$-isogeny to the Jacobian of a smooth
genus-three curve over k. The isogeny is injective on every prime subgroup
of order $r\ne5$ of that selected source twist.

**Proof.** The discriminant hypothesis gives two distinct rational
eigenvalues on E[5]; apply the module theorem to obtain L. All source
conjugates are ordinary and have full absolute j-degree. Over an algebraic
closure an ordinary binary elliptic curve's degree-two isogeny targets
have j-invariants $j^2$ and $j^{1/2}$. Degree-four targets have invariants
$j^4,j,j^{1/4}$. Full degree and $d\ge3$ exclude equality with a distinct
relative conjugate, so degrees 1,2,4 cannot occur.

The classical modular polynomials exclude degrees 3 and 5. A degree-six
isogeny factors into degrees two and three. Its j-pair therefore satisfies
$\Phi_3(j^2,y)=0$ or $\Phi_3(j^{1/2},y)=0$. Squaring the latter equation
is equivalent to $\Phi_3(j,y^2)=0$. The four tests exclude these cases.
Checking the pair $(j,j^q)$ covers all conjugate pairs: Frobenius cycles
the indices, and duality reverses an isogeny without changing its degree.
Thus the lemma applies.

An indecomposable principally polarized threefold over an algebraically
closed field is a genus-three Jacobian. Arithmetic Torelli over the finite
base field gives either B or its [-1]-twist as a Jacobian over k. The odd
relative degree three makes this twist the Weil restriction of the source's
nontrivial quadratic twist. The degree of the gluing isogeny is $5^3$;
its kernel cannot meet an r-subgroup for $r\ne5$.

This proof does not choose which twist works, assert hyperellipticity,
construct C, evaluate the isogeny or bound the total attack cost. These
distinctions are required before promoting a candidate into an attack
catalogue. The general theorem and geometric bridges have not been
formalized in Lean; the pinned fixed module proof is partial.

## Exact modular polynomials and sources

The retained integer coefficients from
[Sutherland's MIT distribution](https://math.mit.edu/~drew/ClassicalModPolys.html)
reduce in characteristic two to

$$\Phi_3(X,Y)=X^4+Y^4+X^3Y^3,$$
$$\Phi_5(X,Y)=X^6+Y^6+X^5Y^5+X^4Y^2+X^2Y^4.$$

`cubic-gluing-reference/PROVENANCE.json` binds their source URLs and
SHA-256 digests. Rust unit checks parse the retained integer coefficients
and compare the complete reductions, including symmetry. This verifies
the implementation against those fixtures, not a new computation of the
classical modular polynomials. The distribution cites
[Bröker--Lauter--Sutherland, 2010](https://arxiv.org/abs/1001.0402) for
prime-level computation.

The Jacobian existence and arithmetic-twist steps use the same published
results and limits as `THREE_GLUING.md`: Oort--Ueno and
[Beauville--Ritzenthaler](https://arxiv.org/abs/1005.3683), with the finite-field
Torelli distinction preserved. Tian's preprint already uses the isotropic
quotient approach for cubic cover attacks. Hess's broad binary descent
inclusion remains a baseline. Exact recognition priority and the full 2023
journal comparison are unresolved.

![The solid part ends at existence for one source twist. Target reconstruction and a log transfer remain open.](cubic-gluing-figures/five-geometry.pdf){width=95%}

The previous module diagram is not rewritten; this diagram adds the new
geometric hypotheses. No canonical curve or isogeny route is added without
the explicit selected target and checked map. Results are recorded in the
new dated `CUBIC_GLUING_RESULTS.md`, preserving the preregistered notes.
