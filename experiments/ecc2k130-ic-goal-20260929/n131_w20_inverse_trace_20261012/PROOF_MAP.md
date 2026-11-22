# Proof map: W20 inverse-trace gate

| Result | Lean declaration | Hypotheses and verification |
| --- | --- | --- |
| Pointwise replacement of an exact source gate preserves seven-slot relation existence with the same distinct-column predicate and target | `W20GateReplacement.exact_gate_substitution` | Assumes `∀ code, bdd code ↔ inverseTrace code`; arbitrary seven-slot point-sum function and column predicate. Checked by `lean GateReplacement.lean`; `#print axioms` reports no axioms. |
| The W20 inverse-witness predicate equals the frozen 132,045-code BDD predicate | Concrete GF(2¹³¹) bridge remains open in Lean | The field is `GF(2)[t]/(t^131+t^13+t²+t+1)`, curve `y²+xy=x³+1`, source span `t..t²⁰`, seed mask 898618, and both endpoints are nonzero. `run.py freeze` checks trace zero on all 20 basis vectors, recomputes the exact accepted-pair count from the frozen support table, and checks inverse/trace on all 14 selected endpoints. The earlier native census checked rationality of every nonzero W20 mask; the BDD audit checked all 524,288 canonical selectors against that table. A formal field representation, trace/rationality theorem, and kernel-checked bridge to the enumerated support remain to be supplied. |
| The constructed seven-pair point sum satisfies the new XCNF | Executable assignment audit | `run.py control` binds selectors, pair outputs, inverse witnesses, intermediate sums, and S3 branch bits, then checks every clause and native XOR row. The prior checked-Sage audit independently checks the selected point relation. This finite execution check is separate from the Lean theorem. |

The source-gate mathematics is the characteristic-two Artin–Schreier criterion:
for nonzero `x`, dividing the curve equation by `x²` gives
`(y/x)² + (y/x) = x + x⁻²`. The absolute trace of `x⁻²` equals the
trace of `x⁻¹`. Since every W20 source element has trace zero,
the point exists exactly when `Tr(x⁻¹)=0`. The witness equation
`xv=1` forces `v=x⁻¹`. Both endpoints must pass, and the frozen support
table supplies the same-column exclusion.

The toolchain is pinned by `lean-toolchain` and recorded in
`lean_runtime.txt`; `lean_check.txt` retains the theorem and axiom check.
`lean4checker --fresh` was unavailable on this host.
