# CT50: exact Richelot bidual equations and the rational no-branching gate

**2026-11-12; [pcc:unverified].** This child of [CT49](../ct49/CT49_NONSPLIT_RICHELOT.md) uses the *actual* F_101 Cpi1/Cpi2/C10/C20 models from [crypto PR #3877](https://github.com/isogeny-labs/crypto/pull/3877). All statements below are producer assertions, not scientifically signed PCC verdicts. The source is independently written standard-library [ct50_dual.py](ct50_dual.py), with retained CT49 Python, JavaScript and C++ primary-input checks.

## Eight exact reverse computations, not just zeta coincidences

Let f=lambda q_0 q_1 q_2 with q_i monic quadratics defined in a cubic extension, and let Delta be the determinant of their constant/linear/quadratic coefficient rows. Define the cyclic Richelot brackets h_i=q'_(i+1)q_(i+2)-q_(i+1)q'_(i+2) and H=prod(h_i)/(lambda Delta^3), with Delta nonzero.

The following **universal polynomial identities** hold over any field of odd characteristic (the rows of h are a signed/scaled adjugate of the rows of q):

- det(h_0,h_1,h_2) = **-2 Delta^2**.
- bracket(h_(i+1),h_(i+2)) = **-2 Delta q_i**.
- Reapplying the exact same normalized codomain recipe with lambda_hat = 1/(lambda Delta^3) returns **f itself, coefficient by coefficient**, not merely an unspecified quadratic twist. All identities can be checked by expanding the three quadratic coefficient rows; no zeta/point-count heuristic enters.

The independent F_101^3 code constructs all eight q triples, computes both bracket rounds, checks the two identities in the full cubic field, and verifies the EXACT seven original F_101 coefficients after two rounds. It rejects the zero-determinant even matching (shift zero) and an intentionally wrong bidual determinant exponent (eight negative controls). Its first forward targets are independently reproduced by CT49's separate JS and Python programs.

| Source | First shift Delta | Second shift Delta | Both reverse determinants | Bidual |
| --- | ---: | ---: | ---: | --- |
| Cpi1 | 50 | 51 | 50 | exactly Cpi1 |
| Cpi2 | 81 | 20 | 8 | exactly Cpi2 |
| C10 | 73 | 28 | 48 | exactly C10 |
| C20 | 34 | 67 | 11 | exactly C20 |

The exact full target coefficients are pinned by CT49. In this CT50 computation **no square-root or curve twist was selected to force the source to return**. [pcc:unverified]

## Rational Richelot graph has four forced-return leaves

The four source sextics have Frobenius permutation 3+3; each admits three Frobenius-stable perfect matchings, one degenerate and two nondegenerate. Each new target is an irreducible sextic over F_101, hence its six branch points form a single Frobenius 6-cycle. A Galois-stable (2,2)-kernel corresponds to a stable perfect matching of the six branch points. A 6-cycle has **exactly one** such matching: (0,3), (1,4), (2,5) in cycle coordinates. The three target bracket factors h_i represent this unique kernel, and the reverse codomain returns the original source by the explicit double computation.

Therefore, **within the F_101-rational (2,2)-Richelot graph**, each of the four new target curve classes is a forced-return leaf: it has one outgoing rational maximal-isotropic 2-kernel, the dual of the incoming edge. It does not offer an independent second rational Richelot step. The two shift representatives per source are isomorphic via x -> -x; CT49's exhaustive PGL2 control distinguishes the four target classes. This does not prohibit (7,7), higher-degree, extension-field, or non-Richelot transfers. [pcc:unverified]

## Rational discrete logarithms: exact preservation, no cost advantage

CT49 independently enumerated N1=120 and N2=10436 on each new target and source; the induced Jacobian order is **12317=109*113**. The group is cyclic because that order is squarefree, and has no nonidentity rational 2-torsion. Each nondegenerate F_101-rational Richelot correspondence gives a degree-four isogeny phi with geometric kernel of order four, but its restriction to the two rational Jacobian groups is **bijective**, since gcd(4,12317)=1. The standard dual-isogeny identity is dual(phi) o phi = [2]. Thus, with the correct correspondence sign/orientation, the rational inverse is

    phi^(-1) = [6159] o dual(phi)   (mod 12317),

because 2*6159=12318=1 (mod 12317). Every subgroup of order 109 or 113 and every DLP scalar is preserved by phi. This is a *mathematical preservation/inverse certificate conditional on the classical Richelot correspondence*, not an executable full-Jacobian map or a solving-cost result. A wrong choice of sign for the dual evaluator must fail its [2] test, not be silently accepted. [pcc:unverified]

## Reproduction and bounded controls

    python3 -B experiments/chained-transfer-reference/ct50/ct50_dual.py
    python3 -O -B experiments/chained-transfer-reference/ct50/ct50_dual.py
    node experiments/chained-transfer-reference/ct49/ct49_richelot.js
    python3 -B experiments/chained-transfer-reference/ct49/ct49_branch_audit.py

Local Python normal and -O runs yielded identical eight bidual lines, all matching and mutation checks passed. The scoped CI must be checked at the exact branch head before recording an Actions receipt. These do not make a valid PCC science signature. [pcc:unverified]

## Obligations, failures, and cost gate

- **Still open:** the actual source-to-target morphism on generic *nonmonic* Mumford divisors, its extension/nonsplit/ramified/infinity cases, all 12,317 rational classes, group homomorphism and dual composition [2] in both directions, and native 4-torsion orientation against #3877. The present script evaluates **equations**, not divisor class images.
- **Still open:** complete cold construction + map + recovery + solver cost, matched optimized rho and best index-calculus baselines, accepted EKS Spot admission/S3 access, and independent PCC signing. Do not enter a benchmark ledger or claim a speedup.
- **Controls:** zero-determinant stable matching rejected for all sources; wrong reverse scaling exponent rejected for all eight shifts; 3+3 and 6-cycle stable-kernel count separately recomputed.
- **Next discriminator:** adapt the existing pinned independent `nonsplit_map.rs` + balanced/nonmonic Cantor implementation on these exact eight inputs; independently compare 12,317 outputs, random additions, Ramified/Weierstrass support, dual norm and all exceptional charts. A mismatch is a correspondence defect, not proof of an algebraic obstruction. Freeze cost protocol *after* correctness and live budget admission.

**Sources checked:** crypto #3877 partial-Frobenius report and exact model tables, cryptanalysis #1511 CT49, cryptanalysis existing `SHIFTED109.md` full-rational Richelot precedent, and standard Richelot dual theory in [Magma handbook](https://magma.maths.usyd.edu.au/magma/handbook/text/1615) and [Dokchitser et al. on Richelot dual curves](https://londmathsoc.onlinelibrary.wiley.com/doi/full/10.1112/plms.12545). Shared research-KB MCP and locked lead atlas were unavailable in the current connected runtime; no prior-art absence claim. [pcc:unverified]

See editable [DOT graph](ct50-return.dot) and [rendered SVG](ct50-return.svg) for the four forced-return target leaves. No paid compute, no merge-gate override, no frozen evidence or ledger edit.

## Universal independent symbolic proof oracle

The second checker, [ct50_symbolic.py](ct50_symbolic.py), uses a dependency-free sparse integer-polynomial ring in **six independent variables** (the three monic quadratics' linear and constant coefficients), not the specific F_101 models or the cubic-field implementation. It expands both sides and checks that all coefficients vanish over **Z**, proving the universal identities before reduction to any odd characteristic. It independently rejects sign-mutant identities, and the scoped workflow checks normal and `-O` output parity. This separates the general algebraic identity from the eight finite-field fixture computations. It still does **not** prove the divisor-level dual composition [2] without the classical Richelot theorem and independently evaluated correspondence. [pcc:unverified]
