# The D=-2631 Hecke relation rank splits 240/240 under Fricke

For the saved `D_K=-2631, f=6, p=23743` class, the global Fricke involution
`W_11(P)=T-P` pairs all 768 points and all 576 complete Hecke rows. In
the corresponding `+` and `−` point-pair coordinates, the relation matrix
has **rank 240 in each 384-column sector**. The 54 independently certified
floor witnesses split **27/27**. Thus the involution exposes two equal
144-dimensional relation kernels, while pairing the existing floor
certificates. Every saved Fricke-transformed relation is already present
as a row.

| Exact quantity | `+` sector | `−` sector | Total |
| --- | ---: | ---: | ---: |
| Paired column coordinates | 384 | 384 | 768 |
| Relation rank over `QQ` | 240 | 240 | 480 |
| Relation column nullity | 144 | 144 | 288 |
| Floor-witness rank over `QQ` | 27 | 27 | 54 |

The [protocol](PROTOCOL.md) fixed the three source artifacts and the rank
questions before calculation. The [Sage calculation](ranks.json) checks
their SHA-256 digests, the fixed-point-free point involution, and all 576
row transports; it obtains identical ranks over `QQ`, `F_23`, and
`F_1000000007`. The [independent integer replay](validation.json) rebuilds
both projected matrices and computes the two modular ranks with a separate
sparse elimination implementation. The [runtime receipt](runtime-info.json),
stdout, and stderr preserve the execution context. This is an exact
relation-matrix diagnostic with `candidate_id: null` and `timing_claim: null`.

**Proof map.** For each orbit `{i,W(i)}`, the coordinate change is
`(r_i,r_W(i)) ↦ (r_i+r_W(i),r_i-r_W(i))`. Its inverse divides the sum and
difference by two. The [Lean module](formal/FrickeProjection.lean) checks
both rational reconstruction identities under Lean `v4.35.0-rc4` and
Mathlib `021c46bdd042f67b538b9f9871d556a93713a9a9`;
[`#print axioms`](formal/build-output.txt) reports `propext`,
`Classical.choice`, and `Quot.sound`. Invariance of the saved row space is
verified by the 576 row transports in the input scan and checked again by
`rank.py`. Invariant subspaces split over `QQ` because two is invertible;
the projected rank sum 480 independently matches the full rational rank
from [PR #1193](https://github.com/isogeny-labs/cryptanalysis/pull/1193).
The actual 768-column ranks and the moduli-to-coordinate map are certified
by the Sage/integer artifacts and the global proof in
[PR #1195](https://github.com/isogeny-labs/cryptanalysis/pull/1195),
respectively; the Lean module formalizes the pair-coordinate step, not
those complete objects. `lean4checker --fresh` was unavailable on this host.

The next structural question is which non-Fricke relation families can
connect the 288-dimensional kernel to independently known logs, with their
source, verification, and cost accounted for on the same class.
