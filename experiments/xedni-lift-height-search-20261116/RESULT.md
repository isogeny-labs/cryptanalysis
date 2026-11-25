# Bounded shifts reduce rational witness coordinate height

A frozen 27-candidate integral-lift search reduced the median rational witness-coordinate score from 214 to 142 bits across the 127 public-relation events. The score is the maximum numerator or denominator bit length among the two rational points' affine coordinates. Selection lowered the score for 120 of 127 positive events, with a median **paired** reduction of 53 bits. Every one of the 4,293 candidate curves was constructed and independently replayed; all passed the rational relation and public-reduction checks. The result measures representation size for an already identified public relation, with the full 27-candidate search cost retained.

## Frozen construction and selection

The [protocol](protocol.json) pins the 159 [source lift events](../xedni-common-preimage-lift-20261116/lifts.jsonl) by SHA-256 `c2619d5a8f2b7d3831c68e2fcd56243ce436b69003105d65c2f87bd7235201a5`. These comprise all 127 public relation events in the selected vector family and the 32 preselected public nonrelation controls. For the common finite preimage `S`, let `(x₀,y₀)` be its centered integer lift. For every `(kₓ,kᵧ,k_A)∈{-1,0,1}³` in lexicographic order, set

```text
x = x₀ + kₓp,       y = y₀ + kᵧp,       A = −1 + k_A p,
B = y² − x³ − Ax,   T = (x,y),          P = bT, R = −aT.
```

All variants reduce to the public curve `y²=x³−x−2` and preserve the public preimage `S`. Hence each has the exact rational relation `aP+bR=O`; on a positive event both points reduce to the specified `U,V`, while a negative control retains its second-point mismatch. The selected winner minimizes the stated coordinate score, with lexicographic shift tie-breaking. The `(0,0,0)` candidate is the previously reported centered baseline and was replayed exactly for every event.

| Measurement | Frozen result |
| --- | ---: |
| Source events, including controls | 159 |
| Candidates per event | 27 |
| Candidate attempts, all status `pass` | 4,293 |
| Selected winners | 159 |
| Positive events with a lower score | 120 / 127 |
| Positive baseline median score | 214 bits |
| Positive selected median score | 142 bits |
| Positive median paired score reduction | 53 bits |
| Positive baseline / selected maximum score | 405 / 330 bits |
| Control events with a lower score | 28 / 32 |

The [candidate rows](rows.jsonl) preserve all attempted coefficients, points, scores, reductions, and statuses; [winners.jsonl](winners.jsonl) retains each baseline, selected score, and paired change. [result.json](result.json) records the counts and SHA-256 digests. A separate [checked-Sage auditor](audit_sage.py) reconstructed all 4,293 rational curves and points, their group relations and reductions, every score, and all 159 argmin selections. [audit-sage.json](audit-sage.json) records `PASS`, with the [runtime receipt](sage-runtime.json) saved before the Sage job.

## Formal proof map

The pinned Lean 4 `v4.35.0-rc4` and Mathlib revision `021c46bdd042f67b538b9f9871d556a93713a9a9` build [HeightSearchInvariant.lean](formal/HeightSearchInvariant.lean):

| Declaration | Checked statement |
| --- | --- |
| `shifted_one_point_curve_equation` | Every chosen integer `x,y,A` lies on the curve with constructed `B`. |
| `shifted_coefficient_reduces` | Under the three coordinate/coefficient reduction equalities and the public point equation, the constructed `B` reduces to the public `B₀`. |
| `every_variant_common_relation` | `P=bT`, `R=−aT` satisfy `aP+bR=0` in any additive commutative group. |

The [build output](formal/build-output.txt) reports only standard Lean foundations in `#print axioms`: `[propext]`, `[propext, Classical.choice, Quot.sound]`, and `[propext, Quot.sound]`, respectively. The concrete elliptic-curve reduction homomorphism and its subgroup restriction remain the formal bridge identified in the parent common-preimage result; checked Sage supplies the full arithmetic replay for this panel.

This is a bounded, public-vector-dependent component comparison. It charges 27 constructions per event and records coordinate size; it does not replace a public-relation search or a same-target online wall-time study. The next experiment should freeze a bit-height cap and expand the prime range, measuring admission probability and construction cost while retaining all rejected and capped variants.
