# Full product-variable rank of the target-conditioned four-atom eliminant

**Result.** The frozen 266-term four-atom eliminant has coefficient-matrix rank **9/9** in the two source-product variables at the known N41 public-row block and its independent field control. The complete 32-by-32 product-fiber evaluation matrices also have rank **9/9** on both coordinates. Sixteen preregistered N41 seed/coordinate controls all have rank 9. At the archived N131 W15 constructed block and its field control, the same coefficient matrix has rank **9/9**. An independent checked-Sage path reconstructed and matched every coefficient matrix, all 20 ranks, the N41 32-by-32 fiber ranks, and the archived positive product roots.

This is an exact filter-design gate. A proposed decomposition of the specialized eliminant's **values** into at most eight terms `f_i(p)g_i(q)` cannot equal its values on the N41 positive 32-by-32 product fiber. The result concerns this value matrix and the tested field/source charts; a different representation of its zero predicate remains possible. The method therefore needs a coupled source-and-target constraint beyond a low-rank separation of this eliminant.

## Frozen method and arithmetic

The N41 field is `GF(2)[t]/(t^41+t^3+1)` and its positive chart is the frozen two-pair source fiber with rotations 14 and 21, seeds 94 and 171, and 32 distinct products in each bin. The target-conditioned four-atom output is the [frozen positive reciprocal](../n41_symbolic_seed_fiber_20261012/panel.json); a separately fixed reciprocal is the negative control. The N131 field is `GF(2)[t]/(t^131+t^13+t²+t+1)` with the archived W15 constructed block at rotations 26 and 39. Its exact rotated seed coordinates come from the checked [control fixture](../n131_w15_rotated_fouratom_inverse_20261010/control_result.json), whose source basis is not polynomial-bit identity.

For fixed rotated seeds `a,b` and offered block output `z`, write the checked universal eliminant as `H(a,b,p,q,z)=Σ_(i,j=0)^8 M_(i,j)(a,b,z)p^i q^j`. The producer evaluates its 266 GF(2) terms in native integer binary-field arithmetic and performs exact Gaussian elimination over the same field. The auditor rebuilds `M` with installed Sage and checks a canonical 81-entry digest before Sage computes its rank. It also checks `H=0` at the known N41 and N131 positive product witnesses. On N41, Sage evaluates the 32-by-32 matrix `V_P M V_Qᵀ` over the entire positive and negative product bins and measures rank 9 directly.

| Exact panel | Cases | Coefficient ranks | Complete finite-fiber ranks | Producer interval | Peak producer RSS |
| --- | ---: | --- | --- | ---: | ---: |
| N41 positive, negative, fixed-seed controls | 18 | 18 × 9/9 | Positive and negative: 9/9 | 0.130 s | 18,071,552 B |
| N131 constructed positive and field control | 2 | 2 × 9/9 | Not materialized | 0.094 s | 17,006,592 B |

The local intervals are exploratory arithmetic diagnostics. The [N41 protocol](protocol.json) and [N131 corrected protocol](protocol_n131.json) fix source/input hashes, case laws, one worker, a 120-second wall cap, and 4-GiB memory ceiling. Both completed under those limits. The [N41 result](result.json), [N131 result](result_n131.json), and separate [N41](audit.json) and [N131](audit_n131.json) independent checks retain every matrix digest and rank. The checked [Sage runtime receipt](sage_runtime_info.json) was saved before either audit.

The first N131 producer used `seed_mask << 1` as a polynomial-basis coordinate. The independent Sage audit rejected its claimed archived positive evaluation. Its original [protocol](protocol_n131_attempt1.json) and [rank output](result_n131_attempt1_wrong_seed.json) are retained as a **wrong-source-encoding producer failure**. The corrected protocol reads the rotated seed coordinates from the archived checked fixture; its independent audit verifies the archived product root makes the rebuilt eliminant zero.

## Proof and transfer boundary

For any two lists of 32 distinct field products, the 32-by-9 Vandermonde evaluation matrices in powers 0 through 8 have column rank 9: a nonzero degree-at-most-eight polynomial has at most eight field roots. Consequently `rank(V_P M V_Qᵀ)=rank(M)=9` when `rank(M)=9`. An evaluation matrix formed by at most eight separable terms `f_i(p)g_i(q)` has rank at most eight, since each term has rank at most one. The exact Sage rank of both N41 32-by-32 matrices independently checks the premise and conclusion for these frozen fibers. The [proof map](PROOF_MAP.md) records the partial Lean formalization status and the missing concrete-field bridge.

This gate leaves the complete objective active. The next experiment should operate on the zero predicate of `H` jointly with source-product subspace membership and the public upper S3 equation, preserving an unpinned N41 eight-column witness before an N131 ordinary-query promotion. The tested matrix ranks give no target-conditioned generator by themselves; `candidate_id` remains null.
