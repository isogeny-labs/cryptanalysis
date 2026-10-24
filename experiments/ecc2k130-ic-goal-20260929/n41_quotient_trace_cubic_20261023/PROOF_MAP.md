# Proof map: root-free quotient cubic bits

The quotient calculation specializes the archived 170-term polynomial
`H(a,b,p,q,U)` over `GF(2^41)`. Its variable is `u=1/(x+1)`, while the
archived cubic feature bits use `z=1/x`. For monic `H`, let `c=H(1)` and
`H(U)=(U+1)Q(U)+c`. If `c≠0`, then `Q/c` is the inverse of `U+1` in
`GF(2^41)[U]/H`, so the quotient residue `UQ/c` represents `z` at every
root of `H`. Trace-dual coefficients turn each bit `z_i` into a polynomial
residue. Products of two or three residues represent the corresponding
squarefree feature bits at every root.

| Result | Formal or finite check | Status and exact boundary |
| --- | --- | --- |
| A constant quotient residue equals that constant at every root of `H`. | `QuotientCubic.constant_remainder_sound` in `QuotientConstancy.lean` | Checked under the exact quotient identity `P(v)=b+H(v)Q(v)`, a root `H(u)=0`, and zero/add laws. It uses no custom axioms. |
| A target bit opposite that constant excludes the root. | `QuotientCubic.reject_mismatch` | Checked with the same hypotheses and explicit mismatching target bit. |
| The specialized `H` has eight distinct field roots, `H(1)≠0`, and the quotient masks match the eight archived `1/x` roots on each selected family. | `audit_v2.py` through the checked Sage launcher | Verified for all 8 frozen families, 64 roots, and 520 target decisions. This finite field bridge is not a Lean theorem. |
| The synthetic-division identity for the specialized polynomial and the trace-dual coefficient arithmetic. | `run_v2.py` assertions plus independent root replay | The producer checks the reciprocal quotient inverse and idempotence of all 41 trace residues; the Sage audit checks every output bit mask against the roots. Full coefficient-level formalization remains open. |

`QuotientConstancy.lean` is pinned to `leanprover/lean4:v4.34.1` with bundled
`Std`. `lean_check.log` records the actual build and `#print axioms` output;
both declarations have no axioms. No `sorry`, `admit`, native-evaluation
certificate, or assumed result is used in those proofs.

A polynomial-syntax Lean proof was attempted through the repository's cached
Mathlib revision `021c46bdd042f67b538b9f9871d556a93713a9a9` under Lean
`v4.35.0-rc4`. The import failed before elaboration because the cached
`Mathlib.Data.Set.Finite.Range.olean` dependency points to a missing
`/Volumes/SSD990-2/cryptanalysis-hecke-D3783-f6-20261022/formal` build.
`MathlibDependencyProbe.lean` and `mathlib_probe.stdout` preserve the exact
failed dependency check. The missing formal bridge is coefficient-level
polynomial division, quotient reduction, and the concrete `GF(2^41)` trace
implementation; the faithful conditional soundness lemmas above are checked.
