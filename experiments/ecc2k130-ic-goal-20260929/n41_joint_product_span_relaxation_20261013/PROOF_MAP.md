# Proof map

Toolchain: Lean 4.34.1, commit `5045d0056413266e57c625dcd7c365b10e377c52`; [version](lean_version.txt), [build and axiom output](lean_check.log). The module imports only `Std`. `lean PairRelaxation.lean` exited 0. Both printed declarations have no axioms; `lean4checker` was not installed.

| Mathematical obligation | Lean declaration or evidence | Exact scope and status |
| --- | --- | --- |
| Every exact usable pair remains in the product-span relaxation | `PairRelaxation.exact_pair_in_product_span` | Checked. For any type with zero, one, addition and multiplication, assumes usable source elements lie in `W`, `W` is closed under addition, and products of two `W` elements lie in `D`. The exact pair carries the displayed pair equation and distinct sources. |
| Two exact pair outputs satisfying a target link survive the joint relaxation | `PairRelaxation.exact_two_pair_target_survives` | Checked. Universal in both outputs and target. The `S3` predicate is an explicit parameter; no curve implication is silently assumed. |
| Binary-field halftrace linear system enumerates exactly the relaxed pair equation | [archived derivation](../n41_n131_universal_product_linearized_20261011/RESULT.md), [independent inverse audit](audit_result.json) | Mathematical derivation and sampled N41 inverse audit; not formalized in Lean here. Its remaining proof obligation is a characteristic-two field definition with the odd-degree halftrace identity and trace guard. |
| Cleared S3 in the `1/x` chart equals `(cdt)^2+cdt+c^2+d^2+t^2` | [symbolic identity](s3_identity.json), [deriver](derive_s3.py) | Exact GF(2) polynomial calculation. A Lean multivariate polynomial identity over characteristic two remains open because this checkout's pinned Lean environment has no polynomial/ring library imported. |
| A constructed S3 hit lifts to a point-sum witness | [checked Sage replay](sage_replay_result.json), [runtime](sage_runtime_info.json) | Verified for the frozen four-mask control and two sign assignments. This is an instance check, not a universal formal curve-law bridge. |

The complete curve-coordinate theorem, with halftrace and S3 connected to arbitrary points on `y²+xy=x³+1`, remains open. The checked structural theorems do not replace that statement.
