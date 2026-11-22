# Balanced S3 topology preserves the N41 relation at the same formula size

The seven-pair direct-parity source circuit was rewired into a balanced S3 tree while retaining the exact fixed-seed mask domain, folded-column shield, public target, and resource envelope. The frozen constructed assignment satisfies every row of the balanced formula. It has exactly **40,091 variables, 105,787 clauses, 4,456 native XOR rows, and 2,181,538 bytes**, matching the sequential circuit's counts. The unpinned one-worker query reached its frozen 185-second parent cap with active search and no terminal model.

The balanced tree forms pair aggregates `(0+1)`, `(2+3)`, `(4+5)`, then `(0+1+2+3)` and `(4+5+6)`, and finally couples those two aggregates to the same raw public target. The curve, seed 56, W8 source, seven rotations, 40 permitted pair codes, 14-column shield, and target point are identical to the [sequential run](../n41_w8_selector_elimination_control_20261013/RESULT.md). `control_result.json` binds the new formula hash and checks the complete saved assignment. The prior experiment's checked-Sage replay independently verifies all seven signed raw pairs and the public point; those source and target records are unchanged.

| Same-point N41 public query | Status | Parent wall | Sampled combined RSS | Logged restarts |
| --- | --- | ---: | ---: | ---: |
| Sequential S3 chain | `BOUNDED_UNKNOWN` | 185.145 s | 58,638,336 B | 1,006 |
| Balanced S3 tree | `BOUNDED_UNKNOWN` | 185.155 s | 94,601,216 B | 596 |

Both had one solver worker, `--maxtime=180`, a 185 s parent cap, 4 GiB RSS, and no solver source pins. The parent stopped both at the cap, and neither produced a SAT or UNSAT terminal line. The differing restart counts are solver trajectory diagnostics on an unisolated host, not a verified speedup. The complete logs, frozen protocols, and read-only `python3 -B verify.py` preserve both decisions. `replay_model.py` is the prepared full-row and group replay path for a future SAT result; it was not run for this bounded query. This remains a point-decomposition component with `candidate_id: null`.

Balancing the S3 tree did not pass the unpinned N41 promotion gate. The next design should couple two unresolved source-bound pair-output families directly to the target before selecting pair masks, then measure whole-family rejection and charge construction, solver, and replay. A fresh N131 600 s relation query should follow only an unpinned N41 relation and a source-bound N131 work projection.
