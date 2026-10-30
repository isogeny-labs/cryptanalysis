# Negation closure limits the p63317 signed pair index to 689 subgroup points

The prespecified p63317 public target `(31493,39327)` has status `NO_RELATION` under the frozen signed distinct-source pair policy. The pair index enumerated 3,120 patterns but reached only 689 of the 2,531 order-2531 subgroup points (27.2%). Its coverage is exactly the unordered sumset of the 40 projected class points. Because that point set is closed under negation, the 3,120 signed patterns have at most `40·41/2 = 820` possible unordered sums; 689 are distinct in this instance. The retained target lies outside that set, so the method did not produce a scalar from its pair index.

## Frozen instance and preparation

The curve is `E:y²+y=x³−x²−10x−20` over `F_63317`, with `#E(F_63317)=63275` and largest prime factor `q=2531`. The 40 audited conductor-four class points and 477 support-four relation rows are hash-pinned from the prospective D79 holdout. Multiplication by 25 projects each class point into the order-2531 subgroup; all 40 projected points are distinct and nonzero. The exact relation matrix has rank 39 over `F2531`. Adding the anchor `log_T(T)=1` at the first nonzero projected point gives a unique 40-coordinate class-log solution. Its Sage solve took 36,065,542 ns after inputs were loaded, and the independent Sage audit enumerated all 2,531 multiples of `T` to verify every coordinate.

The target seed, rejection rule, counter cap and signed pair policy were frozen before target generation. Counter zero produced the public point. The fixture scalar is 973 and is kept separately from the producer's public-point input. No target replacement followed the pair lookup.

## Coverage and target status

Let `S={log_T(25P_i):0≤i<40}⊂F2531`. The independent audit establishes that `|S|=40`, `0∉S`, and `−S=S`. Any signed pair `±s_i±s_j` lies in `S+S`. Conversely, a sum of two distinct entries of `S` is a direct pair. A repeated-entry sum `2s` is represented using distinct source indices for `s` and `−s`, with signs `+,-`. Hence the frozen signed distinct-index pair outcomes equal `S+S` exactly.

| Measure | Result |
| --- | ---: |
| Signed distinct-index patterns enumerated | 3,120 |
| Unordered two-entry sums available before collisions | 820 |
| Distinct covered subgroup elements | 689 |
| Subgroup size | 2,531 |
| Frozen target scalar in covered set | No |
| Target query status | `NO_RELATION` |

The pure-Python sumset audit and an independent checked-Sage group index both obtain 689 points and exclude fixture scalar 973. They also reproduce the exact index digest, target point, seeded fixture construction, class logs and 477-row modular rank. The producer records 2,954,000 ns to project the base and build the pair index, then 1,500 ns for the target-dependent miss lookup and interval overhead. The latter is a censored lookup diagnostic, not a verified scalar-recovery time. Earlier class construction, relation enumeration and log solving are separate receipts. `candidate_id` and `target_online_ms` remain null.

`FiniteCoverage.lean` checks the exact 40-entry log list, its negation closure, the 820 unordered sum patterns, 689 distinct values, and absence of scalar 973. `PROOF_MAP.md` states the finite and geometric verification boundaries. The full signed-index/sumset equality has the mathematical proof above and two independent computational checks.

## Next experiment

The same frozen public target can test a prespecified three-summand extension. A pair-index-plus-one query would ask whether `Q−B_k` is in the existing pair index, charging all 40 target-dependent probes and retaining a miss if none succeeds. This tests added coverage while preserving the failed pair arm and its original target identity.
