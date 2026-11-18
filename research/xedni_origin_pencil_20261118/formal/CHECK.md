# Formal verification receipt

`OriginPencil.lean` formalizes the coefficient-coordinate facts used by the
target-origin-pencil search: forward and inverse coefficient-sum transport,
the target endpoint's effective coefficient, preservation of a zero
fixed-origin target coefficient, and the `(d+1)B` endpoint bound.
[pcc:unverified]

It was checked in the pinned Lean 4.35.0-rc4/Mathlib environment from
`research/xedni_plane_group_20261117/formal`. The exact producer-side command,
toolchain revision, exit status, and axiom output are retained in `BUILD.txt`.
The source contains no `sorry`. [pcc:unverified]

The proof is algebraic. It does not formalize the remaining geometric bridge
that good reduction maps a concrete chord residual to the negative sum of its
endpoint source scalars. [pcc:unverified]

No Lean build error occurred. This is a producer-side receipt without
independent PCC standing. [pcc:unverified]

The self-contained Lake project also built all 9,040 jobs successfully. The
repository `tools/lean/proof-gate.sh` then failed in its auditor, before
auditing a theorem, because `AuditAxioms.lean` uses APIs absent under Lean
4.35 (`Lean.ofReduceBool`, `Lean.trustCompiler`, and `String.trim`). The exact
failure is retained in `PCC_GATE_FAILURE.txt`; it is an infrastructure failure
and does not grant PCC standing. [pcc:unverified]
