# Class-part span bounds Hecke rank but screens none of ten D79 classes

Every verified degree-13 Hecke row is a signed sum of lifted sources' class-part vectors. Consequently, augmenting the baseline by all Hecke rows cannot have larger rank than augmenting it by the class-part vectors. The bound is valid before signed cancellation enumeration, once the source lifts are available. Across ten sealed 40-source classes, the class-part vectors complete rank 40 in every case, so the bound does not reject any class as unable to reach rank 39.

| p | q | Baseline rank | Class-part span rank | Hecke rank | First source count permitting rank 39 by bound | First attained rank 39 |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 102077 | 929 | 32 | 40 | 34 | 7 | — |
| 103357 | 197 | 35 | 40 | 39 | 4 | 35 |
| 108557 | 701 | 31 | 40 | 34 | 10 | — |
| 115237 | 307 | 32 | 40 | 35 | 7 | — |
| 122117 | 127 | 32 | 40 | 33 | 8 | — |
| 123517 | 2749 | 32 | 40 | 34 | 9 | — |
| 129197 | 461 | 34 | 40 | 36 | 5 | — |
| 137957 | 137 | 31 | 40 | 33 | 8 | — |
| 145477 | 61 | 34 | 40 | 37 | 6 | — |
| 151637 | 149 | 32 | 40 | 32 | 8 | — |

The p103357 trace makes the looseness concrete: after four ascending source lifts, class-part span already permits rank 39, but signed outside-trace cancellations do not attain it until source 35. At p151637, the full source span permits eight additional dimensions while 190 verified Hecke rows add none. The bottleneck in these cases is the cancellation restriction and the resulting row dependencies, rather than the linear span of unrestricted class-part vectors.

## Mathematical proof

Let B be the baseline row space, C the span of lifted class-part vectors, and H the span of derived Hecke rows over F_q. Each row `h` has the form `Σ_s a_s c_s` for source coefficients `a_s`, so `h∈C`; hence `H⊆C` and `B+H⊆B+C`. Monotonicity of finite-dimensional rank gives `dim(B+H)−dim(B) ≤ dim(B+C)−dim(B)`. The Lean module formalizes this implication over an arbitrary field and finite source, relation, and coordinate index sets. The Sage replay checks that the integer source coefficients and stored class rows instantiate the hypothesis on the ten curves.

The replay is a retrospective diagnostic on retained source outputs. It includes no source-lift or relation-enumeration speed measurement. `candidate_id` and `target_online_ms` remain null. The exact prefix ranks and first-feasible counts are in `result.json`. The first run attempt failed while decoding the pinned Python helper as JSON; its stderr is retained, and the corrected run passed the sealed-input checks.

The next bound needs to incorporate the outside-trace cancellation condition or the support-at-most-four restriction. The unrestricted class-part span alone is too broad for a useful skip decision in this panel.
