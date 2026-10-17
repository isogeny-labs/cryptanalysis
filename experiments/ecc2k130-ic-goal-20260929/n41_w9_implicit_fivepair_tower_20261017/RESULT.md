# Implicit five-pair tower linked at the public target

An exact **three-plus-two pair-output tower** was built for the frozen N41 orientation-6 public point with all five aligned W9 source codes free. The archived ordinary relation satisfies every emitted CNF clause and native XOR row. Moving the public target into the two-pair norm removes 41 primary partial-sum coordinate bits, but expands the circuit from **112,023 to 144,139 AND gates**. The first unpinned SAT query passed the 600 s wall boundary after its supervisor lost process-control authority; the corrected target-early query reached its enforced **600 s wall cap**, 148,000 logged conflicts, and 586 MB sampled combined peak RSS. Neither run returned a terminal SAT model. These results reject promotion of these two monolithic Sage/Python-generated SAT encodings to the N131 public-query gate under the present implementation.

## Instance and exact circuit

The field is `GF(2)[u]/(u^41+u³+1)` and the curve is `y²+xy=x³+1`, ID `EC1N41Ckb1h7d5e80d3c4d0`. The five source-pair slots each have 71 admissible canonical codes and four signed point states per code, with rotations `(0,0,12,12,24)`. The input is the frozen orientation-6 public subgroup point from [aligned_states.json](../n41_n131_w29_rotation_alignment_20261017/aligned_states.json). No source code or signed state is fixed in either solver formula. All overlapping folded-column code pairs are excluded by 770 clauses. The [checked-Sage fixture](fixture.json) supplies a positive *assignment control* at state IDs `(105,244,66,47,111)`; neither query receives those IDs.

Let `a,b,c,d,e` be reciprocal pair-output coordinates and `z` the reciprocal coordinate of the first three-pair partial sum. Each pair code determines a binary-linear product `p_i` and a quadratic `C_i x_i²+p_i x_i+H_i=0`. The left formula takes the three successive quadratic norms of `f4(a,b,c,z)`. In the initial formula, a second coordinate `y` represents the right two-pair partial sum: two norms of `f3(d,e,y)` and the public-target link `f3(z,y,t)=0` complete the circuit, where `t=1/x(Q)`.

The target-early formula eliminates `y` algebraically. It takes the two right-root norms of `f4(d,e,z,t)` and constrains the resulting field value to zero alongside the left three-root norm. The [Lean theorem](TargetTowerSound.lean) proves the characteristic-two implication `f3(d,e,y)=0 ∧ f3(z,y,t)=0 ⇒ f4(d,e,z,t)=0`, and the four-root product's zero consequence. The numeric circuit then applies the two quadratic norms to that target-conditioned four-point expression. This is a sound necessary condition on whole right code families at a shared `z`; candidate models still require exact point-sum replay.

## Frozen builds and public queries

| Boundary | Partial-sum `y` explicit | Target absorbed into right norm |
| --- | ---: | ---: |
| AND gates | 112,023 | 144,139 |
| Variables | 128,554 | 164,053 |
| CNF clauses | 337,887 | 434,194 |
| Native XOR rows | 16,409 | 19,833 |
| Serialized XCNF | 11,304,978 B | 14,409,689 B |
| Archived witness assignment | All three equations and every clause/XOR row pass | Both norm equations and every clause/XOR row pass |
| Unpinned public query | `WALL_CAP_MONITOR_FAILURE`; last log near 2.013M conflicts | `WALL_CAP`; last log near 148K conflicts |
| Parent wall boundary | Frozen 600 s; termination observed before 632 s, exact solver interval unavailable | **600.209 s**, enforced by owning supervisor |
| Peak RSS | Unknown because the first monitor lost custody | **586,235,904 B** sampled process tree |

The initial builder launch through system Python stopped at a missing `psutil` import before constructing a formula; [failure receipt](build_v1_failure.json) and the exact source are retained. The checked-Sage builder then produced both formulas and verified the positive control. The initial [query protocol](query_protocol.json) pinned one solver worker, a 600 s parent cap, 4 GiB combined RSS cap, source and binary digests. Its supervisor aborted because this macOS sandbox denied `psutil.children(recursive=True)` process listing. The already-running solver was identified by the open output file and exact PID. A direct-PID rescue monitor read its RSS but was denied termination authority at the wall boundary; the exact PID was then stopped through an elevated `SIGTERM`. The [failure](query_failure_v1.json), [terminal classification](query_result.json), partial stdout, and rescue stderr are retained. That run has **no certified peak-RSS bound or solver terminal status**.

The target-early [protocol](early_query_protocol.json) used the same target, source law, solver version, worker count, wall cap, and 4 GiB envelope. Its corrected owning supervisor sampled direct child plus parent RSS 2,946 times and terminated the child at the wall cap with return code `-15`. The [receipt](early_query_result.json) records `WALL_CAP`, no monitor error, 600.209 s, and 586 MB peak combined RSS. The conflict counts are raw progress counters, not relation-yield or solver-completion measurements. Both queries ran on an ordinary shared host; their wall readings are descriptive and do not establish an isolated CPU speed comparison. The measured configuration remains `candidate_id: null` because it is a decomposition-stage solver without the rest of the IC pipeline.

## Independent algebra and proof boundary

The [checked-Sage pair audit](pair_law_result.json) reconstructed every admissible pair-output point in all five slots: **355 code/slot rows and 1,420 signed states**. Every reciprocal output obeys the circuit's `C_i x_i²+p_i x_i+H_i=0`; every code has exactly two distinct reciprocal roots. The archived five-pair group sum, public orientation, and nonexceptional partial coordinates are checked in the [fixture](fixture.json). The build scripts independently completed the witness's auxiliary-gate assignments and checked all formula clauses and XOR rows.

Pinned Lean 4.34.1 built `f3_swap_middle`, `common_quadratic_root`, `right_target_f4_zero`, and `right_root_product_zero`; [output](lean_v2.stdout) reports only `propext`, `Classical.choice`, and `Quot.sound`. The first Lean build's unsolved final simplification is preserved in `TargetTowerSound_v1.lean` and `lean_attempt_v1.*`. The written proof uses the S3 middle-coordinate symmetry, the common-root quadratic resultant, and the fact that one zero factor makes the right-root product zero. The concrete S3-to-elliptic-group chart and the implementation's nested norm-to-root-product bridge have checked finite-field controls here and in the prior [three-source tower](../n41_w8_three_code_resultant_20261015/RESULT.md); full Lean bridges to those concrete objects remain open.

## Decision and next gate

Inserting the target before right-coordinate branching increased symbolic circuit size and gave no completed public relation at the same one-worker wall boundary. The five-pair tower therefore remains a verified algebraic component, not the selected N131 solver. The next test should use the existing independently verified unpinned N41 six-pair public relation as a control and measure a **native, source-prefix family constraint** before expanding a three-slot Cartesian product. It must reject entire still-free code regions from the public point with charged work below the direct N41 join, then pass a source-bound N131 projection before any 600 s/4 GiB public run. Later gates remain useful relation rank, final linear algebra, unseen target recovery, and matched same-point rho online time.
