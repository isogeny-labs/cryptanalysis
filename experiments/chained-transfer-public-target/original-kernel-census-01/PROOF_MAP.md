# Independent finite original-kernel census proof

`lean/KernelCensus.lean` uses the full literal input projection in
`lean/literal-native-inputs.json`, whose source digest pins the entire
311-record native88f828 fixture. All18 masks, D values, seven smoothness
vectors, stored eligibility flags and both complete64-entry transport tables
are present. Python only renders these existing literals; it calculates no
kernel or path verdict. [pcc:unverified]

Six declarations in `OriginalKernelCensus` check:

- `actual_data_shapes`: complete finite shapes and base-field D values.
- `actual_transport_bijections`: both image tables contain64 distinct images.
- `all18_eligibility_checks`: nonzero smoothness vectors and an exhaustive
  F223 square test reproduce every stored eligibility flag.
- `complete_triple_coverage`: the enumeration contains216 triples and every
  triple of Fin6 indices.
- `actual_supported_verdict`: direct64-bit membership comparisons and
  recomputed eligibility yield pairs(4,1)/(1,4) and triple(4,1,4).
- `actual_path_unique`: no other triple of Fin6 indices is accepted.

Both original Lean4.34.1/4.35.0 gates pass all six roots with zero trusted
assumptions. The first array-encoding reduction failure is retained in
69d82d; the successful proof uses the same literals in lists and ordinary
kernel reduction. Exact local statement bindings are recorded separately.
[pcc:unverified]

These are finite-data theorems. They do not establish HLP quotient identity,
actual elliptic/field correspondence, Frobenius descent, geometric degree,
Picard encoding or the program bridge. Native checks preserve the original
coordinate certificates, and full-group Jacobian evaluation is a subsequent
separate construction with its own protocol. No cost or signed promotion
follows from the finite verdict. [pcc:unverified]
