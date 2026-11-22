# Half-fixed torsion-class count proof map

The exact four-class convolution for six even original-source positions
and six odd union-source positions is formalized in
[`HalfBranchClasses.lean`](HalfBranchClasses.lean).

| Result | Lean declaration | Hypotheses and boundary | Status |
| --- | --- | --- | --- |
| Source plus image class vector | `HalfBranchClasses.union_classes` | The concrete original and image one-position vectors are the inputs | Kernel checked |
| Ordered twelve-position counts | `HalfBranchClasses.twelve_position_counts` | `sixPairs` starts at class zero and applies the exact mod-four convolution for six original/union pairs | Kernel checked |

The declarations establish the integer convolution and its exact output.
An independent [four-character audit](class_closed_form_result.json)
derives the same counts from the class-vector transforms rather than
repeating the convolution recurrence.
The [source census](../n131_d13_phi_raw_fiber_20261115/census_result.json)
and its [independent audit](../n131_d13_phi_raw_fiber_20261115/audit_result.json)
establish the one-position class vectors for the exact N131 source.
The Lean module does not formalize the elliptic-curve construction or
that census; this is the remaining bridge to a fully formal curve-level
theorem. Division of the counts by the subgroup order is explicitly a
uniform-occupancy model, not a theorem about natural target yield.

The pinned toolchain is `leanprover/lean4:v4.34.1` in
[`lean-toolchain`](lean-toolchain), using its bundled `Std` dependency.
From this directory, `lean HalfBranchClasses.lean` exits zero. The
captured [stdout](lean.stdout) shows `#print axioms` reporting no axioms
for either theorem; [stderr](lean.stderr) is empty. `lean4checker
--fresh` is unavailable on this host.
