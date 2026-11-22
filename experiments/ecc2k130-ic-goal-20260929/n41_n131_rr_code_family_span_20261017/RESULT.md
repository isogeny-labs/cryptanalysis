# Trace-certificate saturation across a free pair code

**Four source-valid W23 first-pair codes saturate the 131-bit space of sign-dependent Riemann–Roch coefficients when the other five pair codes and one x root per code are fixed.** Their pooled ranks are **34, 68, 102, 131**. Thus no single GF(2)-linear trace functional can annihilate every sign-dependent coefficient across these four charts. The first three selected charts still admit such a common functional. An independent checked-Sage computation formed all 256 seven-point determinants, recovered their sign coefficients by Boolean Möbius inversion, and reproduced every rank. An exact [67-term XOR certificate](span_certificate.json), independently checked against those Sage coefficients, expresses the first chart's constant coefficient in the nonconstant span.

This is a quantitative test of whether a fixed-root rejection certificate can be reused over a still-free source code. It closes **one shared linear-certificate construction on this selected four-code W23 family**. It does not exclude different code regions, code-dependent certificates, nonlinear conditions, or other early target constraints.

## Exact source and calculation

The N131 field is `GF(2)[t]/(t^131+t^13+t^2+t+1)` and the curve is `y²+xy=x³+1`. The six slots use fixed-seed W23 pair edges and Frobenius rotations `(0,18,36,54,72,90)`. The raw public point is the frozen target in [panel_n131_v2.json](panel_n131_v2.json). Five edges are the archived source sample indices `(2,3,4,5,6)`. The first slot varies over sample indices `(0,1,7)` and the first further eligible, folded-column-disjoint edge found by the frozen ascending-mask rule, `(46,898580)`. The [checked Sage preparer](prepare_n131_v2_sage.py) rebuilt every first-slot point and verified source trace conditions, two-root/four-sign structure, and folded-column disjointness. For the coefficient screen, each slot selects its lower x root and lower y sign; the sign polynomial then ranges over all `2^6` y-sign choices.

For seven distinct-x points consisting of the six pair sums and negative target, the `L(7O)` determinant is `D(s)=c_0+Σ_{0<|M|≤3}c_M∏_{i∈M}s_i`. A trace functional `L` that is 1 on `c_0` and zero on every nonconstant `c_M` proves every sign choice in that chart misses the target. To share one `L` over several first-code charts, all their 0-labeled coefficient vectors and 1-labeled constants must define a consistent linear system. The producer computes both ordinary coefficient rank and augmented rank; the independent Sage audit checks the finite coefficients and ranks.

| Frozen first-slot chart prefix | N131 pooled nonconstant rank | One common linear functional |
| --- | ---: | --- |
| Sample edge 0 | 34 | Exists |
| Edges 0, 1 | 68 | Exists |
| Edges 0, 1, 7 | 102 | Exists |
| Edges 0, 1, 7 and mask 46 | **131** | **Impossible** |

The [four-chart result](result_n131_v2.json), [Sage determinant audit](audit_result_n131.json), and [independent span replay](audit_span_result.json) retain all outcomes. The earlier three-chart [result](result_n131.json) remains separately frozen. All four charts have distinct x coordinates and each has nonconstant rank 34. The fourth chart lifts the augmented rank to 132, while the field-vector rank is 131.

The matched N41 screen fixes the five pair-code choices in the [verified public relation](../n41_sixpair_shared_target_20261017/join_audit_result.json) and varies its first pair over 35 column-compatible seed-56 codes. The two x roots of the first code already fill the 41-bit nonconstant span; even when only the lower x root of each code is used, the first **two distinct codes** fill it. The [root0 result](result_n41_root0.json) is a producer diagnostic on the exact N41 source; its public relation remains the correctness control for the source and target.

## Proof and next gate

The pinned Lean 4.34.1 [structural theorem](SpanObstruction.lean) proves that a Boolean-linear functional annihilating a set of coefficients also annihilates every XOR combination of them. `#print axioms` reports only standard `propext`. The finite N131 constant-in-span certificate is computationally checked by the independent Sage determinant replay; the concrete curve, determinant, and rank bridge is documented in [PROOF_MAP.md](PROOF_MAP.md). The [terminal verifier](terminal.json) checks input hashes, statuses, rank sequence, certificate XOR, Sage audit, and Lean output. These are correctness and representation diagnostics on one selected source family; `candidate_id` remains `null`.

The next constructive test should let the separating functional depend on a **compact source-code prefix** and measure how many W23 codes each prefix can cover before its coefficient span saturates. A useful prefix rule must be derived without enumerating its member codes, preserve every true decomposition, and reduce complete target-dependent work against the exact N41 join. A fixed functional over this selected four-code set fails that gate.
