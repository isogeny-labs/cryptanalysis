# Bounded coefficient-family control for xedni's two-point panel

The frozen 14-vector family produces 6,136 admissible public-group relation
events in the eight-field panel. The 13 vectors with nonzero coefficient sum
have disjoint hit sets: each has `r−1` hits in a subgroup of order `r`, and
every hit independently replays the fixture scalar. The remaining vector,
`(1,-1)`, has zero hits under the panel's distinct-point admission rule.
The earliest family hit lies at ordered query 3–8, versus 3–66 for the
previously tested single vector `(1,2)`. This gain in first-hit rank uses
14 vector tests per admissible query.

| Base prime | Subgroup `r` | Admissible queries | Family hits | First family query | First `(1,2)` query |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 47 | 43 | 1,722 | 546 | 5 | 5 |
| 101 | 53 | 2,652 | 676 | 6 | 53 |
| 191 | 53 | 2,652 | 676 | 6 | 53 |
| 211 | 79 | 6,006 | 1,014 | 3 | 66 |
| 251 | 61 | 3,540 | 780 | 8 | 57 |
| 281 | 73 | 5,112 | 936 | 5 | 63 |
| 347 | 47 | 2,070 | 598 | 3 | 3 |
| 349 | 71 | 4,830 | 910 | 8 | 62 |

The runner evaluated 30,008 ordered queries and 400,176 public-group vector
tests on admissible pairs. It formed `Pᵢ=Q−tᵢG` from the frozen public `Q`
and `G`, and checked `aP₁+bP₂=O` with independent group arithmetic. The
scalar 17 was used only in the separate modular audit and for fixture replay;
the runner recovered the scalar from each nonzero-sum hit and checked it
against `Q`. Both stderr files are empty. The independent audit reconstructs
every query from the modular equation, checks all per-vector counts and first
events, and verifies the original `(1,2)` row against the earlier control.

## Why the hit sets partition cleanly

For the panel's prime-order subgroup, the relation is
`a(w−t₁)+b(w−t₂)=0 (mod r)`. Each selected nonzero-sum vector has `a,b` and
`a+b` nonzero modulo `r`. Its line has `r` solutions, one of which is
`(t₁,t₂)=(w,w)`. Every other solution has two nonidentity, distinct sampled
points and is admissible, giving `r−1` hits. The selected primitive vectors
represent distinct projective directions modulo all eight subgroup orders:
every pairwise determinant has absolute value between 1 and 18, below the
minimum subgroup order 43. Two such lines meet only at the excluded point
`(w,w)`. The `(1,-1)` line is `t₁=t₂` and has no admissible query. Thus the
observed union size is exactly `13(r−1)` in each field.

The pinned Lean module proves that two relations with nonzero determinant
force both sampled scalars to zero, and that a zero-sum vector cannot relate
distinct sampled scalars. The full finite-cardinality statement remains a
written proof plus exhaustive audit; `PROOF_MAP.md` records its missing Lean
cardinality bridge.

## Interpretation and reproduction

The family increases the number of public reduced relations linearly with
the number of distinct directions, while charging one public-group test per
direction on every admissible query. It is a control for the two-point
coefficient-search idea: these exact counts do not include rational-lift
construction for the new vectors, target-independent setup, or a wall-time
comparison. A lift relation in this family still has to be found and reduced
before its scalar equation applies.

`protocol.json` freezes the family, query order, field list, admission rule,
and parent digests. From this directory run `python3 run.py > result.json`
and `python3 audit.py > audit.json`; `SEAL.sha256` checks the retained files.
