---
title: "Binary cubic descent: explicit quartics and a CM exclusion test"
date: 2026-10-25
geometry: margin=0.8in
fontsize: 10pt
---

The Rust census finds **33 smooth plane quartics over F8** with Jacobian
Weil polynomial $T^6-tT^3+512$, for $t=\pm35$. These are two source trace
classes absent from the earlier local spectral journal. They are **not
established globally novel affected curves**: the quartic family is published,
an evaluated source-to-Jacobian map is missing, and publication priority of
the derived criterion remains open. Beating rho is not the acceptance gate.

## Exact census and controls

The source model is $E_a:y^2+xy=x^3+ax^2+59$ over
$K=\mathbb F_2[z]/(z^9+z+1)$, modulus 515, with a=0 or 1.
The coefficient 59 has full absolute degree nine. The base field is
$k=\mathbb F_2[u]/(u^3+u+1)$, modulus 11. Integers denote power-basis
bitmasks; they are not integer field scalars. No subgroup generator has
been selected, so no EC1 subgroup identity or verified ISO1 edge is assigned.

We enumerate the published ordinary O3 normal family of
[Nart--Ritzenthaler, section 1.4](https://arxiv.org/abs/math/0312366v2).
Write $Q=ax^2+by^2+cz^2+dxy+eyz+fzx$. Here s=2, t=6 and the model is

$$Q^2=(x+y+z)\{2(x^3+y^3+z^3)+xyz
 +7(xy^2+x^2z+yz^2)+5(xz^2+x^2y+y^2z)\}.$$

The paper's three nonsingularity conditions and rational C3 coefficient
action are applied exactly. In particular $Q(1,1,1)\ne1$ is required.
The norm expansion is checked on all 512 base-field triples. Smoothness
conditions are compared with the seven split Fano points on 64 binary
coefficient vectors. Four fixed models check the optimized point counter
against a raw polynomial-arithmetic counter with a different projective
normalization. All 33 retained targets are independently replayed over F8,
F64 and F512; the two displayed examples also have standalone CLI receipts.
This is a second arithmetic path within the same Rust implementation,
not an external implementation review.

| Stage | Exact number |
|---|---:|
| All coefficient vectors | 262,144 |
| Smooth vectors | 228,481 |
| Rational C3 orbit representatives | 76,189 |
| Representatives with N1=9 | 21,652 |
| Also N2=65 | 3,799 |
| Trace -35 targets | 30 |
| Trace +35 targets | 3 |

![Exact finite census. Bars show counts, with a logarithmic axis; no sampling uncertainty or timing claim.](quartic-cubic-figures/census.pdf){width=95%}

For genus three, the first three point counts determine the Weil polynomial
by Newton identities. With these targets it equals the restriction polynomial
of the displayed source. Tate's theorem therefore gives an isogeny-class
relation. It does not supply an efficient homomorphism or a transferred log.

| Source | Example Q coefficient vector | N1,N2,N3 | Source and Jacobian order |
|---|---|---|---|
| a=0, trace -35 | (5,7,7,6,0,0) | 9,65,618 | 548 = 4 times 137 |
| a=1, trace +35 | (3,7,7,4,4,0) | 9,65,408 | 478 = 2 times 239 |

The JSON [standalone replays](quartic-cubic-checks/verify-commands.json)
include the fully expanded quartic polynomials, field embeddings and counts.
These coefficients identify equations, not selected prime-subgroup instances.

## Geometric automorphisms separate the targets

Conjugating to the split Fano-bitangent model reduces the full geometric
automorphism search to all 168 elements of GL3(F2). Every retained matrix is
replayed in the original coordinates by polynomial substitution up to scalar;
group closure and Frobenius closure are checked separately.

Of 33 targets, **27 have trivial geometric automorphism group**. The other
six, all with trace -35, have a V4 group stable under Frobenius, cycling its
three involutions. Their parameter codes are 13504, 28267, 60803, 74777,
149517 and 224622. This is the published degree-two elliptic-quotient route
of [Nart--Ritzenthaler, 2009](https://arxiv.org/abs/0905.0546), not a new
construction. Quotient maps have not been evaluated here. All three trace
+35 targets have trivial geometric automorphism group, hence admit no
separable degree-two elliptic quotient. This does not exclude higher-degree
maps or establish a new attack.

## A derived sufficient CM test

The [full written proof](CUBIC_CM_DISCRIMINANT.md) gives the following test.
For a simple ordinary cubic restriction, a rational transverse isotropic
ell-kernel, and geometric CM field $\mathbb Q(\sqrt{-\delta})$ with delta
positive squarefree, decomposability forces positive sorted a,b,c of sum ell,
whose pair products are degrees of inter-factor isogenies, and

$$H=2\ell abc-(ab)^2-(ac)^2-(bc)^2=\delta z^2,\quad z\in\mathbb Z.$$

For traces +/-35 the fundamental Frobenius discriminant is -823. The written
ordinary CM/Tate-module argument forces inter-factor degrees to be represented
by $8x^2+3xy+26y^2$. At ell=53 only (1,26,26), (8,8,37), (8,13,32) survive
the degree test. The first has H<0; the other two have H=71,680 and 103,360,
neither divisible by 823. Thus the written criterion gives geometric
indecomposability for every such transverse 53-quotient. Arithmetic Torelli
selects a genus-three Jacobian for one source twist. Its degree is $53^3$,
coprime to the source primes 137 and 239. The abstract torsion certificates
check all $53^3$ combinations per source trace, but contain no E[53] points.

This quotient has **not** been identified with any of the 33 explicit
quartics. Neither the arithmetic twist nor a quotient equation/map is
selected by this argument. The prime scan covers only ell=2 mod 3 up to 53;
53 is not claimed minimal. The sum-37 control (8,13,16) has H=823 times 64
and correctly passes this necessary arithmetic condition.

![The computed equations and the abstract quotient are separate evidence. Dashed links denote missing identifications or evaluated maps.](quartic-cubic-figures/transfer-scope.pdf){width=95%}

The new Lean project proves four named arithmetic statements, with a
transitive audit of five theorems including a generated equation lemma.
Two named statements use no axioms; the other two use only propext,
Classical.choice and Quot.sound. The [proof map](cm-formal/README.md)
explicitly leaves the CM degree form, unbounded witness bounds, polarized
geometry, simplicity and Torelli outside the formal proof. No sorry,
custom claim axiom or native-decision trust is used. The repository gate
passes on 96 research sources, five freshly rebuilt and 91 archive-bound.

## Novelty, evidence and next step

| Requested result | Current evidence |
|---|---|
| New recognition criterion with proof | Derived sufficient CM test; priority unresolved |
| New globally affected source family | Not established; only two new local trace classes |
| Explicit target equation | 33 verified spectral targets in a published family |
| Explicit DLP transfer and recovered planted log | Missing |
| Lower genus or total attack cost than GHS/gGHS | Unmeasured; no claim |

The full Tian 2023 journal priority comparison remains unfinished. Published
Hess generalized descent already gives broad existence for these sources.
The finite census is an observation, the CM implication is a written
derivation, and the source-to-target map is an implementation gap. None
is promoted to a novel vulnerability by absence from a local journal.
The [active problem](../../problems/binary-cubic-gluing-target-and-novelty.md)
specifies the next discriminating construction: identify a trace +35 target
as the polarized quotient (or construct the actual target), evaluate the
map on a declared r=239 subgroup, and independently recover a planted log.

Prospective contracts are `QUARTIC_CUBIC_CHECKS.md`,
`QUARTIC_AUTOMORPHISM_CHECKS.md`, `CUBIC_CM_CHECKS.md` and
`CUBIC_CM_DISCRIMINANT_CHECKS.md`. Code was frozen before each scientific
run. Source commits, commands, raw outputs, hashes, failures and version
transitions are in `quartic-cubic-checks/artifact-manifest.json`.
All 48 Rust release tests and strict all-target Clippy pass. An earlier
Clippy attempt failed on three style diagnostics; the corrected attempt is
retained alongside it. The first corpus replay failed because the audit
also found a generated equation theorem; the expectation was corrected to
cover it, and the second replay passed. These are validation corrections,
not changed scientific outcomes. Wall times are execution receipts only,
without an isolated-host claim, cost calibration or rho comparison.

Canonical sources checked: `ic-candidate-catalog/curves.yaml`,
`ic-candidate-catalog/isogeny_routes.json`, `volcano-ic/figures/` and the
existing GHS scope/kernel/cubic figures. No verified curve-graph edge or
weak-curve catalogue entry is added: no map or subgroup transport exists.
The earlier five-gluing overlap report remains valid for its separate
12-class scope. Frozen evidence is preserved; mutable global gates and
the problem record receive explicit old/new hash transitions.
