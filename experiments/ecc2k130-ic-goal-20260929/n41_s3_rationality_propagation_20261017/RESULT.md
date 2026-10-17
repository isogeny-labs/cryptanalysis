# Direct bilinear pair leaves in the N41 six-pair S3 circuit

**A fixed-seed product identity reduced the frozen public N41 six-pair circuit from 26,937 to 16,851 AND gates**, a reduction of **10,086 gates (37.44%)**. The new leaf uses seven explicit source-code bits and one 41-bit reciprocal pair-output coordinate. Independent checked Sage replayed all **960** signed pair states and verified that every one of the **240** code-slot leaf quadratics has exactly the two intended output roots. The 185-second and versioned 550-second unpinned public SAT searches both returned `BOUNDED_UNKNOWN`; their raw logs and resource caps are retained.

## Direct leaf construction

For the N41 W8 geometry, let `u` encode a source mask, `s` be the fixed seed, `p=(u²+u)((u+s)²+(u+s))`, and `c=1/x_pair`. The source-product map is linear in the seven free canonical mask bits because, writing `A=u²+u` and `S=s²+s`, `p=A(A+S)=A²+SA`. The earlier pair equation in `z=1/(x_pair+1)` is

`p(z²+z)+(s+z)²=0`.

Substituting `z=c/(c+1)` and clearing `(c+1)²` gives the direct bilinear leaf equation

`p c + ((s+1)c+s)² = 0`.

The executable excludes `c=0,1` and uses the archived 40 permitted canonical source codes per slot, plus the existing cross-slot folded-column clauses. The independent Sage audit reconstructs every source point and pair sum on `y²+xy=x³+1`, checks this equation, and finds two distinct reciprocal x-roots for each code. Its leading coefficient `(s+1)²` is nonzero, so these two roots exhaust each quadratic's field roots. Every allowed N41 code already has rational source points in the frozen geometry; the circuit's source inverse-trace witnesses are unnecessary for this exact finite source.

The five balanced S3 links and public target remain the same as in the [previous circuit](../n41_sixpair_shared_target_20261017/RESULT.md). The known relation satisfies every clause and native XOR row of the new public formula. An independent source readback confirms that none of the 42 code bits is pinned by a unit clause; the SAT queries receive only the public formula.

The rationality argument is local. For a point with nonzero x in the base field, Frobenius fixes x and sends the point either to itself or to its inverse, because the two y-roots differ by x. If `P+R` is rational and non-two-torsion, both children cannot be inverted by Frobenius: that would invert their rational sum and make it two-torsion. Exactly one child cannot be inverted either: cancellation would make that child two-torsion. Hence both children are rational. Apply this implication from the public root down each nonexceptional S3 link; the reciprocal-x nonzero clauses keep its intermediate nodes in the required chart. The [proof map](PROOF_MAP.md) links the group implication to a checked, axiom-free Lean theorem and identifies the remaining curve and S3 bridges. Checked Sage exhausts the corresponding reciprocal S3 implication over `GF(2^5)` and `GF(2^7)`, finding rational children in all **840** and **6,384** zero triples with a rational parent.

## Frozen N41 measurements

The field is `GF(2)[t]/(t^41+t^3+1)`, the curve is `y²+xy=x³+1`, and the public raw point is `(2026560328086,1928332930914)` on `EC1N41Ckb1h7d5e80d3c4d0`. The candidate remains a stage-level design with `candidate_id: null`.

| Same public target and six-pair topology | Previous shared-inverse circuit | Direct bilinear leaves |
| --- | ---: | ---: |
| AND gates | 26,937 | **16,851** |
| Variables | 31,533 | **20,283** |
| Ordinary CNF clauses | 82,957 | **52,243** |
| Native XOR rows | 3,689 | **2,975** |
| Direct leaf AND gates per slot | — | **287 = 7×41** |

| Frozen public SAT query | Result | Parent wall | Sampled combined RSS | Logged restarts |
| --- | --- | ---: | ---: | ---: |
| One worker, 180-second solver / 185-second parent | `BOUNDED_UNKNOWN` | 185.013 s | 409,419,776 B | 3,480 |
| One worker, 540-second solver / 550-second parent | `BOUNDED_UNKNOWN` | 550.025 s | 522,272,768 B | 5,411 |

Both runs parsed the exact public XCNF and entered search; neither printed a SAT or UNSAT terminal line before its parent cap. The previous circuit's 185-second query also ended bounded and used 205,340,672 bytes sampled combined RSS. These ordinary-host runs were not isolated matched performance pairs; the formula-size reduction is exact, while a solver-throughput or target-relation improvement remains unmeasured. [verification.json](verification.json) binds source, formula, build check, Sage audits, Lean output, raw solver logs, caps, and the versioned query protocols. Its post-run source readback covers the transitive arithmetic modules and rebuilds the public XCNF byte for byte.

## W23 transfer check

The N131 W23 mask represents `w=u²+u`; its source x-coordinate is `1+1/u` with `u=halftrace(w)`. For fixed seed mask `898618`, the product is `p=w(w+w_s)` and has exact rank **22** on the 23-dimensional mask space. The direct bilinear leaf therefore projects to **2,882 = 22×131 AND gates per slot** before any full N131 S3 circuit, column policy, or solver cost. Independent checked Sage verified the product rank, showed `1` is outside its image, and replayed the direct leaf identity on all **32 signed sums** of eight archived W23 sample edges. The two initial projection attempts are retained as `PRODUCER_FAILURE` receipts: the first used the N41 mask model for W23; the second had a halftrace assertion variable error. The corrected v3 protocol and result are [here](n131_leaf_projection_v3_result.json).

For a proposed N131 implicit-mask circuit, the [Frobenius propagation theorem](RationalityPropagation.lean) could replace per-endpoint rationality gates when the public root, all internal group sums, and source endpoints lie in the non-two-torsion chart. This is a conditional method direction. The current N41 circuit instead uses an explicitly enumerated rational code list. N131 promotion still needs a complete source-bound one-worker, 600-second, 4-GiB projection, distinct-column handling, and an unpinned ordinary N41 relation from the changed solver.

## Next experiment

The source gate is now small enough that further inverse-gate tuning is unlikely to address the observed N41 search cap. The next experiment should put the public point into a **joint constraint on at least two still-free pair-code families** before S3 tree expansion. The exact quartic family filter in the [parallel RR gate](../n41_rr_family_resultant_20261017/RESULT.md) distinguishes code families that their linear spans cannot, but its fixed-suffix, pairwise implementation is too large at N131. A useful next implementation must eliminate a free suffix family symbolically, check that it retains the archived relation, and report whole-family rejection and complete failed-attempt cost on an unpinned N41 public query.
