# Proof map

The source product `a(a+s)=a²+as` is binary linear in the ten free
source bits. The checked Sage run enumerates all 1,024 products,
asserts each equals the corresponding binary sum of ten basis
products, and constructs their characteristic-two vanishing
polynomial by the recurrence `L_new(z)=L(z)²+L(b)L(z)`.

`SubspaceVanishing.vanishingFn_add` proves that this recurrence remains
additive in any characteristic-two commutative ring.
`SubspaceVanishing.vanishingFn_zero_on_binarySpan` proves that the
resulting function vanishes on every binary subset sum of the ordered
basis. These declarations preserve the quantified basis list and field
characteristic assumption; the concrete 41-bit basis independence and
field representation are checked by the Sage producer, outside Lean.

The quartic used for each code is the prior exact
[`R(w;x,p,H,C)` polynomial](../n41_w9_two_quartic_resultant_20261017/RESULT.md).
The producer audits four roots against direct group subtraction for
one code per target row. The generic source-product-to-quartic
elimination and the polynomial GCD/root bridge are not formalized in
this module; the written algebra and finite executable checks retain
those proof obligations. A GCD with the vanishing polynomial is an
exact root test here because that polynomial splits into all 1,024
source-product field elements.

The module uses pinned Lean `4.34.1`, builds with
`lean SubspaceVanishing.lean > lean_check.log 2>&1`, and records
`#print axioms` for both declarations. It uses standard Lean foundations,
with no custom axioms or unverified native evaluation.
