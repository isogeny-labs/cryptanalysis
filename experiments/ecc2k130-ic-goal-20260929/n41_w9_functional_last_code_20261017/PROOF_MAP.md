# Guarded functional last-code proof map

The field is `GF(2)[u]/(u⁴¹+u³+1)` and the curve is
`y²+xy=x³+1`, with subgroup order `549756390943` and cofactor four.
The original N41 five-pair formula contains the last-link equation

`a(w)p² + b(w)p = q(w)`, with `p=P(code)` for the eight-dimensional
rotated source-product map `P`. The extension retains that equation.
With frozen public reciprocal `t`, source constants `H` and `C=1+H`,
the coefficients are `B=tw`, `A=1+B²`, `D=t²+w²`,
`M=AH+CD`, `a=AD`, `b=BM`, and `q=M²+CHB²`.
For `a,b ≠ 0`, put `s=b/a`, `z=qa/b²`, and let `H` be the 41-term
halftrace. Characteristic-two arithmetic gives

`a(su)²+b(su) = (b²/a)(u²+u)`.

If a code satisfies the original equation, then `u=p/s` obeys
`u²+u=z`. Hence `Tr(z)=0`. The halftrace identity in the degree-41
field is `H(z)²+H(z)=z+Tr(z)`. Therefore `u` is either `H(z)` or
`H(z)+1`, and the product must equal

`p₀=sH(z)` or `p₁=p₀+s`.

The circuit uses the deterministic Itoh–Tsujii inverse with `0⁻¹=0`,
an F₂-linear halftrace map, and one Boolean branch to select `p₀` or
`p₁`. It asserts `p=P(code)` only when both `a` and `b` are nonzero.
For exceptional coefficients the additional assertion is disabled;
the original equation remains active. Conversely, any assignment of
the extension satisfies the original formula because the base clauses
are retained. Thus the guarded extension preserves exactly the base
formula's projected `(w,code)` solution set, assuming each arithmetic
gate implements its stated field operation.

| Result | Declaration or audit | Status |
| --- | --- | --- |
| Guarded root branch preserves the base solution set given the regular-root implication | `GuardedDecoder.extension_iff_base` | Lean checked; only `propext`, `Classical.choice`, `Quot.sound` |
| Characteristic-two root and halftrace identities | Written derivation above; 284 exact positive numerical replays in `build.py`; independent `audit_sage.py` replay on all 1,564 rows | Mathematical proof and finite controls; full Lean field bridge open |
| Added Boolean circuit on distributed positive controls | `build.py`, `result.json` | 16 full extension assignments checked |
| Base circuit retained byte-for-byte | `protocol.json` source hash and `verify.py` header/receipt checks | Frozen SHA-256 |

`leanprover/lean4:v4.34.1` is pinned in `lean-toolchain`; `lean
GuardedDecoder.lean` succeeded and `lean.stdout` records `#print axioms`.
`lean4checker --fresh` was unavailable. The full field-specific theorem
remains a partial Lean formalization: the exact missing bridge is a
formal GF(2⁴¹) implementation with multiplication, inverse, 41-term
halftrace, and a proof that the circuit gate semantics equal those
operations. The generic guarded preservation implication is checked;
the numerical gate and positive-row checks audit the concrete bridge.
The independent checked-Sage audit completed in 4.027 s of arithmetic,
with self peak RSS 231,292,928 bytes. Its source and runtime inputs are
frozen in `audit_protocol.json`.
