---
title: "A published-descent baseline for full-degree binary coefficients"
date: "2026-10-24"
geometry: margin=24mm
fontsize: 10pt
---

Classification: **derived corollary of published work**, with a Rust parameter
checker. This is not a new vulnerable family, a publication-novel theorem, a
complete attack, or a cost obstruction. It explains a baseline that a future
novelty claim must distinguish from a useful low-genus or low-cost descent.

## Request and current evidence

| Requirement | Status |
|:--|:--|
| Identify a previously unrecognized affected source family or criterion | Not established. The five earlier families already have higher-genus Hess descents. |
| Supply a proof | The inclusion corollary below is proved from an elementary trace lemma and Hess's Theorems 11, 12 and 14. Its ingredients and construction are prior work. |
| Lower total cost than GHS/gGHS, or a broad cost obstruction | Not established. No construction/transfer/solve cost comparison is made here. |
| Rust implementation in the cryptanalysis repo | Completed by merged PR [1018](https://github.com/aburan28/cryptanalysis/pull/1018). The new checker is Rust too. |
| Continue the pending exploration sweep | Still open: 355 denominator jobs remain. No fresh campaign data is collected in this change. |
| Keep prime fields and Koblitz controls in their proper scope | Relative degree one is excluded; proper-relative-subfield b, including b=1, is excluded from this corollary's assertion. |

The owner's clarification remains in force: beating Pollard rho is not the
acceptance gate for identifying a new affected family. Conversely, an
unimplemented cost comparison is not filled in with a genus comparison.

## A short trace lemma

**Lemma (derived).** Let $K=\mathbf F_{q^N}$ over $k=\mathbf F_q$, with $N\ge3$,
and put $U=\ker\operatorname{Tr}_{K/k}$. For every $s\ne0$ there is a
$\gamma\in U\setminus\{0\}$ such that
$\operatorname{Tr}_{K/k}(s/\gamma)\ne0$.

**Proof.** Otherwise all $q^{N-1}-1$ nonzero roots of

$$L(X)=\sum_{i=0}^{N-1}X^{q^i}$$

would be roots of

$$P_s(X)=\sum_{i=0}^{N-1}s^{q^i}X^{q^{N-1}-q^i}.$$

Both $P_s$ and $L/X$ have degree $q^{N-1}-1$, and $L/X$ has exactly those
distinct roots. Thus $P_s=sL/X$. But the coefficient of
$X^{q^{N-1}-q}$ on the left is $s^q\ne0$. That exponent is positive and
divisible by $q$, whereas every positive exponent in $L/X$ is congruent to
$-1$ modulo $q$. This is a contradiction. $\square$

The $N=2$ case is intentionally separate. In characteristic two,
$U=k$; if $s\notin k$, take $\gamma=1$, so
$\operatorname{Tr}_{K/k}(s/\gamma)\ne0$. The lemma is not asserted for
arbitrary nonzero $s\in k$ in this quadratic case.

## Published-construction inclusion

**Corollary (derived from Hess).** Let $k=\mathbf F_q$ have characteristic
two, $K=\mathbf F_{q^N}$ with $N\ge2$, and

$$E/K:\quad Y^2+XY=X^3+aX^2+b,\qquad b\ne0.$$

Suppose $b$ has full relative degree $N$ over $k$. There is a curve $C_0/k$
obtained by Hess's generalized split-pole construction with

$$g(C_0)\le 2^N-2$$

and a homomorphism

$$\Phi:E(K)\longrightarrow J_{C_0}(k)$$

whose kernel is annihilated by a power of two. In particular, $\Phi$ is
injective on every odd-prime-order subgroup. This applies to either
absolute-trace class of $a$. The target need not be hyperelliptic.

**Proof.** Set $s=\sqrt b$. Choose $\gamma$ by the lemma, or take
$\gamma=1$ in the quadratic case, and put $\beta=s/\gamma$. Then

$$\gamma\beta=s,\qquad
\operatorname{Tr}_{K/k}(\gamma)=0,\qquad
\operatorname{Tr}_{K/k}(\beta)\ne0.$$

The standard Artin--Schreier transformation, followed by scaling its rational
coordinate, identifies the elliptic function field with

$$w^2+w=\gamma/x+a+\beta x.$$

Write $\sigma(z)=z^q$, let $M_\gamma,M_\beta\in\mathbf F_2[T]$ be the
minimal annihilators under $\sigma$, and let
$M=\operatorname{lcm}(M_\gamma,M_\beta)$, with degrees $u,v,m$ respectively.
All annihilators divide $T^N+1$, so $m\le N$. The zero trace of $\gamma$
gives $M_\gamma\mid(1+T+\cdots+T^{N-1})$, hence $u\le N-1$.
Applying relative trace to $M_\beta(\sigma)\beta=0$ gives
$M_\beta(1)\operatorname{Tr}_{K/k}(\beta)=0$. Thus $T+1$ divides
$M_\beta$, and consequently $M$.

It follows that
$\operatorname{Tr}_{K/\mathbf F_2}(M(\sigma)a)=
M(1)\operatorname{Tr}_{K/\mathbf F_2}(a)=0$. Hess's exact-constant condition
holds for both trace classes of $a$, the function-field degree parameter is
$m$, and Theorem 11 gives the Frobenius lift because $\gamma$ has zero
relative trace. Theorem 12 gives

$$g(C_0)=2^m-2^{m-u}-2^{m-v}+1.$$

For $m=N$, use $u\le N-1$ and $v\le N$ to obtain $g(C_0)\le2^N-2$.
For $m<N$, the bound $g(C_0)\le2^m-1\le2^{N-1}-1$ suffices.

Finally, if $\sigma^j$ fixes both $\gamma$ and $\beta$, it fixes
$b=(\gamma\beta)^2$. Full relative degree of $b$ therefore forces the
coefficient-pair period $s(h)$ in Hess's Theorem 14 to equal $N$.
That theorem bounds the kernel of the norm-after-conorm map by
$E(K)[2^{m-1}]$. Its restriction to an odd-prime-order subgroup is injective.
$\square$

## What this changes in the novelty test

For this full-relative-degree class, merely finding a prime-subgroup-preserving
descent at some genus cannot establish the first connection with GHS-like
descent: it is already contained in the published framework. This includes
both twists, after a suitable split-pole presentation. A canonical
Frobenius-lift failure does not exclude generalized descent.

The bound is an existence **upper** bound, not a lower bound or an optimal
genus. It gives 2, 6, 30, 2046 and 8190 for relative degrees 2, 3, 5, 11
and 13. Those numbers do not estimate construction, transfer or solve cost.
They do not rule out a new useful low-genus recognition criterion, a new
explicit correspondence, or a lower-cost attack. They do not settle the
publication priority of the earlier degree-eight/nine maps.

![Symbolic inclusion and the outstanding quantitative gate. No concrete curve IDs or measured attack are represented.](scope-figures/inclusion.pdf)

The editable diagram is [inclusion.dot](scope-figures/inclusion.dot), with
an [SVG rendering](scope-figures/inclusion.svg). It adds no curve or isogeny
edge to a canonical graph.

## Rust checker and evidence boundary

`examples/hess_scope.rs` constructs one $(\gamma,\beta)$ witness for a
specified full-degree coefficient. It checks the product, relative traces,
annihilator relations, exact-constant condition and full joint period with
the fast field and separate raw-polynomial arithmetic. It returns the genus
of that published witness, not the minimum over presentations.

```sh
cargo run --release --locked \
  --manifest-path experiments/ghs-sweeper/Cargo.toml \
  --example hess_scope -- \
  --base-degree 1 --relative-degree 3 --a 1 --b 2
cargo test --release --locked \
  --manifest-path experiments/ghs-sweeper/Cargo.toml \
  --example hess_scope
```

The checker does not instantiate $C_0$, its Jacobian, a subgroup generator,
or a planted log. Curve and IC candidate IDs remain null. The injectivity
statement above is a proof using the published theorem, not a measured
transfer claim. No catalogue entry is created.

The fixed software unit controls check the quadratic construction in both
constant-trace classes, the explicit cubic witness $(\gamma,\beta)=(2,3)$
in $\mathbf F_8$, an even-degree case, the historical trace-one coefficient
$b=166$ in $\mathbf F_{1024}$, and rejection of singular/trivial/subfield
inputs. These are software correctness assertions, not a new parameter
sweep, a natural-yield estimate, or an IC benchmark.

![Exact genus upper bound from the corollary, not an optimized genus or a cost measurement. Twelve integer arguments N=2 through 13; no empirical sampling uncertainty.](scope-figures/genus-bound.pdf)

The plot's [integer values](scope-figures/genus-bound.csv) are direct evaluations
of $2^N-2$. The renderer is `render_hess_scope.py`. These are derived arithmetic,
not experimental search rows. The [software-check contract](PROOF_CHECKS.md)
fixes the unit assertions and the figure inputs before their execution.

## Remaining blockers and graph audit

The 355 pending exploration jobs have not been replaced or discharged by this
inclusion proof. The updated repository policy requires a frozen
`experiment.protocol/v1` before new campaign data. Its pointer requires
`crypto-autoresearcher` on `origin/main`. At inspected commit
`dcfdd16cdf7783a059ca1e6e4cc5efbf77434b7b`, the canonical checker,
protocol/export schemas and skill are absent. No substitute schema is invented
and no new campaign is run under a retroactive protocol. The missing canonical
location has been requested while this proof and code verification proceed.

The checked graph sources are the cover infrastructure's source-parity table,
the previous GHS audit, and the retained branch-orbit/prior-art report. Their
curves, transfers and claims are unchanged. The curve registry and isogeny
routes receive no new entry: this is a symbolic inclusion in a published
construction, with no instantiated new curve or verified new route.

## Sources and claim labels

- **Primary, read:** F. Hess, *Generalising the GHS Attack on the Elliptic
  Curve Discrete Logarithm Problem*, LMS J. Comput. Math. 7 (2004),
  pp. 174--177, equation (10), Theorems 11, 12 and 14:
  <https://doi.org/10.1112/S146115700000108X>. The retained primary PDF and
  extracted text were checked; a source hash receipt accompanies this report.
- **Prior local evidence, read:** [prior-art audit](reference/prototype-prior-art.md)
  and [Hess presentation audit](reference/prototype-hess-audit.json). These
  already identify valid higher-genus presentations for the five old families.
- **Theorem/identity:** the trace lemma and inclusion corollary are derived
  as above; no publication-novelty claim is made for either.
- **Exact software checks:** the Rust unit log and source hashes accompany
  this report; they certify the stated fixed inputs, not a new family.
- **Not established:** a novel affected source family, explicit new cover,
  planted-log transfer, lower total cost, calibrated speedup, or a cost
  impossibility theorem.
