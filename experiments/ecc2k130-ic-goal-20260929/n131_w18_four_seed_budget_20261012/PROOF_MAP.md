# Four-seed coverage proof map

The counting contribution is a finite-target bound. A schedule chooses a
list of four-seed families independently of a uniformly sampled subgroup
target. Each family has a left list of two-pair sums and a right list of
two-pair sums. Each left/right combination determines one projected target.
Duplicate targets, source-column collisions and exceptional charts only
decrease the number covered. With at most `c_max²` entries in each half,
`T` families cover at most `T c_max⁴` distinct subgroup targets. Hence their
uniform-target success probability is at most `min(1,T c_max⁴/r)`.

| Mathematical step | Lean declaration | Exact hypotheses and status |
| --- | --- | --- |
| One family covers at most `c_max⁴` distinct outputs | `FourSeedBudget.fixed_tuple_coverage` | Abstract output map `A→B→Q`; hit list has no duplicates, every hit has a listed left/right witness, and each half list has length at most `c_max²`. Checked. |
| A target-independent schedule of `T` families covers at most `T c_max⁴` distinct outputs | `FourSeedBudget.fixed_schedule_coverage` | Family list and its output maps are fixed; each hit has a listed family and left/right witness; all half-list lengths are at most `c_max²`. Checked. The theorem itself does not define target sampling. |
| `1,082,551,755,296,979,644` is the first `T` for which `2T c_max⁴ ≥ r` | `FourSeedBudget.half_ceiling_is_minimal` | Constants `c_max=133152` and `r=680564733841876926932320129493409985129`; proves the strict inequality at `T−1` and nonstrict inequality at `T`. Checked by kernel-verified `decide`. |
| Every concrete W18 seed family has at most `c_max=133152` signed, distinct-column pair states | Open concrete-source bridge | The [independent audit](audit.json) recomputes all 262,144 integer counts from the 131,307-mask W18 source with a Walsh transform and same-column correction. A Lean definition of the exact source table, curve/column policy and checked finite count is not yet present. Full concrete formalization is partial. |

The structural proof reuses
[`JoinCoverage.distinct_successes_bound`](../n131_w18_tenpair_mitm_bound_20261012/JoinCoverage.lean):
the output list has one entry for each left/right combination; a duplicate-free
list of successful targets is a sublist in the membership sense and cannot
be longer. `fixed_schedule_coverage` concatenates those lists and bounds the
sum by induction on the family schedule. The arithmetic theorem checks
the exact half-coverage threshold. The probability sentence follows by
dividing the distinct-target count by the `r` equally likely subgroup
targets; it does not apply to a schedule chosen after inspecting the target.

Lean 4.34.1, commit `5045d0056413266e57c625dcd7c365b10e377c52`,
with its bundled Std, compiled the dependency and this module. The commands,
source digests, exit codes and output hashes are in
[`proof_receipt.json`](proof_receipt.json); outputs are
[`lean_dependency_check.log`](lean_dependency_check.log) and
[`lean_check.log`](lean_check.log). `#print axioms` reports only
`propext`, `Classical.choice`, and `Quot.sound` for the structural theorems,
and none for the numeric theorem. The reported proofs contain no `sorry`,
`admit`, custom research axiom, or native-evaluation bypass.
`lean4checker --fresh` was unavailable on this host.
