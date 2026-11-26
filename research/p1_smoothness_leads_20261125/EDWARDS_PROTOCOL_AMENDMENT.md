# Pre-run Edwards positive-control correction

After committing `EDWARDS_PROTOCOL.md` and generating inputs, but before
running `msolve`, the selected positive target was found inside the factor
base. The first generated inputs were not executed or committed. This
amendment changes only that positive target selection and its expected
solution count. It is frozen before solver execution. `[pcc:unverified]`

Use Edwards points at sorted indices `0,2,5` instead of `0,2,4`. Their sum
maps to Weierstrass `(1393,5697)`, is outside the eight-point factor base
even up to negation, and has exactly 12 ordered coordinate triples in each
model. Keep the field, curve, birational map, factor base, negative target,
polynomial construction, solver command, and validation rules from the
original protocol. Regenerate all four `.ms` inputs and fixture metadata
before the first solver call. Preserve this amendment with the output.
`[pcc:unverified]`
