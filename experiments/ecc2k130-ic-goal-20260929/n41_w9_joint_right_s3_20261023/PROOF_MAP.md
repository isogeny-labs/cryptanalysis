# Proof map

| Result | Checked proof or audit | Exact boundary |
| --- | --- | --- |
| The five-point group sum can be regrouped as a left three-pair sum plus a right two-pair sum | `JointAssociation.regroup_five` | Arbitrary point type and an associative binary operation. |
| Defined reciprocal coordinates of the right two-pair sum and target satisfy both alternate S3 links | `JointAssociation.joint_target_link_full` | Assumes the exact group sum, defined coordinates for all participating points, and a chart-soundness implication for S3. These assumptions are explicit. |
| Concrete N41 right-sum chart and frozen-panel result | `audit_sage.py` and `audit_result.json` | Independent Sage curve arithmetic for all 33 panel rows; checks source columns, two alternate S3 equations, full group sum, and the Boolean circuit's gate values. |
| No loss of the archived relation in either encoding | `build.py`, `build_compact.py`, and the independent audit | The exact positive assignment satisfies every emitted clause and native XOR row; all four alternate gate values agree with the checked curve arithmetic. |

Pinned toolchain: `leanprover/lean4:v4.34.1`. Run `lean JointAssociation.lean` here. `lean.stdout` reports no axioms for both declarations; `lean.stderr` is empty. `lean4checker --fresh` was unavailable on this host. A full Lean bridge from the concrete curve group law and `1/x` chart to the polynomial S3 equation remains open. The finite-field and group bridge for this exact N41 panel is independently computed by checked Sage.
