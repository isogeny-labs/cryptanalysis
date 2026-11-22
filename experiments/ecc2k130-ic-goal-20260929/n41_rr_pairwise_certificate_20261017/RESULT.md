# Complete N41 certificate-coverage census for one free pair code

**Every pair of distinct first-code charts in the frozen N41 public-relation source has full 41-bit sign-coefficient span.** All 35 lower-x-root charts individually admit a GF(2)-linear Riemann–Roch trace certificate, yet none of their **595** unordered pairs admits one common certificate. Taking both x roots of each code also gives full rank 41 for **all 35** codes, so a single trace functional cannot certify even one complete code family in this fixed-five-slot panel. Two independent checked-Sage determinant passes reproduced every one of these finite ranks.

This gives a complete source-domain falsifier for sharing one sign-annihilating trace across the first code in this particular N41 target-conditioned panel. It strengthens the earlier selected-code [N131 result](../n41_n131_rr_code_family_span_20261017/RESULT.md), where the fourth first-code chart saturated the 131-bit field. The result concerns a fixed trace functional; it leaves code-dependent and nonlinear certificates open.

## Frozen source and exact test

The curve is `y²+xy=x³+1` over `GF(2)[t]/(t^41+t³+1)`, curve ID `EC1N41Ckb1h7d5e80d3c4d0`. The raw target is `(2026560328086,1928332930914)`, whose cofactor-four image is the frozen subgroup point `(1654986373106,1310318707590)`. The five fixed pair slots and their x roots come from the independently [verified six-pair relation](../n41_sixpair_shared_target_20261017/join_audit_result.json). The first slot ranges over every one of the **35** canonical seed-56 codes whose two folded columns avoid the ten occupied columns. Each code has two x roots and two y signs per root. The [protocol](protocol.json) freezes the exact geometry, relation, target, source code and chart order.

For one root chart, the seven-point `L(7O)` determinant has a degree-at-most-three sign polynomial `D(s)=c₀+Σ_{0<|M|≤3}c_M∏_{i∈M}s_i`. A trace `L` that maps `c₀` to one and every nonconstant `c_M` to zero proves all 64 sign assignments in the chart miss the target. The test inserts the 41 nonconstant coefficients of each chart into a GF(2) basis, then solves the exact labeled linear system for a common `L`. Full nonconstant rank 41 rules out such an `L` regardless of the constant labels.

| Frozen comparison | Count | Nonconstant-rank result | Shared trace certificates |
| --- | ---: | ---: | ---: |
| Individual lower-x-root charts | 35 | Rank 34 each | 35 |
| Distinct pairs of lower-x-root charts | 595 | **Rank 41 in every pair** | **0** |
| Both x roots of one code | 35 | **Rank 41 for every code** | **0** |

The [census](result.json) records every coefficient vector, local decision, and pair rank. The [first Sage audit](audit_result.json) independently formed all 2,240 lower-root determinants, inverted their sign truth tables, and recomputed all 595 pair ranks with Sage GF(2) matrices. The [second Sage audit](audit_fullroot_result.json) formed another 2,240 determinants for the upper roots and independently checked all 35 two-root ranks. Each audit checked the exact geometry points and distinct-x chart condition. The [terminal receipt](terminal.json) binds the source hashes, all outcomes, Sage audits, and proof build. These runs are correctness diagnostics on one archived public point; no speed ratio is derived from them.

## Proof map and next algorithmic step

The pinned Lean 4.34.1 [theorem](CertificateCoverage.lean) proves the structural implication: if one chart's constant lies in the XOR span of the sign-dependent coefficients of two charts, every Boolean-linear trace annihilating those coefficients also annihilates that constant. Its `#print axioms` lists only standard `propext`. The finite GF(2) rank certificates and concrete curve bridge are independently audited in Sage; [PROOF_MAP.md](PROOF_MAP.md) records the remaining Lean obligations.

A fixed linear sign-annihilator does not provide the family-level pruning required before the N131 three-slot expansion. The next constructive design must carry code dependence into the condition itself or use a nonlinear invariant, and must be tested on the unpinned N41 relation against the exact native join. `candidate_id` remains `null` at this representation stage.
