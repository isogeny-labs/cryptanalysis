# Formal verification receipt

`Dedup.lean` formalizes only the key-factorization implication: if exactness or
recovery is a function of the transported fixed-coordinate key, changing its
origin-local representative cannot change the result. It also retains the
elementary first-success obligation. [pcc:unverified]

The pinned Lean 4.35.0-rc4/Mathlib build completed all 9,040 jobs, with no
`sorry` and no axioms reported for the three declarations. Exact producer-side
output is retained in `BUILD.txt`. [pcc:unverified]

This does not prove that the concrete plane-cubic group implementation factors
through the fixed key. The exhaustive deterministic alias audit exercises that
bridge on 99,622 representatives. Independent PCC standing remains blocked by
the repository auditor's previously retained Lean 4.35 API incompatibility.
[pcc:unverified]
