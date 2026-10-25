---
title: "Coordinate certificates for the binary cubic 3-gluing kernel"
date: "2026-10-25"
geometry: margin=24mm
fontsize: 10pt
---

**Status: construction engineering and exact kernel verification.**
This continues the [derived criterion](THREE_GLUING.md); the older report
and its evidence remain a dated, immutable snapshot. The present work
addresses actual source-torsion coordinates. A novel affected family and
an explicit genus-three discrete-log transfer remain unestablished.
Beating Pollard rho is not an acceptance gate.

| Requirement | Current status |
|:--|:--|
| Native Rust in the cryptanalysis repository | Complete for the supported coordinate kernel and replay checker. |
| A novel affected family or identifying theorem | Not established; the fixed source trace classes also occur in local history. |
| Explicit transfer and independently verified planted log | Target reconstruction, twist selection and isogeny evaluation remain open. |
| Original pending campaign | 355 jobs remain pending; canonical protocol admission remains blocked. |

## Source review and question

Tian's [2020 preprint](https://arxiv.org/abs/2012.07173), sections 2.1
and 3, describes Frobenius on the restriction as
$(R_0,R_1,R_2)\mapsto(R_2^q,R_0^q,R_1^q)$ and uses the product Weil
pairing. These definitions apply to the kernel step. Its reconstruction
uses ordinary two-torsion and odd-characteristic quartic formulae, so it
does not supply the missing binary target here. The full
[2023 journal text](https://doi.org/10.1007/s00145-023-09474-2) remains
unread; no priority exclusion is inferred from the shorter preprint.

The pairing calculation follows [Enge, section 3, equation (7)](https://arxiv.org/abs/1301.5520):
use functions normalized at infinity and retain the sign convention.
In characteristic two the sign is one. For a nonzero point of order
three, its tangent line has divisor $3(P)-3(O)$, so a single tangent
evaluation replaces a general Miller loop. Normalization and the fact
that the points really have order three are checked preconditions.

## Coordinates over one quadratic extension

Let $d\ge3$ be odd, $n=3d$, $K=\mathbf F_{2^n}$, and
$E:y^2+xy=x^3+ax^2+b$. Assume the existing root criterion holds and
retain the full-absolute-degree condition on $b$. The new checker
supports $d=3,5$ within the existing field implementation's limits.
Only the fixed $d=3$ certificates were executed here; the $d=5$ path is
implemented but unverified in this continuation.

Set $L=K[u]/(u^2+u+1)$. It is a field because
$\operatorname{Tr}_{K/\mathbf F_2}(1)=1$. Encode a scalar as a pair
$(s,t)$ meaning $s+tu$. Multiplication and conjugation are

$$ (s+tu)(v+wu)=(sv+tw)+(sw+tv+tw)u,
\qquad \overline{s+tu}=(s+t)+tu. $$

The norm is $s^2+st+t^2$, giving inversion through $K$. All field
identities are replayed with separate raw-polynomial multiplication.

For each of the two division roots $x$, the identity
$b=x^4+x^3$ reduces the equation for $z=y/x$ to

$$z^2+z=x^2+a.$$

For $h\in K$, its ordinary half-trace $H(h)$ satisfies
$H(h)^2+H(h)=h+\operatorname{Tr}(h)$. Thus
$z=H(x^2+a)+\operatorname{Tr}(x^2+a)u$ solves the equation over $L$.
The $2^n$-Frobenius fixes one resulting torsion line and negates the
other. Choose nonzero generators $P,Q$ on those respective lines and
set $P_i=P^{q^i}$ and $Q_i=Q^{q^i}$.

## A kernel with actual points

The previously abstract generators now become

$$U=(P_0,P_1,P_2),\qquad V=(Q_0,Q_1,O),\qquad W=(O,Q_1,Q_2).$$

The certificate contains these three tuples, their 27 combinations,
the source coefficients defining the conjugate curves and the numerical pairings. Replay checks
that every point lies on its declared factor, has order dividing three,
and that all 729 ordered additions and pairings stay in the kernel and
give product pairing one, respectively. It also checks Frobenius
stability and the three zero coordinate intersections.

This is stronger evidence for the kernel than a spectral or dimension
match. It is still a certificate for a subgroup in the source product,
not an evaluated map to a Jacobian. The kernel's three individually
rational points must be distinguished from its 27 geometric points.

![The checked kernel and the outstanding target/map steps.](kernel-figures/certificate.pdf)

## Verification boundary and remaining work

The fixed inputs and rejection controls were specified in
[KERNEL_CHECKS.md](KERNEL_CHECKS.md) before their new assertions ran.
The native example generates or verifies serialized coordinate witnesses;
it recomputes its checks instead of trusting stored success flags.

```sh
cargo run --release --locked \
  --manifest-path experiments/ghs-sweeper/Cargo.toml \
  --example three_gluing_kernel -- generate --base-degree 3 --a 0 --b 24
cargo run --release --locked \
  --manifest-path experiments/ghs-sweeper/Cargo.toml \
  --example three_gluing_kernel -- verify \
  --certificate experiments/ghs-sweeper/kernel-checks/certificate-a0.json
```

**Exact fixed-control results:** all 34 release all-target tests pass,
including five coordinate-kernel tests. Formatting and all-target Clippy
with warnings denied pass. Both serialized positive certificates replay;
a deliberately corrupted field binding is rejected by the CLI.

With $u^2+u+1=0$, the actual source bases are:

| Source constant | $P$, fixed by $2^9$-Frobenius | $Q$, negated by that Frobenius | $e_3(P,Q)$ |
|:--|:--|:--|:--|
| $a=0$ | $(2,152)$ | $(75,316+75u)$ | $u$ |
| $a=1$ | $(75,375)$ | $(2,154+2u)$ | $1+u$ |

For each positive certificate, all 729 product pairings equal one, the
three coordinate-intersection sizes are $(1,1,1)$, and exactly three kernel
points are individually rational. The decomposable negative control is
isotropic but has intersection sizes $(3,3,3)$; the transverse negative
control has 432 nontrivial pairings and also fails Frobenius stability.
These are exact results on fixed subgroups, not rates on a curve sample.

![Exact subgroup checks. Three fixed subgroups, 729 ordered pairs per subgroup; no sampling uncertainty or cost comparison.](kernel-figures/control-checks.pdf)

The [unit output](kernel-checks/all-targets-attempt-2.txt),
[positive certificate](kernel-checks/certificate-a0.json) and
[second twist](kernel-checks/certificate-a1.json) retain the coordinates
and predicates. The fast and raw paths share the group-law formulas and
control flow; the separate field arithmetic and the two pairing formulas
do not constitute an external independent review of the complete checker.

The `twist` command transports a certificate through the quadratic-field
isomorphism $\phi(x,y)=(x,y+ux)$, sending $a$ to $a+1$. This supplies a
[third certificate](kernel-checks/transported-twist-a1.json), for the
quadratic twist of the **same** quotient kernel. The separately generated
$a=1$ kernel above need not be that kernel. The fixed tests verify all 729
group-law identities for $\phi$, $F\phi=-\phi F$ on all 27 points,
and round-trip transport through $\phi^2=1$, with both field algorithms.
This is an isomorphism over $L$, not a discrete-log transfer over $K$;
it still does not determine the arithmetic Torelli obstruction.

## Historical overlap is present

An exact order check on the same inputs gives $\#E_0(K)=480$,
$\#E_1(K)=546$, hence source traces $33,-33$. Both traces were already
recorded by the completed genus-three smoke search. The extracted
[historical rows](kernel-checks/local-prior-overlap.json) bind the old
models, source representatives, exact traces and raw-verification flags.
They are spectral/source matches with no explicit map. Thus these controls
do not introduce a new local source isogeny class. This does not settle
publication priority of the criterion or the explicit correspondence.

The old genus-three targets have point counts $(9,65,414)$ and
$(9,65,612)$ over $\mathbf F_{8^e}$, $e=1,2,3$, respectively. No target
isogeny between either of those curves and the new quotient is constructed
here, and their existence does not select the arithmetic Torelli twist
of the particular quotient certified above.

Publication priority of the binary application is still open. Selecting
the source twist requires the quotient's arithmetic Torelli obstruction;
knowing coordinates of the isogeny kernel does not resolve it. Binary
quotient reconstruction and explicit isogeny evaluation remain to be
implemented before a planted-log transfer can be tested. All attack curve
IDs, subgroup orders, IC IDs and construction/transfer/solve/rho costs
remain null. No catalogue row or verified curve-route edge is added.

The larger campaign is still pending. The required canonical protocol
tool was absent at inspected `crypto-autoresearcher origin/main`
`e5f46a59516ceca68828e7fc2fcab2e8fc0b12d7`. The local pointer explicitly
requires that branch: “Use a sibling checkout at `../crypto-autoresearcher`
on `origin/main`; never copy the tool here.” Its
[SKILL.md](https://github.com/aburan28/cryptanalysis/blob/c273e62140071fe4370fbe6946dcb898c95b4eb2/.agents/skills/experiment-protocol/SKILL.md)
is the source of this campaign restriction. No unmerged replacement is substituted. This
certificate work is a fixed mathematical/software check, not a new sweep
or a comparative experiment.

Graph audit: the existing GHS report, branch-orbit report, infrastructure
source-parity table, curve registry and route index retain their prior
meaning. The new diagram records a kernel certificate and unimplemented
obligations; it is not a new isogeny edge between exact curve IDs.
