# Proof and evidence map

| Result | Declaration or independent evidence | Status and exact boundary |
| --- | --- | --- |
| Five-pair common-Frobenius identity for an additive endomorphism | [`common_factor_five`](../n41_common_frob_factor_20261012/CommonFactor.lean), pinned Lean 4.34.1 check in the prior [`lean_check.txt`](../n41_common_frob_factor_20261012/lean_check.txt) | Kernel checked with no theorem axioms. The theorem is abstract over an additive endomorphism. |
| Curve-specific map `(1+Frobenius^7)Q′=Q`, subgroup eigenvalue and invertibility | Prior checked-Sage [`target.json`](../n41_common_frob_factor_20261012/target.json) and its [`PROOF_MAP.md`](../n41_common_frob_factor_20261012/PROOF_MAP.md) | Executable concrete-field bridge; the complete Sage group object is not imported into Lean. |
| New five-state relation, ten distinct columns, and quotient rank `7→8` | Frozen native [`result.json`](result.json), independent checked-Sage [`audit_result.json`](audit_result.json), [`audit_sage.py`](audit_sage.py) | Exact finite source and group replay. This is an empirical witness, not a new universal theorem. |
| N131 signed W18 pair-state count and uniform-model probability bound | [`project.py`](project.py), [`projection.json`](projection.json), source-support digest, prior [`FivePairCount.lean`](../n41_common_frob_factor_20261012/FivePairCount.lean) for the distinct-column extension bound | Exact source count and rational arithmetic. The probability statement is conditional on uniform residuals; no claim about a correlated public-target generator. |

`python3 -B verify.py` checks frozen source, binary, protocol, runtime, prior-row, projection, and result hashes. A new Lean theorem would be required for any claimed universal property of a future target-conditioned proposal mechanism; this experiment makes no such claim.
