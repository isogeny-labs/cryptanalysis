# Varied target scalars change the frozen family’s first-hit behavior

Across the eight held-out fields, the unchanged 14-vector family first relates the public target at queries **36–242** when each target scalar is derived independently from the frozen SHA-256 rule. The same family reached query 35 in every field when the fixture scalar was fixed at 17. This panel isolates target diversity: field selection, vector order, admissibility, and query schedule are unchanged.

| Field `p` | Subgroup `q` | Fixture scalar `d` | First query | Vector | Vector tests | Abstract add calls |
| ---: | ---: | ---: | ---: | :---: | ---: | ---: |
| 773 | 751 | 496 | 242 | `(1, 1)` | 3,364 | 22,824 |
| 863 | 883 | 671 | 36 | `(3, 1)` | 489 | 3,317 |
| 883 | 883 | 260 | 131 | `(1, -2)` | 1,808 | 12,269 |
| 983 | 983 | 671 | 48 | `(2, 1)` | 653 | 4,427 |
| 1049 | 1103 | 775 | 120 | `(2, 1)` | 1,661 | 11,267 |
| 1153 | 1153 | 530 | 94 | `(3, -1)` | 1,300 | 8,820 |
| 1423 | 1453 | 342 | 115 | `(2, -3)` | 1,589 | 10,780 |
| 1433 | 1459 | 430 | 88 | `(1, 3)` | 1,210 | 8,207 |

## Protocol and verification

`protocol.json` pins the parent family source and protocol, field selection, scalar derivation, query order, admission, immediate stop, and cost boundary before the varied-target run. For each `(p,q)`, the fixture uses `d = 1 + SHA256("xedni-target-diversity-v1|p|q") mod (q−1)`, interpreted as an integer digest; `Q=dG` is constructed outside the search interval. The producer searches from public `Q,G`, records every queried prefix row, and stops at the first relation with invertible coefficient sum. No scalar was rejected or reseeded.

The checked Sage audit independently reconstructs each curve `y²=x³−x−2`, confirms `#E(F_p)=ord(G)=q`, derives each scalar anew from the frozen label, checks every saved vector test against both the elliptic-curve group law and the modular relation equation, and independently replays the recovered scalar. It also reconstructs the exact abstract add-call count, including lazy query generation and every vector test through the hit. The fixture construction and independent replay are separate correctness work. All eight rows pass. An add call is an abstract group-operation count, not a field-operation or wall-time measurement.

The pinned Lean module `VariedTargetFirstHit.lean` proves, for each of the eight `(q,d)` pairs, that the recorded vector relates at its recorded offset and that no vector in the frozen family relates at any earlier admitted offset on the first lexicographic query row. The early-offset statements exclude offset zero, where the public points coincide, and offset `d`, where the second point is identity. The checked Sage audit supplies the curve/group bridge. `lake build VariedTargetFirstHit` passed 3,138 jobs, and all 16 `#print axioms` outputs use only standard Lean foundations.

The finite first-hit result does not price relation discovery, rational curve selection, rank work, or a matched same-target rho run. The next comparison should freeze multiple independently generated target points per field and measure the complete target-dependent interval on one calibrated resource tier, preserving each failed or censored attempt.

Reproduce from the repository root with `python3 experiments/xedni-target-diversity-holdout-20261115/run.py`, `./sage --runtime-info`, `./sage -python experiments/xedni-target-diversity-holdout-20261115/audit.py`, `(cd experiments/xedni-target-diversity-holdout-20261115/formal && lake build VariedTargetFirstHit)`, and `python3 experiments/xedni-target-diversity-holdout-20261115/verify.py`.
