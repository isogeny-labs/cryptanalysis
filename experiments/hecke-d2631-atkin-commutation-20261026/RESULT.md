# An order-five involution commutes with all saved D=-2631 Hecke fibers

On the frozen 768-point `D_K=-2631`, conductor-6 class over `F_23743`, the candidate level-11 involution `W(P)=T-P`, with `T=(16:-61:1)` of order five, is a **fixed-point-free permutation of 384 pairs**. For all 768 points, `j(P)` and `j(W(P))` satisfy the degree-11 classical modular polynomial, and `W` preserves the checked endomorphism conductor. On every one of the **576 complete degree-2/3 Hecke fibers**, `W` carries the entire rational neighbor multiset to the neighbor multiset of `W(P)` and permutes the corresponding saved relation row. The frozen [protocol](PROTOCOL.md) fixed the candidate map and these pass conditions before the scan.

| Pointwise or matrix property | Checked count or result |
| --- | ---: |
| Class points / fixed points of `W` | `768 / 0` |
| Degree-11 modular-polynomial mismatches | `0 / 768` |
| Conductor mismatches | `0 / 768` |
| Complete degree-2 / degree-3 neighbor multisets transported | `384 / 192` |
| Saved relation-row transport mismatches | `0 / 576` |
| Saved affine Atkin–Lehner row mismatches | `0 / 768` |
| Signed cycle-vector action | three two-cycles: `(0 4)(1 2)(3 5)` |
| Degree-3 pair-vector action | 24 two-cycles, up to sign |
| Rank of original plus transported floor witnesses over `QQ` | `54` |

The [checked-Sage scan](scan.json) reconstructs each saved point from [PR #1193](https://github.com/isogeny-labs/cryptanalysis/pull/1193), verifies `5T=0`, computes the classical degree-11 polynomial at every mapped pair, and compares complete degree-2 and degree-3 neighbor **multisets**. It transforms each sparse row by the point permutation and compares it coefficient for coefficient with the saved row whose source is `W(P)`. The 54 floor vectors are transported in the same way; each of the six cycle vectors and 48 pair vectors maps to a recorded vector up to sign. The independent [integer validator](validation.json) replays the 768-column and 576-row permutations, all 768 saved affine rows, the 54 vector actions, and their involution identities directly from the frozen matrices.

The [runtime receipt](runtime-info.json) records the checked Sage build. The bounded [launch](launch.json) exited 0; stdout and stderr are retained. SHA-256 inputs in `scan.json` bind the prior raw matrix, conductor/row audit, floor certificates, and regularized evaluator. This is a pointwise finite-class bridge from the algebraic candidate involution to the actual Hecke rows. Identifying `T-P` uniformly with the moduli-theoretic Atkin–Lehner involution on every finite field remains a separate theorem obligation; the modular-polynomial and row checks establish the identity on this exact saved class.

**Proof map.** In an arbitrary additive commutative group, [AffineTransport.lean](formal/AffineTransport.lean) proves that `Q↦T-Q` preserves both a three-neighbor equation with `a₂=-2` and a four-neighbor equation with `a₃=-1`, provided `5T=0`. The checked module uses Lean `v4.35.0-rc4` and Mathlib revision `021c46bdd042f67b538b9f9871d556a93713a9a9`; [`#print axioms`](formal/build-output.txt) reports only `propext`. The concrete group points, neighbor maps, and row identities are checked by the Sage scan and independent integer replay. A faithful Lean definition of the elliptic-curve Hecke correspondence and its level-11 moduli action is still open. `lean4checker --fresh` was unavailable on this host.

The new structural consequence is that the 54-dimensional floor certificate space in PR #1193 is stable under this measured involution, with six norm-2 cycles paired into three orbits. This result concerns the saved relation matrix and has `candidate_id: null` and `timing_claim: null`.
