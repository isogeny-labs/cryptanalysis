# First-slot code propagation leaves all 40 N41 public families open

**CNF and native-XOR unit propagation rejects zero of the 40 valid first-slot code families** in the frozen N41 six-pair public-point formula. The archived ordinary relation's first-slot code is 6 and remains open. An independent full-scan propagator reproduced every code's status and exact fixed-point assignment count. This closes first-code unit propagation as an early whole-family rejection rule for this N41 circuit under this input law; it directs the next solver design toward a stronger nonlinear consequence that couples multiple source slots to the target.

## Frozen input and method

The input is the [N41 six-pair public XCNF](../n41_sixpair_shared_target_20261017/public.xcnf), whose previous [exact target-conditioned join](../n41_sixpair_shared_target_20261017/RESULT.md) found and independently replayed an unpinned relation. The curve is `EC1N41Ckb1h7d5e80d3c4d0`, the target is that run's frozen raw public point, and the formula has 31,533 variables, 82,957 ordinary CNF clauses, and 3,689 native XOR rows. The [protocol](protocol.json) fixes the formula and independent join-certificate hashes, one worker, a 180-second cap and 4 GiB process RSS cap before measurement. This is a point-decomposition component with `candidate_id: null`.

The [screen](screen.py) identifies each of the six seven-wire source-code groups from its 88 forbidden-code clauses. Their complements contain exactly 40 allowed codes per slot. It assigns each valid first-slot code, then repeatedly applies unit clauses and one-unassigned-variable XOR equations until a contradiction or fixed point. A contradiction would exclude every completion of that code under this exact public target; `OPEN` means only that these local rules found no contradiction. The relation certificate's source mask 6 maps to allowed code 6 and is checked as a positive control. The [second implementation](audit.py) reparses the XCNF and rescans every clause and XOR row to a fixed point, without using the first implementation's incidence queues.

| Complete first-slot census | Result |
| --- | ---: |
| Valid code families tested | 40 / 40 |
| Contradictions / open families | **0 / 40** |
| Archived relation's code | 6, open |
| Assigned variables at fixed point | 978–1,226 |
| Incidence-based screen wall | 0.306 s total; 3.18 ms median per code |
| Independent full-scan replay wall | 13.544 s; 2–3 whole-formula passes per code |
| Peak process RSS, screen / replay | 62,390,272 / 37,044,224 B |

The [run receipt](result.json) retains all 40 statuses, assignment counts and per-code times; [stdout](run.stdout) and [stderr](run.stderr) retain the terminal streams. The [independent audit receipt](audit_result.json) matches all 40 fixed-point counts and statuses; its [stdout](audit.stdout) and [stderr](audit.stderr) are retained. These timings are ordinary-host algorithmic diagnostics, with no physical-host isolation or matched IC/rho run. This finite census needs no sampling interval. The screen is a semantic CNF/XOR propagation test on the exact archived formula; it does not estimate natural relation yield at N131.

## Search decision

Fixing one source-code family propagated many auxiliary values but yielded no target-conditioned rejection on this N41 public formula. A second code or a nonlinear elimination across multiple pair-output families is required before this style of filter can supply the early pruning needed by the N131 W23 source. Such a change must retain the unpinned N41 relation, measure whole-family rejection and charged cost, and meet the frozen N131 source-bound work and memory gate before an ordinary-target query. The separate d13/m12 one-target candidate has a `READY` preflight and remains at its local storage-admission gate; its precomputation, rank, target-recovery and paired-rho stages are distinct from this diagnostic.
