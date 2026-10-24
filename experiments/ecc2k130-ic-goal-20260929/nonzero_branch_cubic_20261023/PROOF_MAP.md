# Proof map: fixed-bit nonzero product branch

The target-conditioned two-product resultant has the frozen 13-term support in
`n41_w11_freecode_resultant_20261018` and
`n131_w33_freecode_resultant_20261018`. The earlier
`resultant_degree1_syzygy_20261019/DegreeFall.lean` proves that multiplying
this resultant by the first source product lowers its Boolean source-code
degree to at most three, and proves zero-set equivalence when the product is
nonzero. Its 13-term support proof and complete ANF bridge status remain as
recorded there.

The new [NonzeroBranch.lean](NonzeroBranch.lean) contains three checked
declarations:

| Result | Lean declaration | Exact hypotheses and status |
| --- | --- | --- |
| A fixed-one code bit excludes the zero and seed code | `NonzeroBranch.excludes_zero_and_seed` | Injective field encoding, the zero code maps to zero, zero and seed code have bit false, tested code has bit true; checked |
| The first source product is nonzero | `NonzeroBranch.product_ne_zero` | Field, `s+s=0`, `a≠0`, `a≠s`; checked |
| Scaled cubic and original resultant have the same zero set | `NonzeroBranch.cubic_branch_exact` | Same field and nonzero-source hypotheses, arbitrary resultant field element; checked |

The module is pinned to `leanprover/lean4:v4.34.1`. Run
`lean NonzeroBranch.lean > lean_check.log 2>&1` from this directory. The
saved [log](lean_check.log) includes `#print axioms` for all three
declarations; the reported foundations are `propext`, `Classical.choice`,
and `Quot.sound`. The proofs have no placeholders, custom axioms, or native
evaluation. `lean4checker --fresh` was unavailable on this host.

The bridge from an abstract injective code encoding to the concrete N41 and
N131 branch is finite: the [independent checked-Sage audit](audit_result.json)
rebuilds the field, seed, and source products and checks every one of 16 N41,
8 N131 width-three, and 16 N131 width-four first codes against `a=0`,
`a=s`, and `p=0`. It also checks the positive resultant root. These finite
checks do not formalize the complete elliptic curve law in Lean. The prior
N131 independent [group replay](../n131_w33_resultant_core_20261018/replay_result.json)
checks the recovered constructed pair on the exact curve.
