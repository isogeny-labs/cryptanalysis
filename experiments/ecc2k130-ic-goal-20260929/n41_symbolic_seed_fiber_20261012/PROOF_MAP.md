# Proof map for source-product fiber elimination

| Claim | Formal declaration or evidence | Status |
| --- | --- | --- |
| A nested finite product is zero iff one allowed product pair makes `H` zero | `JointNorm.joint_zero_iff` in the adjacent [checked Lean module](../n41_joint_fourpair_resultant_20261012/JointNorm.lean) | Fully checked for arbitrary finite lists and a carrier with explicit `1≠0` and no-zero-divisors hypotheses. Both hold in `GF(2^41)`. |
| `Res_p(G_P,H)` and `Res_q(G_Q,…)` equal nonzero scalar multiples of those finite products | Open resultant bridge | The concrete Sage resultants and source roots are checked per completed case. A Lean polynomial resultant library and exact monic split-product theorem are still needed. |
| `gcd(G_Q,H(p_i,q,z))` has positive degree iff an allowed `q_j` makes `H` vanish | Open GCD-root bridge | The split-source polynomial and all eight concrete decisions are checked in Sage. The generic polynomial-GCD theorem is not yet formalized in Lean. |
| The archived 266-term `H` equals elimination of the reciprocal pair equations and upper Semaev equation | Prior computational derivation and its source receipt | A general Lean derivation remains open; this experiment hashes the archived polynomial before execution. |
| An `H` root corresponds to a signed diagonal four-atom group sum on the nonexceptional chart | Independent checked-Sage group audit | Verified on every frozen panel assignment. General curve-law formalization remains open. |

The formal structural theorem was built using pinned Lean 4.34.1 in the adjacent experiment, with `#print axioms` output retained there. This experiment adds no weaker replacement theorem or assumed conclusion. A complete formal proof of the resultant predicate requires the two open bridges above.
