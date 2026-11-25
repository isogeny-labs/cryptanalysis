# Native corpus integration correction

PR #1282 merged at 2026-10-28T16:36:58Z as
`47865467f9cc28c316a12ddab017017047815f19`. All 15 published blob hashes
were verified at that merge. Its `corpus` check had already failed at 16:31:13Z:

    ValueError: unreviewed Lean corpus addition:
    docs/known-label-next-leads-20261028/Algebra.lean

[Failed job and log](https://github.com/isogeny-labs/cryptanalysis/actions/runs/40725985266/job/122949254132).
This failure was caused by the publication. The original module was labeled
unbuilt, but that label did not make an unregistered `.lean` source admissible.
GitHub auto-merge also completed before Rust analysis finished at 16:43:06Z.
The full merge gate was therefore not met; a successful merge is not evidence
that all applicable checks passed. No manual bypass, rerun or skip was used.

## Correction and unchanged acceptance requirements

The module remains at its original path and byte-identical source SHA-256
`d0e0fa1892bc800999e3b5330f543bf2e99811f607606901f363fce27bcb428d`.
The corpus gate now has an explicit binding for that source and must execute:

- The existing Lean `leanprover/lean4:v4.35.0-rc4` workspace with Mathlib
  revision `021c46bdd042f67b538b9f9871d556a93713a9a9`.
- Native compilation of the original file into a fresh `.olean`.
- Axiom printouts covering all four declarations, restricted to the existing
  allowed foundations `propext`, `Classical.choice`, and `Quot.sound`.
- The existing exhaustive module auditor, with exactly four theorems,
  zero failing theorems and zero trusted exceptions.
- A final unchanged-source hash check.

Unknown source paths, changed pins or bytes, compilation failures, incomplete
audits and nonstandard axioms remain refusals. No check, workflow selector,
proof escape prohibition, historical corpus receipt or Lean source is removed.
The Python refusal controls use simulated compiler/auditor outputs and are not
reported as native proofs. The full native job must pass on the corrective PR's
current head. Auto-merge for that correction is deferred until the complete
applicable check set and review gates have been inspected.

## Proof map and scope

| Declaration | Scope | Required evidence |
| --- | --- | --- |
| `triangle_identity` | Ring identity underlying the triangle-label formula | Native compiler plus exhaustive axiom audit |
| `signed_second_moment` | Polynomial identity for twice the signed denominator | Same |
| `signed_third_moment` | Polynomial identity used to recover the negative index | Same |
| `positive_pair_product` | Polynomial identity for the positive pair product | Same |

These statements use a general commutative ring; interpreting division in the
decoder additionally uses a prime field of order greater than three and distinct
indices. Neither these identities nor passing corpus CI formalizes the full
elliptic-group transport, index-signature injectivity, probability argument or
any claimed cost bound. Those broader results remain written arguments or
proposals. No new research benchmark was run by this correction.
