# Squared Hasse predicate Lean bridge: pre-dispatch review plan

2026-10-27 UTC · Conductor T-504. Producer source is immutable commit
`f1c2dca` on `codex/hasse-square-bridge-20261027`, based on cryptanalysis
main `dc73f9791dc7d2c61e0c77572d2c3aaeedb30436`. Subject:
`CurveAudit.squared_deviations_have_short_sum`,
`CurveAudit.unsignedDelta_center_bounds`, and
`CurveAudit.unique_multiple_from_hasse_squared_checks` in
`bindings/rust/curve-audit/formal/HasseSquareBounds.lean`; source SHA-256
`26e3e7bbf28aad0f60f72137fca027427b435f05bcef9f5de5881d7979307c42`.
Proof map SHA-256
`e69234ad80de640a09f5b25a9fd49987e55dfeebfff88b38186cbf4b8c7dcb84`.
Lean pin `leanprover/lean4:v4.34.1`, pin SHA-256
`d5edba4e4b8faad9c1baeadb265716d20d03be4d1a2647dc5e35b0c0325bea7b`.
The source imports the existing `HasseUnique.lean` at base main.

## Prior and separated reviewer joints

Coordinator prior, before review: the squared-spacing arithmetic appears
valid and a local preliminary build exited zero. The theorem is a real
bridge from Rust's integer predicates to uniqueness, but still lacks actual
curve-cardinality divisibility, Hasse and implementation-code fidelity.
Reviewers may disagree. No broader proof or official decision is presumed.

| Joint | Owner | Worked attack |
| --- | --- | --- |
| Arithmetic from two squared deviations and strict `r²>16p`; sharpness and nonvacuity | Blind reviewer A | Derive without producer code. Try `r=0`, `p=0`, exact equality `r²=16p`, and one missing squared bound. Find a concrete false weakened case. |
| Lean statement vs proof map and Rust `hasse_unique_multiple`; unsigned difference orientation and remaining curve bridge | Source reviewer B | Compare committed source with map, Rust lines 137–149 and README 70–100. Search for assumed conclusion, missing divisibility, wrong subtraction case, or overstatement. |
| Exact-source pinned build, transitive axiom audit, positive/negative controls and immutable hashes | Coordinator | Rebuild both modules in isolation, audit every named theorem, compile positive/sharp cases, reject `sorry` and missing module. |

Reviewer A may read only `blind-brief.md` and public Nat/Lean documentation,
not source, proof map, plan, receipts or B. Reviewer B may read this plan,
bound Lean source, proof map, Rust function and README, not A's brief or
report. Both must list actual reads, sibling access, owned joints, protocol
deviations, and `holds | breaks | inconclusive` findings. Reviewer outputs
remain separate until both return.

Positive control: `p=101,r=41,n=m=82,k=l=2`; center `102`, each deviation
`20`, `20²=400≤404`, and `41²=1681>1616`. Sharp known-false weakened
case: `p=1,r=4,n=0,m=4,k=0,l=1`; center `2`, both squared deviations equal
`4p`, `r²=16p`, yet `n≠m`. A false theorem proved with `sorry` must fail
transitive axiom audit, and an unknown module must fail closed.

Verdicts are separate for machine, fidelity and overall. `validated_scoped`
can apply only to the exact Nat arithmetic implication after complete checks.
The full P-192/P-224 curve-order claim remains not verified until prime-field,
point group, exact point order, Lagrange, Hasse-to-squared predicate, concrete
certificate and executable Rust-code bridges are proved. No experiment or
benchmark result is inferred or changed by this theorem.
