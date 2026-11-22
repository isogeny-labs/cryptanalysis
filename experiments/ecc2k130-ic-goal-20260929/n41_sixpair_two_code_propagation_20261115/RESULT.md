# Two-code propagation identifies exactly the 46 source-invalid N41 pairs

Fixing the first two source product codes and propagating CNF unit clauses and
native XOR unit equations rejects **46 of 1,600** code pairs in the archived
ordinary N41 six-pair public-point formula. An exact comparison with the
independently archived source table shows that these are precisely its **46
source-invalid pairs**: all **1,554 source-admissible pairs remain open** under
this propagation rule. The relation's independently replayed witness pair
`(6,100)` stays open. This closes two-code unit propagation as a
target-conditioned early rejection rule for this input and directs the next
solver experiment to a stronger consequence involving the target and multiple
unresolved pair blocks.

## Frozen input and method

The input is the [N41 six-pair public XCNF](../n41_sixpair_shared_target_20261017/public.xcnf)
on `EC1N41Ckb1h7d5e80d3c4d0`; its archived
[independent relation certificate](../n41_sixpair_shared_target_20261017/join_audit_result.json)
supplies the positive witness. The formula contains 31,533 variables, 82,957
ordinary CNF clauses, and 3,689 native XOR rows. Each of its first two source
slots has 40 permitted seven-wire codes. The [protocol](protocol.json) freezes
the formula, propagator, witness, input law, one worker, 180-second alarm, and
4-GiB process RSS cap. This is a point-decomposition component with
`candidate_id: null`.

The [producer](screen.py) reuses the prior incidence-based semantic
[propagator](../n41_sixpair_code_propagation_20261115/screen.py) and fixes both
code groups before running it to a fixed point. `CONFLICT` means that a clause
or XOR equation became false and excludes every completion of those fixed
codes in this exact formula. `OPEN` means only that these local rules found no
contradiction. Every one of the 40×40 combinations is retained in
[result.json](result.json), including its status, assignment count, conflict
reason, and per-pair elapsed time.

| Complete first-two-code census | Result |
| --- | ---: |
| Code pairs tested | 1,600 / 1,600 |
| Conflicting / open | **46 / 1,554** |
| Conflict rule | CNF for all 46 |
| Source-admissible pairs rejected | **0 / 1,554** |
| Witness codes | `(6,100)`, open |
| Assigned variables for open pairs | 1,026–1,522 |
| Producer internal wall | 5.184 s |
| Median per-pair loop time | 3.158 ms |
| Producer self peak RSS | 61,505,536 B |

The separate [source-validity check](source_validity_comparison.json) maps
each seven-wire code to the archived four-state source geometry and compares
the 46 conflicts against the 46 missing pairs in the
[1,554-case table](../n41_w8_two_code_affine_span_20261013/cases.jsonl).
The sets match exactly. This comparison uses the table only to classify the
producer's outcomes; no source-validity result was supplied to propagation.

The independent [full-scan auditor](audit.py) reparses every CNF and XOR row,
recomputes each two-code fixed point without the producer's incidence queues,
and checks every status and every open-pair assignment count. Its receipt is
saved as [audit_result.json](audit_result.json): **1,600/1,600 statuses** and
**1,554/1,554 open-pair assignment counts** match, with 46 conflicts.
The audit took 114.818 seconds and reached 36,995,072 B self peak RSS.
The first auditor precheck stopped at conflicting pair `(2,2)` because it
compared the number of assignments before the first conflict across two
different propagation orders. Both implementations reported `CONFLICT`;
the final auditor compares that semantic status for conflicts and exact
fixed-point size for open pairs. The initial check and correction are
retained in [audit_precheck_failure.json](audit_precheck_failure.json).

These wall and RSS observations are ordinary-host algorithmic diagnostics
on one fixed archived public point. Run `python3 verify.py` here to check the
frozen hashes, both independent receipts, and witness retention. The next
filter must reject at least one **source-admissible** N41 family while
retaining `(6,100)` and must include its target-dependent work and source
traversal in the cost. Before a degree-131 transfer, it needs a source-bound
600-second/4-GiB cost case with multiple pair blocks unresolved.
