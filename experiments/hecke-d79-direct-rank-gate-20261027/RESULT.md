# A pre-lift direct-rank gate correctly rejects the p90917 holdout

The frozen rule selected the first eligible 40-point D79 class after (v=279): (v=301), (p=90917), (#E(F_p)=90780), and largest subgroup-order prime (q=89). Before degree-13 work, its 199 direct relations and degree-2/5 base rows had rank 32 over (F_{89}), so the trained threshold `rank≥37` issued `SKIP`. The full 40-source challenge, run regardless of that decision, produced 201 group-verified Hecke rows and rank 35. The frozen rank-39 criterion was not met, giving one prospective `CORRECT_REJECT` result.

| Ascending sources available | Hecke candidates | Relation rank over (F_{89}) |
| ---: | ---: | ---: |
| 5 | 0 | 32 |
| 10 | 3 | 32 |
| 15 | 7 | 33 |
| 20 | 12 | 33 |
| 25 | 30 | 33 |
| 30 | 58 | 33 |
| 35 | 123 | 33 |
| 40 | 201 | 35 |

The independent checked-Sage audit re-evaluated the prescreen, reconstructed the 40 class points and projection, independently enumerated all 199 direct relations, replayed every source equation and the 201 Hecke group relations, and checked the direct and full ranks. All 40 source lifts had status `OUTSIDE_CLASS_TRACE`. The gate decision and class result were hash-sealed before those lifts.

The full pool adds **three** rank directions, whereas the three training classes added at most two. Thus direct rank 37 is a tested heuristic threshold, not a proven necessary condition for reaching rank 39. This holdout validates one rejection and leaves false-reject risk open. A further prospective series should record gate decisions and full-source challenges over more independently selected classes before using it to skip work routinely.

The audited Hecke pool has one support-three row and 200 support-four rows. Of the 201 supports, 197 use exactly two residue-1 sources, three use none, and one uses four. Lean kernel-checks these finite composition counts with no axioms. The numeric matrix-rank formalization remains open in `PROOF_MAP.md`.

The local direct enumeration took **1,359,520,417 ns** and the full challenge source-lift intervals sum to **871,123,126 ns**; Hecke enumeration took **1,414,448,709 ns**. These are stage diagnostics from the recorded checked-Sage runtime, not an online IC comparison. `candidate_id` and `target_online_ms` remain null.
