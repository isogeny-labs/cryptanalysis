# S3 coefficient identity: partial formalization

[pcc:unverified]

[pcc:unverified] S3Direct.lean proves the direct Boolean coefficient identity and cross-term
symmetry over any commutative characteristic-two ring and finite index set.
Boolean coordinates are explicit hypotheses u_i²=u_i and w_i²=w_i.

Pinned Lean: leanprover/lean4:v4.35.0-rc4.
Pinned mathlib: 021c46bdd042f67b538b9f9871d556a93713a9a9.
Producer kernel checks004 and006 completed with exit0. Check006 narrows
imports to the required algebra and tactics; its source is current. Main declaration axioms:
propext, Classical.choice, Quot.sound. Symmetry uses propext. No admitted
proofs or additional algebraic axioms appear in the checked source.

Command (using the existing pinned project cache as the environment):

```sh
lake env lean --root="$EXPERIMENT" -o /tmp/ic-s3-direct-lean/S3Direct.olean "$EXPERIMENT/S3Direct.lean"
```

The project environment was the existing research/nist_explicit_gluing_resume_20261114/formal
checkout in /Volumes/SSD990/cryptanalysis. Failed attempts001..002, warning-bearing success003 and clean
attempt004, failed narrow-import005 and successful006 are retained separately;
only the final source/exit0 support this
producer check. The observed axioms are not a signed independent PCC verdict.

Remaining obligations: Rust word-field arithmetic, exact correspondence of
memory operations and emitted canonical masks, allocation bounds, integration
with the solver, and full pipeline cost. Differential tests address concrete
instances of implementation correspondence; they do not close these proofs.

The repository AuditAxioms.lean helper could not compile against this pinned
Lean API. That failure is retained. AuditS3.lean uses the same standard-axiom
criterion without a compiler-trust whitelist and inspects all five declarations
in S3Direct. The final audit exits0: five theorems inspected, zero with additional axioms.
Its output is a producer audit, not a signed independent verdict.
