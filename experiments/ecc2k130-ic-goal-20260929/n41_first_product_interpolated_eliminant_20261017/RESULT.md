# First-product interpolation screens all N41 three-code families

**Seventeen first-product specializations reconstruct a target-conditioned eliminant that screens all 64,000 valid product-code triples on the frozen N41 public residual in 0.411 seconds after precomputation.** Exactly one triple survives, with products `(97508,1383481007416,216004441708)`. Independent checked Sage reconstructs its seven pair states `(97,151,42,0,14,109,51)`, checks fourteen distinct folded columns, and sums them to raw public point `(1970584690684,115750356512)`. The frozen negative residual retains zero of 64,000 triples in 0.416 seconds. A second checked-Sage evaluator, nesting the variables in the opposite order, reproduces all **128,000** decisions.

The method leaves the first three pair-code choices free while fixing four suffix pair states from the archived public relation. It is a target-conditioned point-decomposition component (`candidate_id: null`). The fixed suffix defines each panel's residual; it is charged as an input condition rather than an unpinned seven-pair search.

## Algebra and exact source

The field is `GF(2)[t]/(t^41+t^3+1)` on `y²+xy=x³+1`, curve ID `EC1N41Ckb1h7d5e80d3c4d0`. Each of the first three rotated W8 pair slots has 40 admissible first masks, one distinct product per mask and four signed pair-sum states. The shifted reciprocal is `u=1/(x+1)`. The archived four-atom polynomial `H(p,q,z)` has `p` and `q` degree at most four and `z` degree eight. The public residual supplies `Q(z,r,t)`, which is independent of `p`, has `z` degree four and `r` degree at most three. Define

`F(p,q,r;t)=Res_z(H(p,q,z),Q(z,r,t))`.

The resultant is homogeneous of degree four in the coefficients of `H`, so its degree in `p` is at most `4×4=16`. Its `q` and `r` degrees are bounded by 16 and 24. Each coefficient of `q^i r^j` is therefore a polynomial in `p` of degree at most 16. Seventeen distinct field values determine that polynomial uniquely: two degree-16 candidates agreeing on those values have a difference with seventeen roots, hence zero. This reconstructs the complete eliminant, including terms that might vanish at individual samples. For each residual the universal representation has **213 `(q,r)` coefficient polynomials** and maximum observed `p` degree **16**. Their degree histogram is `12:5, 14:58, 15:96, 16:54` for both panels.

The [v2 protocol](protocol_v2.json) fixes seventeen source-valid first-product samples and two held-out source-valid products, including the archived witness `97508`. Each sample is computed in a separate sequential checked-Sage child using the repository launcher. The parent interpolates the 213 coefficient polynomials, checks both held-out direct resultants coefficient by coefficient, and retains every child stdout/stderr hash. Its [witness result](witness_result_v2.json) and [negative result](negative_result_v2.json) preserve the exact tensor and phase costs.

| Frozen residual | 17 sample launchers | Interpolation | 2 holdout launchers | Parent total | Conservative parent + child RSS bound |
| --- | ---: | ---: | ---: | ---: | ---: |
| Public witness suffix `(0,14,109,51)` | 77.586 s | 1.926 s | 11.134 s | **90.988 s** | **976,977,920 B** |
| Negative suffix `(18,136,67,12)` | 115.007 s | 2.851 s | 18.498 s | **136.758 s** | **992,722,944 B** |

The totals also include 0.342 s and 0.402 s of parent bookkeeping respectively. Sample launcher intervals include checked-Sage startup and resultant construction. The children spent 36.575 s and 49.138 s respectively inside their seventeen resultants. The two holdouts are validation work, not required to construct a degree-16 interpolant. These runs used one child at a time, a 300-second parent alarm per panel, and a 4-GiB observational RSS boundary on an ordinary shared host. The [checked runtime record](sage_runtime_info.json) was saved before work began.

## Full code-cube result and independent replay

The [sweep protocol](sweep_protocol.json) binds both interpolated tensors and all 40 valid products per free slot. For each first product, the producer specializes the universal coefficients; for each second product it forms a degree-24 polynomial in the third product; it then tests the 40 valid third products. It visits exactly `40³=64,000` code triples per residual, with 253,329,408 B peak self RSS. A zero is a necessary algebraic condition; the retained triple receives a separate source-column and group check.

| Residual | Product triples screened | Algebraic zeros | Sweep interval | Reverse-order audit | Group result |
| --- | ---: | ---: | ---: | ---: | --- |
| Public witness suffix | 64,000 | **1** | 0.411 s | 0.787 s | One verified seven-state relation |
| Negative suffix | 64,000 | **0** | 0.416 s | 0.847 s | No survivor to expand |

The [reverse-order tensor audit](tensor_audit_result.json) independently evaluates a polynomial in `p` last for every code triple. The [curve audit](audit_result_v2.json) checks all 64 sign combinations inside the retained triple and identifies the single public-target witness, with fourteen distinct folded columns. The [read-only verifier](verification.json) uses a separate pure-Python `GF(2^41)` multiplier to check all 213 tensor coefficients at all 17 samples and both holdouts on both panels, then binds the sweep, reverse audit, group certificate, protocols, runtime and failures. Its coefficient checks total **8,094**.

## Preserved attempts, proof status, and next gate

The first [in-process witness run](witness_result.json) matched two held-out direct resultants in 38.232 s but reached **8,214,069,248 B** peak self RSS, above the 4-GiB boundary. Its [resource receipt](attempt1_resource.json) remains separate from the compliant v2 result. The first curve audit used the geometry's constructed target instead of the archived ordinary public target; its [failure receipt](audit_attempt1.json), protocol and raw stderr remain. The corrected audit uses the public target from `n41_w8_fixedseed_ordinary_join_20261013/protocol.json` and has its own source hash.

The [proof map](PROOF_MAP.md) records the degree bound, interpolation uniqueness, and exact curve/resultant bridge. Pinned Lean 4.34.1 checked coefficient-evaluation additivity and scaling in [InterpolationEval.lean](InterpolationEval.lean), with `#print axioms` reporting only standard foundations. The faithful resultant-degree and 17-sample uniqueness theorems remain open formalization tasks; the complete finite N41 instance has independent arithmetic and group replay.

The N131 W20 seven-pair source has 132,045 edge codes per slot. A literal three-code sweep would visit **2,302,321,041,991,125** product triples before any other suffix choices, requiring about **3.84 trillion triples/s** under 600 seconds. First-product interpolation removes repeated symbolic resultant construction across those codes, but the next algorithm must also eliminate or batch the second and third product families while carrying the public target. The measured N41 tensor and full-cube witness provide a frozen correctness gate for that implicit elimination.
