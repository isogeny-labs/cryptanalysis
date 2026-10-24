---
title: "A binary cubic 3-gluing recognition criterion"
date: "2026-10-24"
geometry: margin=24mm
fontsize: 10pt
---

**Status: derived criterion and proof; publication priority unresolved.**
This is a different search direction from the existing hyperelliptic
Artin--Schreier sweeper. It does not establish a novel affected family or a
completed attack. Beating Pollard rho is not an acceptance condition.

| Requested deliverable | Current evidence |
|:--|:--|
| A genuinely new affected family or recognition criterion | Candidate criterion derived below; publication novelty remains unresolved. |
| A short proof | Module proposition, indecomposability lemma and twist-pair corollary below. No formal Lean or independent mathematical review. |
| Rust in the cryptanalysis repository | Standalone native checker, with independent finite-algebra unit verification. |
| An explicit subgroup/log transfer | Not implemented for this route; source torsion coordinates, target and twist character remain open. |
| Continue the earlier search | The 355 pending hyperelliptic jobs remain pending, with their protocol admission unresolved. |

## Question and literature boundary

Can a small-torsion test identify binary elliptic curves for which a
genus-three transfer exists, without first enumerating hyperelliptic covers?
Tian's [2020 preprint](https://arxiv.org/abs/2012.07173), section 3,
already constructs cubic-extension transfers through rational maximal
isotropic subgroups of a Weil restriction. The approach itself is prior
work. The preprint's reconstruction uses odd-characteristic equations and
two-torsion bitangents; it is not a binary implementation. The
[2023 journal version](https://doi.org/10.1007/s00145-023-09474-2) is
subscription-only in this session; its full contents have not been read.

The narrower contribution attempted here is a complete mod-3 module test,
explicit kernels, and a binary sufficient condition for geometric
indecomposability. Novelty of that formulation still needs a direct check
against the full journal version and other gluing classifications.
Unsuccessful keyword searches do not settle priority.

## An exact module criterion

Let $k=\mathbf F_q$, $K=\mathbf F_{q^3}$, with characteristic different
from three, and let $E/K$ be elliptic. Put $A=\operatorname{Res}_{K/k}E$.
Let $M$ be the matrix of $q^3$-Frobenius on $E[3]$, so
$\det M=q^3=q\pmod3$, and let $t=\operatorname{tr}M$ in $\mathbf F_3$.
In Frobenius-transported bases, $A[3]=V_0\oplus V_1\oplus V_2$ has

$$F(v_0,v_1,v_2)=(Mv_2,v_0,v_1),\qquad
\Omega=J\oplus qJ\oplus q^2J,\quad
J=\begin{pmatrix}0&1\\-1&0\end{pmatrix}.$$

Thus $F^*\Omega=q\Omega$. Call a three-dimensional subspace $L$
**coordinate-transverse** if $L\cap V_i=0$ for each $i$. This is the
necessary coordinate condition in Tian's construction, not by itself a
general theorem that a quotient is a Jacobian.

**Proposition (derived).** An $F$-stable, coordinate-transverse Lagrangian
$L\subset A[3]$ exists if and only if either

1. $q=-1\pmod3$ and $t=0\pmod3$; or
2. $q=1\pmod3$ and $M=I$ or $M=-I$.

**Positive cases.** In case 1 choose eigenvectors $e,f$ of $M$ with
eigenvalues $1,-1$. Write their transported copies as $e_i,f_i$.
The subspace

$$L=\langle e_0+e_1+e_2,\ f_0+f_1,\ f_1+f_2\rangle$$

is stable: $F$ cyclically permutes the $e_i$, sends $f_0$ to $f_1$,
$f_1$ to $f_2$, and $f_2$ to $-f_0$. The $f$-coordinates satisfy
$b_0-b_1+b_2=0$. The weighted pairing makes them orthogonal to
$e_0+e_1+e_2$. There are three independent generators, so $L$ is
Lagrangian. A vector supported in one factor must first have zero
$e$-coefficient, then zero $f$-coefficient by that relation.

In case 2 write $M=\lambda I$, $\lambda=\pm1$. Rescaling the bases
of the three factors by $1,\lambda,1$ turns $F$ into $\lambda$ times
cyclic permutation and leaves the pairing unchanged. In these bases put

$$L=\{((s,y_0),(s,y_1),(s,y_2)):
          s=y_0+y_1+y_2\}.$$

It has dimension three, is stable, and its pairing on two vectors is
$s\sum y_i'-s'\sum y_i=0$. Support in one factor forces $s=0$ and then
the remaining $y_i=0$. Transform back to the transported bases.

**Exclusion of all other cases.** The characteristic polynomial of $F$ is

$$T^6-tT^3+q^3=(T^2-tT+q)^3\quad\text{over }\mathbf F_3.$$

When $q=-1,t\ne0$, or $q=1,t=0$, the quadratic on the right is
irreducible. Every invariant subspace then has even dimension, excluding
a Lagrangian of dimension three. In the remaining case $q=1,t\ne0$,
$M$ has a repeated eigenvalue $\lambda=\pm1$. If it is nonscalar,
$\dim\ker(F-\lambda)=\dim\ker(M-\lambda)=1$, so $F$ is a single
Jordan block of size six. Its unique invariant three-space is
$\ker(F-\lambda)^3=\ker(M-\lambda)^{\oplus3}$. It intersects each
coordinate plane in a line. This proves necessity. $\square$

## A binary coefficient test

For the ordinary normalized binary curve

$$E/K:\quad y^2+xy=x^3+ax^2+b,\qquad b\ne0,$$

the three-division polynomial is $\psi_3(X)=X^4+X^3+b$. Its four distinct
roots encode the four lines in $E[3]$; they depend on $b$, not on the
quadratic twist $a$. They are distinct because $\psi_3'=X^2$ and $b\ne0$.
The proposition therefore becomes the following exact recognition rule:

| Base field | Rational roots of $\psi_3$ over $K$ required |
|:--|:--|
| $q=2^d$, $d$ odd | Exactly two, equivalently factor degrees $(1,1,2)$. |
| $q=2^d$, $d$ even | All four, equivalently factor degrees $(1,1,1,1)$. |

For odd $d$, determinant $-1$ makes two fixed projective lines equivalent
to eigenvalues $1,-1$; the alternative is an irreducible quadratic.
For even $d$, all four lines are fixed exactly when $M$ is scalar.
Root count is $\deg\gcd(\psi_3,X^{2^{3d}}-X)$, requiring no elliptic
point-counting census. For odd $d$ one may also use $3\mid\#E(K)$,
since $q^3+1=0\pmod3$ and $t=0\pmod3$.

### The odd-degree rule reduces to one trace

When $d$ is odd, set $n=3d$ and $c=b^{(2^{n+1}-1)/3}$, the unique cube
root of $b$ in $K$. The coefficient test is exactly

$$\operatorname{Tr}_{K/\mathbf F_2}(c)=0.$$

Here is a direct algebraic proof. Cube and fourth-power maps are
permutations of the relevant cyclic/Frobenius orbits for odd $n$. More
precisely, $u\mapsto u^4+u$ has kernel $\mathbf F_2$ and image the
absolute-trace-zero hyperplane. The substitutions

$$c=u^4+u=u(u^3+1),\qquad x=u^3+1$$

give $x^4+x^3=c^3=b$. Conversely, from a root $x$ take
$u=\sqrt[3]{x+1}$ to recover $c=u^4+u$. Thus the quartic has roots if
and only if $c$ has trace zero, and then has exactly two. An explicit
solution of $u^4+u=c$ is the Frobenius-four half-trace

$$u=\sum_{i=0}^{(n-1)/2}c^{2^{4i}}.$$

Indeed $u^4+u=c+\operatorname{Tr}(c)$. Its two solutions $u,u+1$
give the two division roots $u^3+1,(u+1)^3+1$.

**This trace test is not new on its own.** Its connection to rational
three-torsion and binary Kloosterman sums overlaps established work; see
[Moisio, Theorem 7.3 and Remark 7.4](https://arxiv.org/abs/0706.2112),
which cites Charpin--Helleseth--Zinoviev for the odd-degree case. That
source was checked before adding this simplification. The candidate under
priority review is its use with the induced-module and indecomposability
arguments here, not a claim of inventing the trace condition.

## From the kernel to a genus-three Jacobian

**Lemma (derived).** Suppose no degree-one or degree-two isogeny over
$\bar k$ joins two distinct factors of $A_{\bar k}$. If $L$ is as above,
the induced principally polarized quotient $B=A/L$ is geometrically
indecomposable.

**Proof.** The quotient isogeny $\phi:A\to B$ has polarized dual
$\psi:B\to A$ with $\psi\phi=[3]$, $\phi\psi=[3]$, and
$\psi^*\lambda_A=3\lambda_B$. If $B$ were a product, its dimension
three forces an elliptic polarized factor $\iota:D\hookrightarrow B$.
The components $f_i$ of $\psi\iota:D\to\prod E_i$ satisfy
$\sum_i\deg f_i=3$, with zero assigned to a zero component.
If at least two are nonzero, one has degree one, and another has degree
one or two. Their composition gives a forbidden isogeny between distinct
$E_i$. If just one component is nonzero it has degree three. Since
$\phi\psi\iota=[3]\iota$, the corresponding $\phi|_{E_i}:E_i\to D$
also has degree three. Its kernel is a nontrivial subgroup of
$L\cap E_i[3]$, contradicting transversality. $\square$

**Corollary (derived; one twist only).** Let $q=2^d$, $d\ge2$, and let
$b\in\mathbf F_{2^{3d}}$ have full **absolute** degree $3d$. If the
root criterion above holds, one of the two quadratic twists of $E$ admits
a $k$-rational $(3,3,3)$-isogeny

$$\operatorname{Res}_{K/k}E^{(\epsilon)}\longrightarrow J_C,$$

where $C/k$ has genus three. The isogeny is injective on every
prime-order subgroup with prime different from three.

**Proof.** The conjugate $j$-invariants are $1/b$, $1/b^q$, $1/b^{q^2}$.
Full absolute degree makes them distinct. For an ordinary binary elliptic
curve, every geometric degree-two isogeny has target $j^2$ or $\sqrt j$:
its kernel is the unique connected or the unique etale order-two subgroup.
The exponents $d,2d$ modulo $3d$ are neither $1$ nor $-1$ when $d\ge2$.
Thus the lemma applies to the three conjugate factors.

The quotient is a geometrically indecomposable principally polarized
threefold. The dimension-three Jacobian theorem and arithmetic Torelli,
as stated in [Beauville--Ritzenthaler, section 3](https://arxiv.org/abs/1005.3683),
give $B\simeq J_C$ or its $[-1]$ quadratic twist. These existence
statements include characteristic two; their odd-characteristic
discriminant reconstruction is not used here. Since $[K:k]=3$ is odd,
the nontrivial quadratic character of $k$ restricts nontrivially to $K$.
Twisting the isogeny therefore selects one of the two source twists.
Its kernel is killed by three, so a prime subgroup of order different
from three survives. $\square$

In particular, for every odd $d\ge3$ this gives the succinct sufficient
criterion: full absolute degree of $b$ and $\operatorname{Tr}(\sqrt[3]b)=0$
imply a genus-three transfer for one source twist. A parametric version is
$b=(u^4+u)^3$, retaining only nonzero full-degree $b$. This is a derived
family description; its status as a previously unrecognized affected family
has not been established.

This proves an existence criterion for a twist pair. It does **not**
identify the right source twist, instantiate $C$, evaluate the isogeny,
or prove that the resulting $C$ is non-hyperelliptic. At $d=1$ the
degree-two conjugate isogenies invalidate the lemma's hypothesis.
Proper-subfield and Koblitz coefficients are excluded from the corollary.
Failure of the criterion excludes this particular 3-gluing kernel type;
other isogeny degrees and cover constructions remain possible.

![Recognition, geometric and explicit-transfer obligations are separate.](three-gluing-figures/criterion.pdf)

## Native Rust boundary and next search

`examples/three_gluing.rs` checks a supplied mod-three matrix, constructs
the explicit module kernel in the positive cases, and verifies its pairing,
stability and intersections. Its binary-coefficient mode applies the
polynomial-gcd test, checks full absolute degree and preserves all remaining
twist, target and explicit-map obligations. It does not change the frozen
sweeper engine or existing journal fingerprints.

```sh
cargo run --release --locked \
  --manifest-path experiments/ghs-sweeper/Cargo.toml \
  --example three_gluing -- curve --base-degree 3 --a 0 --b 24
cargo run --release --locked \
  --manifest-path experiments/ghs-sweeper/Cargo.toml \
  --example three_gluing -- matrix --q-mod-3 2 --entries 1 0 0 2
```

The independent unit code checks all 48 invertible two-by-two matrices
against a direct enumeration of the 1120 Lagrangians for each weighted
form. Fixed coefficient controls compare polynomial-gcd counts with direct
raw-field evaluation. See [THREE_GLUING_CHECKS.md](THREE_GLUING_CHECKS.md).
These are software checks of a fixed algebraic statement, not new
curve-search campaign data or a completed cryptanalytic experiment.

**Fixed software observations:** all 28 release all-target tests pass,
including the three new tests. The direct subspace check agrees with the
criterion on all 48 invertible matrices, using 1120 Lagrangians per weighted
form. Formatting and all-target Clippy with warnings denied pass. At the
fixed degree-nine coefficient $b=24$ (modulus 515), both supplied constants
$a=0,1$ give two rational division roots, and $b$ has absolute degree nine.
This verifies the recognition condition for that twist pair; it does not
select a twist or instantiate its target. The raw
[unit log](three-gluing-checks/all-targets-attempt-1.txt) retains the exact
software result. No curve-population or cost comparison is made, so no
quantitative curve-yield or performance graph is inferred from these checks.

The next mathematical/computational obligations are: priority review of
this exact criterion; binary quotient reconstruction; the characteristic-two
obstruction character; source-coordinate torsion certificates; explicit
isogeny evaluation and planted-log replay. Only then can an exact curve and
subgroup enter the weak-curve catalogue. No cost comparison is required to
identify an affected family, but no measured cost is asserted here.

The larger hyperelliptic campaign remains separate. At inspected
`crypto-autoresearcher origin/main` commit
`4ea4e6a22ab30e4da6f4b7515e4fe2dfbdfa8a58`, its required canonical
protocol tool is still absent. No campaign was run under a substitute
protocol. This does not block the proof and native checker work above.

## Evidence, source gaps and graph audit

- **Read primary:** Tian, 2020 preprint, sections 1 and 3; establishes
  the isogeny-based cover-attack prior art and necessary coordinate
  condition. [arXiv:2012.07173](https://arxiv.org/abs/2012.07173).
- **Read primary:** Beauville--Ritzenthaler, introduction and section 3,
  especially Proposition 3.1 and the characteristic-two discussion.
  [arXiv:1005.3683](https://arxiv.org/abs/1005.3683).
- **Read primary:** Lachaud--Ritzenthaler--Zykin, Theorem 1.1.1, gives
  the any-field arithmetic Torelli alternative.
  [arXiv:0802.4017](https://arxiv.org/abs/0802.4017).
- **Read primary:** Moisio, section 7, Theorem 7.3 and Remark 7.4,
  documents the older trace-of-cube-root condition in the binary
  Kloosterman setting. [arXiv:0706.2112](https://arxiv.org/abs/0706.2112).
- **Prior local work:** Hess baseline [HESS_SCOPE.md](HESS_SCOPE.md),
  old [prior-art comparison](reference/prototype-prior-art.md), and
  Diem--Scholten's 2003 cover-attack report. These do not establish priority
  for this formulation.
- **Unread:** the full 2023 Tian journal version and restricted Murai
  thesis. Neither is represented as ruled out. Literature searches for
  binary cubic gluing, scalar Frobenius and rational 3-torsion did not
  establish novelty.

Claims above are derived mathematical statements, not independently
reviewed mathematical results or Lean-checked theorems. Exact source-curve
and subgroup IDs, candidate IDs and run IDs for attacks are null: no
instantiated transfer is supplied. Measured construction, transfer, solve
and rho costs are null.

Graph sources checked: the hyperelliptic infrastructure source-parity
table; the GHS audit and branch-orbit/prior-art reports; the canonical
curve registry and isogeny-route index where available in the repository
tree. No new instantiated curve or verified edge follows from a symbolic
twist-pair existence result, so those graphs remain unchanged. The new
diagram is explicitly a theorem/obligation flow, not an isogeny graph.
