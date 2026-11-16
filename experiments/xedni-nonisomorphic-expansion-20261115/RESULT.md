# A third nonisomorphic rank-one lift adds 80 bounded pairs

The frozen extension of the eight-field rank screen found one additional proved rank-one rational lift. At `p=313`, the centered reduction of `5G` is `(-93,-12)`, lying on `E/Q: y²=x³−x+804408`. Checked Sage proves rank one and trivial rational torsion, and verifies that this point is a signed Mordell–Weil generator. Its `j` invariant differs from the base curve's. The two radius-four generator images intersect only at the identity, so their ordered-pair union has **161** elements, up from **81** for the base curve. `XedniNonisomorphicExpansion.pair_union_card_331` proves the exact union count in Lean.

| Frozen screen outcome for `u=4,5` | Cells |
| --- | ---: |
| Rank one proved | 1 |
| Rank two proved | 9 |
| Rank three proved | 4 |
| Exact rank unresolved | 1 |
| Worker timeout at 12 seconds | 1 |

The unresolved cell is `(p,u)=(313,4)` and the timed-out cell is `(547,4)`. Their statuses and captured output remain in `cells/`; neither enters the qualified family. Every completed candidate has a saved exact torsion result and reduction record. The screen adds 16 attempted curves to the preceding 24-candidate screen; the qualified expansion has one new generator proof.

## Complete relation replay at `p=313`

The frozen public target is `Q=17G` in the subgroup of order 331. For every ordered `(t₁,t₂)∈[0,331)²`, set `Rᵢ=Q−tᵢG`. Each of the two qualified rational models tests whether both reduced points have generator coordinates in `[-4,4]`, and then whether `U+2V=O` on that rational curve. The independent Sage audit replays the exact group equations and scalar multiplication for every positive row.

| Model | Membership checks | Admitted distinct relation tests | Rational relations | First relation query |
| --- | ---: | ---: | ---: | ---: |
| Base, reduction generator `G` | 109,561 | 56 | 4 | 4,323 |
| New, reduction generator `5G` | 109,561 | 56 | 4 | 2,340 |
| **Total** | **219,122** | **112** | **8** | **2,340** |

Each model also records 661 identity statuses, 330 duplicate statuses, and 108,514 outside-cap statuses. The new model's four relation hits occur at queries 2,340, 8,950, 12,255, and 108,596. All eight rational relations reduce to the directly testable public equation and independently replay the fixture scalar. The first new-model hit is an index in the fixed lexicographic order; the rank screen, membership work, and failed cells are part of this procedure. These are operation and event counts without a paired wall-time measurement.

## Proof map and checks

| Result | Proof or independent check | Hypotheses and scope |
| --- | --- | --- |
| Exact ordered pair union `161` | `XedniNonisomorphicExpansion.pair_union_card_331` | Images of `[-4,4]` under multiplication by 1 and 5 in `ZMod 331` |
| New curve rank, torsion, generator, good reduction, distinct `j` | Checked Sage worker, generator proof, independent `audit.py` | Exact curve `[-1,804408]` and point `(-93,-12)` |
| All 109,561 query statuses and eight scalar replays | Independent checked-Sage `audit.py` | Frozen target and `(1,2)` vector at `p=313` |

The formal project pins Lean `v4.35.0-rc4` and Mathlib `021c46bdd042f67b538b9f9871d556a93713a9a9`. `lake build ExpansionUnion` passed 3,138 jobs; `#print axioms pair_union_card_331` lists only `propext`, `Classical.choice`, and `Quot.sound`. The source has no proof placeholders or custom research axiom. `lean4checker --fresh` was unavailable on this host. Elliptic-curve rank and generator completeness are checked in Sage rather than Lean, so the formalization of the full arithmetic witness remains partial.

The original screen and its checked relation audit remain intact. This extension tests only `u=4,5` under the same centered-lift law. A next experiment can run an unseen-field screen with the complete curve-selection cost and compare the first rational relation with a direct public-vector search under the same target and resource envelope.

## Reproduce

From the repository root:

```sh
./sage --runtime-info > experiments/xedni-nonisomorphic-expansion-20261115/sage-runtime-info.json
python3 experiments/xedni-nonisomorphic-expansion-20261115/screen.py > experiments/xedni-nonisomorphic-expansion-20261115/result.json 2> experiments/xedni-nonisomorphic-expansion-20261115/screen.stderr
./sage -python experiments/xedni-nonisomorphic-expansion-20261115/generator.py 313 5 -93 -12 804408 > experiments/xedni-nonisomorphic-expansion-20261115/generator.json 2> experiments/xedni-nonisomorphic-expansion-20261115/generator.stderr
python3 experiments/xedni-nonisomorphic-expansion-20261115/relation.py > experiments/xedni-nonisomorphic-expansion-20261115/relation-result.json 2> experiments/xedni-nonisomorphic-expansion-20261115/relation.stderr
./sage -python experiments/xedni-nonisomorphic-expansion-20261115/audit.py > experiments/xedni-nonisomorphic-expansion-20261115/audit.json 2> experiments/xedni-nonisomorphic-expansion-20261115/audit.stderr
(cd experiments/xedni-nonisomorphic-expansion-20261115/formal && lake build ExpansionUnion > build-output.txt 2>&1)
python3 experiments/xedni-nonisomorphic-expansion-20261115/verify.py
```

Every Sage invocation uses the repository's checked launcher, including the screen's child workers. The runtime receipt, stdout/stderr for every candidate, compressed full query rows, formal build output, and a SHA-256 file seal accompany the result.
