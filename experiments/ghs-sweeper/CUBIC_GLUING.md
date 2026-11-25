---
title: "Cubic gluing beyond 3-torsion: a module recognition theorem"
date: 2026-10-25
geometry: margin=0.85in
fontsize: 10pt
---

The new result in this note is a derived linear-algebra classification, with
publication priority unresolved. It supplies a checkable kernel criterion for
primes beyond three. It does **not** establish a novel affected curve family,
construct a quotient curve, or evaluate a discrete-logarithm transfer.
The user's acceptance criterion is novelty plus a proof and an explicit
transfer; beating rho is not a gate.

| Requirement | Status at preregistration |
|---|---|
| Recognition theorem beyond the previous 3-test | Written proof below; Rust implemented, new runs pending |
| Exact small-field source set | Complete d=3 census specified; pending |
| Published-priority audit | Partial; Tian's 2023 full article remains unread |
| New descended curve and subgroup map | Not constructed |
| Lean proof of the full classification | Not formalized; fixed constructive case attempted separately |

## The module theorem

Let $\ell$ be an odd prime with $\ell\equiv2\pmod3$, and let
$k=\mathbb F_\ell$. Let $q\in k^*$ and $M\in\mathrm{GL}_2(k)$ satisfy
$\det M=q^3$. On $V=(k^2)^3$ set

$$F(v_0,v_1,v_2)=(Mv_2,v_0,v_1),\qquad
\Omega=J\oplus qJ\oplus q^2J,$$

where $J((x,y),(x',y'))=xy'-yx'$. Then $F$ is a similitude with
multiplier $q$. There exists an $F$-stable Lagrangian $L$ such that
$L\cap V_i=0$ for all three coordinate planes **if and only if $M$ is
split semisimple over $k$**: it is either scalar or has two distinct
$k$-rational eigenvalues.

This concerns geometric torsion coordinates transported from a symplectic
basis on an elliptic curve over $\mathbb F_{q^3}$. Here the displayed q
means its residue modulo $\ell$; the determinant is $q^3$, not q. The
weighted form accounts for the Frobenius transport of the basis.

### Proof: two distinct eigenvalues

Write $Me=\alpha e$ and $Mf=\beta f$. Since cubing is a bijection on $k$,
there is a unique $\lambda\in k^*$ with $\lambda^3=\alpha$. Put

$$v=(e,\lambda^{-1}e,\lambda^{-2}e),\qquad
c_i=q^i\lambda^{-i}.$$

Let $W$ consist of triples $(y_0f,y_1f,y_2f)$ with
$c_0y_0+c_1y_1+c_2y_2=0$. Then $Fv=\lambda v$ and $W$ is stable:
it is the perpendicular space of v inside the stable beta-eigenspace of
$F^3$. The direct sum $L=kv\oplus W$ has dimension three and is isotropic.
All $c_i$ and all e-components of v are nonzero. An element of L supported
in only one coordinate therefore has zero e-part, then zero f-part.
Thus L is transverse. An explicit basis for W uses coefficient vectors
$(c_1,-c_0,0)$ and $(c_2,0,-c_0)$.

### Proof: scalar case

If $M=\mu I$, choose $\lambda^3=\mu$. The determinant identity and
injectivity of cubing give $q=\lambda^2$. In coordinates
$w_i=\lambda^i v_i$, F becomes lambda times cyclic permutation and
$\Omega$ becomes the standard sum of three J's. Write $w_i=(x_i,y_i)$.
Take $x=Sy$, where S is the symmetric three-by-three matrix with zero
diagonal and every off-diagonal entry one. Its graph is a Lagrangian,
is stable under cyclic permutation, and is transverse: a vector supported
in a single coordinate forces its y-entry, and then its x-entry, to vanish.

### Proof: irreducible case

If the characteristic polynomial of M is irreducible quadratic, every
irreducible factor of the characteristic polynomial of F has even degree.
Indeed, if z is a root of such a factor of degree h, then $z^3$ is a root
of the irreducible quadratic, so $\mathbb F_{\ell^2}$ is a subfield of
$\mathbb F_{\ell^h}$ and $2\mid h$. The characteristic polynomial of
an invariant subspace divides that of F. An invariant subspace of odd
dimension, in particular dimension three, is impossible.

### Proof: nonscalar Jordan case

Write $M=\mu I+N$ with $N^2=0$, $N\ne0$. Cubing bijective gives a
unique $\lambda^3=\mu$. The polynomial $T^3-\mu$ factors over k into
one linear factor and one irreducible quadratic, since k has no nontrivial
cube root of unity. The cyclic block companion F has minimal and
characteristic polynomial $(T^3-\mu)^2$: applying a putative annihilator
of degree below six to a vector with a cyclic M-vector in one coordinate
would give an M-annihilator of degree below two. Equivalently, its module
is $k[T]/((T^3-\mu)^2)$.

Its primary pieces are therefore $k[T]/(T-\lambda)^2$ and $k[T]/h^2$,
of dimensions two and four. An invariant three-space must have dimensions
one and two in these pieces, respectively. In each piece that submodule
is unique. Their sum is exactly $\ker(F^3-\mu I)$, the direct sum of the
same M-eigenline in all three coordinates. It contains a line in each
coordinate plane and fails transversality. These four cases exhaust M.

## A source-trace screen at ell=5

For $E/\mathbb F_{q^3}$ with trace t, put
$\Delta=t^2-4q^3\pmod5$. A nonzero square Delta proves the positive
split-distinct case; a nonsquare proves the irreducible case. If Delta
vanishes, the trace does not distinguish scalar from Jordan Frobenius.
The two matrices I and $\left(\begin{smallmatrix}1&1\\0&1\end{smallmatrix}\right)$
have the same characteristic polynomial but opposite outcomes.

For ordinary binary curves over F512 relative to F8, the old 3-test is
$t=0\pmod3$. Here $512=2\pmod5$, so the sufficient 5-test becomes
$t=2$ or $3\pmod5$. Consequently traces satisfying the latter and
$t\ne0\pmod3$ pass a different torsion-kernel test. This does not mean
that the source curves were previously unknown to cover attacks.

![Scope of the recognition result. Solid arrows are proved module implications; dashed arrows are unfinished geometric constructions.](cubic-gluing-figures/criterion.pdf){width=95%}

## Geometric boundary

A maximal isotropic kernel gives a principally polarized quotient of the
Weil restriction. Transversality alone has not been proved sufficient here
for its geometric indecomposability at ell=5. The earlier ell=3 proof
uses degree partitions of three; it cannot simply be reused for five.
The partitions $5=1+4=2+3=1+1+3=1+2+2$ introduce possible geometric
isogenies of degrees up to six between source conjugates. Excluding those
is a sufficient route to an indecomposability proof, still to be checked
on any source promoted beyond this module screen. Arithmetic Torelli,
source-twist selection, quotient reconstruction and explicit log transport
remain open. No curve ID or catalogue attack edge is issued here.

## Prior art and provenance

- [Tian, 2020 preprint, section 3](https://arxiv.org/abs/2012.07173)
  already assumes a rational maximal isotropic kernel avoiding the coordinate
  elliptic factors and constructs the resulting isogeny in an odd-characteristic
  model. The method is not new. The exact recognition classification above
  is not asserted in the inspected section. This does not establish priority.
- [Tian, 2023 journal version](https://doi.org/10.1007/s00145-023-09474-2)
  remains accessible only as a subscription preview in this session. Its full
  contents have not been compared, so novelty stays unresolved.
- [Tian et al., 2018](https://doi.org/10.1007/s10623-018-0457-6)
  explicitly describes an odd-characteristic degree-three cover construction
  for cofactor-two curves. Its abstract is not a binary reconstruction theorem;
  full theorem-level comparison is still owed.
- Hess's generalized descent already covers the ordinary full-relative-degree
  binary sources in the broad existence sense; see the frozen `HESS_SCOPE.md`.
  A new torsion predicate cannot by itself create a historically new affected
  family.

Current main was integrated at `dae09d5f` from
`c5aa7b39bfa30e8cdbd46a158c7cbadaa8be3503`. Its instructions removed the
old missing `experiment.protocol/v1` checker dependency. Earlier reports
remain dated snapshots; their mathematical limitations are unchanged.
The referenced sibling lead-atlas tool and shared lab-contract file are absent
in the available sibling revision, so no atlas review is represented as done.

Exact commands and results are appended in a versioned result note after
the frozen checks run. The old kernel and scope diagrams were inspected;
they make no ell=5 claim and remain unchanged. Canonical curve/route graphs
receive no new edge without a constructed target and checked subgroup map.
The remaining target and novelty obligations are tracked in
`problems/binary-cubic-gluing-target-and-novelty.md`.
